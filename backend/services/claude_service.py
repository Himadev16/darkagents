"""
Claude API Service
Wrapper for Anthropic Claude API with retry logic and error handling
"""
import time
from typing import Optional, Dict, Any
from anthropic import Anthropic, AsyncAnthropic
from anthropic.types import Message

from backend.config import settings
import structlog

logger = structlog.get_logger()


class ClaudeService:
    """
    Service for interacting with Anthropic's Claude API

    Features:
    - Retry logic with exponential backoff
    - Token usage tracking
    - Error handling
    - Support for both sync and async operations
    """

    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.async_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL

    def generate(
        self,
        messages: list[Dict[str, str]],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response from Claude (synchronous)

        Args:
            messages: List of message dicts [{"role": "user", "content": "..."}]
            system: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Dict with response content, usage stats, and metadata
        """
        retries = 0
        last_error = None

        while retries < settings.CLAUDE_MAX_RETRIES:
            try:
                logger.info(
                    "claude_api_call",
                    model=self.model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    num_messages=len(messages)
                )

                # Make API call
                response: Message = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system if system else None,
                    messages=messages,
                    **kwargs
                )

                # Extract response text
                content = ""
                if response.content:
                    for block in response.content:
                        if hasattr(block, 'text'):
                            content += block.text

                # Calculate cost (approximate - adjust based on actual pricing)
                input_cost_per_1k = 0.003  # $0.003 per 1K input tokens
                output_cost_per_1k = 0.015  # $0.015 per 1K output tokens

                input_cost = (response.usage.input_tokens / 1000) * input_cost_per_1k
                output_cost = (response.usage.output_tokens / 1000) * output_cost_per_1k
                total_cost = input_cost + output_cost

                result = {
                    "content": content,
                    "role": response.role,
                    "model": response.model,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                    },
                    "cost_usd": total_cost,
                    "stop_reason": response.stop_reason,
                }

                logger.info(
                    "claude_api_success",
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    cost_usd=total_cost
                )

                return result

            except Exception as e:
                last_error = e
                retries += 1

                logger.warning(
                    "claude_api_retry",
                    error=str(e),
                    retries=retries,
                    max_retries=settings.CLAUDE_MAX_RETRIES
                )

                if retries < settings.CLAUDE_MAX_RETRIES:
                    # Exponential backoff: 1s, 2s, 4s
                    sleep_time = 2 ** (retries - 1)
                    time.sleep(sleep_time)
                else:
                    logger.error(
                        "claude_api_failed",
                        error=str(e),
                        retries=retries
                    )
                    raise Exception(f"Claude API failed after {retries} retries: {str(e)}")

        # Should never reach here, but just in case
        raise Exception(f"Claude API failed: {str(last_error)}")

    async def generate_async(
        self,
        messages: list[Dict[str, str]],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response from Claude (asynchronous)

        Same parameters as generate(), but async.
        """
        retries = 0
        last_error = None

        while retries < settings.CLAUDE_MAX_RETRIES:
            try:
                logger.info(
                    "claude_api_call_async",
                    model=self.model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                response: Message = await self.async_client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system if system else None,
                    messages=messages,
                    **kwargs
                )

                # Extract response text
                content = ""
                if response.content:
                    for block in response.content:
                        if hasattr(block, 'text'):
                            content += block.text

                # Calculate cost
                input_cost_per_1k = 0.003
                output_cost_per_1k = 0.015

                input_cost = (response.usage.input_tokens / 1000) * input_cost_per_1k
                output_cost = (response.usage.output_tokens / 1000) * output_cost_per_1k
                total_cost = input_cost + output_cost

                result = {
                    "content": content,
                    "role": response.role,
                    "model": response.model,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                    },
                    "cost_usd": total_cost,
                    "stop_reason": response.stop_reason,
                }

                logger.info(
                    "claude_api_success_async",
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    cost_usd=total_cost
                )

                return result

            except Exception as e:
                last_error = e
                retries += 1

                logger.warning(
                    "claude_api_retry_async",
                    error=str(e),
                    retries=retries
                )

                if retries < settings.CLAUDE_MAX_RETRIES:
                    sleep_time = 2 ** (retries - 1)
                    import asyncio
                    await asyncio.sleep(sleep_time)
                else:
                    logger.error("claude_api_failed_async", error=str(e))
                    raise Exception(f"Claude API failed after {retries} retries: {str(e)}")

        raise Exception(f"Claude API failed: {str(last_error)}")


# Global instance
claude_service = ClaudeService()

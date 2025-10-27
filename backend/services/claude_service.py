"""
OpenRouter API Service
Wrapper for OpenRouter API (using Claude Sonnet 4.5) with retry logic and error handling
"""
import time
import requests
from typing import Optional, Dict, Any
import structlog

from backend.config import settings

logger = structlog.get_logger()


class ClaudeService:
    """
    Service for interacting with Claude via OpenRouter API

    Features:
    - Retry logic with exponential backoff
    - Token usage tracking
    - Error handling
    - Support for both sync and async operations
    """

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "anthropic/claude-sonnet-4.5"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "DARKAGENTS",
            "Content-Type": "application/json"
        }

    def generate(
        self,
        messages: list[Dict[str, str]],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response from Claude via OpenRouter (synchronous)

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

        # Prepend system message if provided
        if system:
            messages = [{"role": "system", "content": system}] + messages

        while retries < settings.CLAUDE_MAX_RETRIES:
            try:
                logger.info(
                    "openrouter_api_call",
                    model=self.model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    num_messages=len(messages)
                )

                # Prepare request payload
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                }

                # Make API call
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=settings.CLAUDE_TIMEOUT
                )

                # Check for HTTP errors
                response.raise_for_status()

                # Parse response
                response_data = response.json()

                # Extract content
                content = response_data["choices"][0]["message"]["content"]

                # Extract usage stats
                usage = response_data.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", input_tokens + output_tokens)

                # Calculate cost (OpenRouter pricing - adjust as needed)
                # Claude Sonnet 4.5 pricing on OpenRouter (approximate)
                input_cost_per_1k = 0.003  # $0.003 per 1K input tokens
                output_cost_per_1k = 0.015  # $0.015 per 1K output tokens

                input_cost = (input_tokens / 1000) * input_cost_per_1k
                output_cost = (output_tokens / 1000) * output_cost_per_1k
                total_cost = input_cost + output_cost

                result = {
                    "content": content,
                    "role": "assistant",
                    "model": self.model,
                    "usage": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": total_tokens
                    },
                    "cost_usd": total_cost,
                    "stop_reason": response_data["choices"][0].get("finish_reason", "stop"),
                }

                logger.info(
                    "openrouter_api_success",
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=total_cost
                )

                return result

            except requests.exceptions.HTTPError as e:
                last_error = e
                retries += 1

                logger.warning(
                    "openrouter_api_http_error",
                    error=str(e),
                    status_code=e.response.status_code if hasattr(e, 'response') else None,
                    retries=retries,
                    max_retries=settings.CLAUDE_MAX_RETRIES
                )

                if retries < settings.CLAUDE_MAX_RETRIES:
                    # Exponential backoff: 1s, 2s, 4s
                    sleep_time = 2 ** (retries - 1)
                    time.sleep(sleep_time)
                else:
                    logger.error(
                        "openrouter_api_failed",
                        error=str(e),
                        retries=retries
                    )
                    raise Exception(f"OpenRouter API failed after {retries} retries: {str(e)}")

            except Exception as e:
                last_error = e
                retries += 1

                logger.warning(
                    "openrouter_api_retry",
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
                        "openrouter_api_failed",
                        error=str(e),
                        retries=retries
                    )
                    raise Exception(f"OpenRouter API failed after {retries} retries: {str(e)}")

        # Should never reach here, but just in case
        raise Exception(f"OpenRouter API failed: {str(last_error)}")

    async def generate_async(
        self,
        messages: list[Dict[str, str]],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response from Claude via OpenRouter (asynchronous)

        Same parameters as generate(), but async.
        Uses aiohttp for async HTTP requests.
        """
        import aiohttp
        import asyncio

        retries = 0
        last_error = None

        # Prepend system message if provided
        if system:
            messages = [{"role": "system", "content": system}] + messages

        while retries < settings.CLAUDE_MAX_RETRIES:
            try:
                logger.info(
                    "openrouter_api_call_async",
                    model=self.model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                # Prepare request payload
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.base_url,
                        headers=self.headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=settings.CLAUDE_TIMEOUT)
                    ) as response:
                        response.raise_for_status()
                        response_data = await response.json()

                # Extract content
                content = response_data["choices"][0]["message"]["content"]

                # Extract usage stats
                usage = response_data.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", input_tokens + output_tokens)

                # Calculate cost
                input_cost_per_1k = 0.003
                output_cost_per_1k = 0.015

                input_cost = (input_tokens / 1000) * input_cost_per_1k
                output_cost = (output_tokens / 1000) * output_cost_per_1k
                total_cost = input_cost + output_cost

                result = {
                    "content": content,
                    "role": "assistant",
                    "model": self.model,
                    "usage": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": total_tokens
                    },
                    "cost_usd": total_cost,
                    "stop_reason": response_data["choices"][0].get("finish_reason", "stop"),
                }

                logger.info(
                    "openrouter_api_success_async",
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=total_cost
                )

                return result

            except aiohttp.ClientError as e:
                last_error = e
                retries += 1

                logger.warning(
                    "openrouter_api_retry_async",
                    error=str(e),
                    retries=retries
                )

                if retries < settings.CLAUDE_MAX_RETRIES:
                    sleep_time = 2 ** (retries - 1)
                    await asyncio.sleep(sleep_time)
                else:
                    logger.error("openrouter_api_failed_async", error=str(e))
                    raise Exception(f"OpenRouter API failed after {retries} retries: {str(e)}")

            except Exception as e:
                last_error = e
                retries += 1

                logger.warning(
                    "openrouter_api_retry_async",
                    error=str(e),
                    retries=retries
                )

                if retries < settings.CLAUDE_MAX_RETRIES:
                    sleep_time = 2 ** (retries - 1)
                    await asyncio.sleep(sleep_time)
                else:
                    logger.error("openrouter_api_failed_async", error=str(e))
                    raise Exception(f"OpenRouter API failed after {retries} retries: {str(e)}")

        raise Exception(f"OpenRouter API failed: {str(last_error)}")


# Global instance
claude_service = ClaudeService()

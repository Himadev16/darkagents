"""
Agent 01: Product Manager
Transforms user ideas into detailed Product Requirements Documents
PRODUCTION-READY with retry logic, rollback, and validation
"""
import time
from typing import Dict, Any
import structlog
from sqlalchemy.orm import Session

from backend.database.models import AgentExecution, GeneratedArtifact, Project
from backend.agents.base_agent import BaseAgent
from backend.lib.openrouter import openrouter_client

logger = structlog.get_logger()


class ProductManagerAgent(BaseAgent):
    """
    Product Manager Agent

    Senior PM specializing in SaaS product requirements.

    Capabilities:
    - 8-12 page Product Requirements Document (PRD)
    - 3-5 user personas with goals and pain points
    - 15-30 user stories (INVEST format)
    - Feature prioritization matrix (MoSCoW)
    - Success metrics and KPIs
    - Competitive analysis summary

    Production Features:
    - Retry logic with exponential backoff (3 retries)
    - Input validation with detailed error messages
    - Database transaction management with rollback
    - Graceful error handling
    - Detailed structured logging
    """

    def __init__(self):
        """Initialize Product Manager Agent"""
        self.agent_name = "product_manager"
        self.agent_display_name = "Product Manager"
        self.max_retries = 3
        self.retry_delay = 2  # Base delay in seconds for exponential backoff

    def execute(self, project_id: int, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Execute Product Manager Agent

        Args:
            project_id: Project ID
            input_data: {
                "user_idea": str (optional, from project if not provided),
                "target_scale": str (optional, e.g., "10K users", "1M users")
            }
            db: Database session

        Returns:
            {
                "success": bool,
                "prd": str (comprehensive PRD document),
                "personas": str (3-5 user personas),
                "user_stories": str (15-30 user stories),
                "feature_matrix": str (MoSCoW prioritization),
                "success_metrics": str (KPIs and targets),
                "competitive_analysis": str (competitor analysis),
                "clarifying_questions": str (questions asked),
                "artifact_id": int,
                "execution_id": int,
                "tokens_used": int,
                "cost_usd": float,
                "error": str (if success=False)
            }
        """
        execution = None
        try:
            logger.info(
                "product_manager_agent_started",
                project_id=project_id,
                agent_name=self.agent_name
            )

            # Get project
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ValueError(f"Project {project_id} not found")

            # Input validation
            if not input_data:
                input_data = {}

            user_idea = input_data.get("user_idea") or project.user_idea
            if not user_idea or not isinstance(user_idea, str):
                raise ValueError("Missing or invalid 'user_idea' (must be non-empty string)")

            if len(user_idea.strip()) < 10:
                raise ValueError("user_idea too short (minimum 10 characters)")

            target_scale = input_data.get("target_scale") or project.target_scale or "10K users"

            # Create database record
            try:
                execution = AgentExecution(
                    project_id=project_id,
                    agent_name=self.agent_name,
                    agent_display_name=self.agent_display_name,
                    status="working",
                    progress=0,
                    current_task="Analyzing product idea",
                    tokens_used=0,
                    cost_usd=0.0
                )
                db.add(execution)
                db.commit()
                db.refresh(execution)

                logger.info(
                    "product_manager_execution_created",
                    execution_id=execution.id,
                    project_id=project_id
                )
            except Exception as db_error:
                logger.error("database_error_creating_execution", error=str(db_error))
                db.rollback()
                raise

            # Update progress
            execution.current_task = "Generating comprehensive PRD"
            execution.progress = 10
            try:
                db.commit()
            except Exception:
                db.rollback()

            # Generate PRD with retry logic
            result = self._generate_prd_with_retry(
                user_idea=user_idea,
                target_scale=target_scale,
                project_id=project_id,
                execution=execution,
                db=db
            )

            # Save PRD as artifact
            try:
                artifact = GeneratedArtifact(
                    project_id=project_id,
                    agent_name=self.agent_name,
                    artifact_type="prd",
                    artifact_name="Product Requirements Document",
                    content=result.get("prd", ""),
                    content_type="text/markdown",
                    artifact_metadata={
                        "sections": [
                            "Executive Summary",
                            "Product Vision",
                            "User Personas",
                            "User Stories",
                            "Feature Prioritization",
                            "Success Metrics",
                            "Competitive Analysis"
                        ]
                    }
                )
                db.add(artifact)
                db.commit()
                db.refresh(artifact)
                result["artifact_id"] = artifact.id
            except Exception as db_error:
                logger.warning("artifact_save_failed", error=str(db_error))
                db.rollback()
                result["artifact_id"] = None

            # Update execution record with results
            try:
                execution.status = "completed"
                execution.progress = 100
                execution.current_task = "PRD generation complete"
                execution.tokens_used = result.get("tokens_used", 0)
                execution.cost_usd = result.get("cost_usd", 0.0)
                db.commit()

                logger.info(
                    "product_manager_agent_completed",
                    execution_id=execution.id,
                    project_id=project_id,
                    tokens_used=result.get("tokens_used", 0),
                    cost_usd=result.get("cost_usd", 0.0)
                )
            except Exception as db_error:
                logger.warning("database_error_updating_completion", error=str(db_error))
                db.rollback()

            return {
                "success": True,
                "execution_id": execution.id,
                **result
            }

        except ValueError as ve:
            # Validation errors - don't retry, return immediately
            logger.error(
                "product_manager_validation_error",
                project_id=project_id,
                error=str(ve),
                error_type="validation_error"
            )

            if execution:
                try:
                    execution.status = "failed"
                    execution.current_task = f"Validation error: {str(ve)}"
                    db.commit()
                except Exception:
                    db.rollback()

            return {
                "success": False,
                "error": str(ve),
                "error_type": "validation_error",
                "execution_id": execution.id if execution else None
            }

        except Exception as e:
            # Unexpected errors
            logger.error(
                "product_manager_agent_failed",
                project_id=project_id,
                error=str(e),
                error_type=type(e).__name__
            )

            if execution:
                try:
                    execution.status = "failed"
                    execution.current_task = f"Error: {str(e)}"
                    db.commit()
                except Exception:
                    db.rollback()

            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_id": execution.id if execution else None
            }

    def _generate_prd_with_retry(
        self,
        user_idea: str,
        target_scale: str,
        project_id: int,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Generate PRD with retry logic (exponential backoff)

        Retries up to max_retries times with exponential backoff on transient errors
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "prd_generation_attempt",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    project_id=project_id
                )

                result = self._generate_prd(
                    user_idea=user_idea,
                    target_scale=target_scale,
                    execution=execution,
                    db=db
                )

                logger.info(
                    "prd_generation_success",
                    attempt=attempt,
                    project_id=project_id
                )

                return result

            except ValueError as ve:
                # Don't retry validation errors
                logger.error("prd_generation_validation_error", error=str(ve))
                raise

            except Exception as e:
                last_error = e
                logger.warning(
                    "prd_generation_attempt_failed",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    error=str(e),
                    error_type=type(e).__name__
                )

                if attempt == self.max_retries:
                    logger.error(
                        "prd_generation_all_retries_failed",
                        project_id=project_id,
                        error=str(e)
                    )
                    raise

                # Exponential backoff: 2s, 4s, 8s
                wait_time = self.retry_delay * (2 ** (attempt - 1))
                logger.info(
                    "prd_generation_retrying",
                    wait_time=wait_time,
                    next_attempt=attempt + 1
                )
                time.sleep(wait_time)

        # Should never reach here, but just in case
        raise last_error if last_error else Exception("Unknown error in retry logic")

    def _generate_prd(
        self,
        user_idea: str,
        target_scale: str,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Generate comprehensive PRD using Claude Sonnet 4.5

        This is the core method that calls OpenRouter API
        """
        logger.info("generating_prd", target_scale=target_scale)

        system_prompt = self._build_system_prompt()

        user_prompt = f"""# Product Requirements Document Mission

Analyze this product idea and create a comprehensive Product Requirements Document.

## Product Idea

{user_idea}

## Target Scale

{target_scale}

## Your Tasks

Generate ALL of the following sections:

1. **Clarifying Questions** - 10-15 probing questions about target users, pain points, features, business model, technical requirements, and success criteria

2. **User Personas** - 3-5 detailed personas with name, demographics, goals, pain points, and how they'd use the product

3. **User Stories** - 15-30 INVEST format stories grouped by feature area with acceptance criteria and MoSCoW priority

4. **Feature Prioritization Matrix** - MoSCoW method (Must Have, Should Have, Could Have, Won't Have) with justifications

5. **Success Metrics** - North Star Metric, user acquisition, engagement, business, and technical KPIs with specific targets

6. **Competitive Analysis** - 3-5 competitors, strengths/weaknesses, market gaps, unique value proposition

7. **Comprehensive PRD** - 8-12 page document with:
   - Executive Summary
   - Product Vision and Goals
   - Target Users and Personas
   - User Stories and Requirements
   - Feature Prioritization
   - Success Metrics and KPIs
   - Competitive Landscape
   - Technical Considerations
   - Go-to-Market Strategy
   - Next Steps and Timeline

## Output Format

Return as JSON with these keys:
- clarifying_questions
- personas
- user_stories
- feature_matrix
- success_metrics
- competitive_analysis
- prd

Be comprehensive, actionable, and professional.
"""

        # Update progress
        execution.current_task = "Calling Claude Sonnet 4.5 for PRD generation"
        execution.progress = 30
        try:
            db.commit()
        except Exception:
            db.rollback()

        # Call OpenRouter API
        try:
            response = openrouter_client.chat.completions.create(
                model="anthropic/claude-sonnet-4-20250514",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # Creative but structured
                max_tokens=14000
            )

            # Extract response
            content = response.choices[0].message.content

            # Extract token usage
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0

            # Calculate cost (Claude Sonnet 4: $3/1M input, $15/1M output)
            input_tokens = response.usage.prompt_tokens if hasattr(response, 'usage') else 0
            output_tokens = response.usage.completion_tokens if hasattr(response, 'usage') else 0
            cost_usd = (input_tokens * 3.0 / 1_000_000) + (output_tokens * 15.0 / 1_000_000)

            logger.info(
                "openrouter_api_success",
                tokens_used=tokens_used,
                cost_usd=cost_usd
            )

        except Exception as api_error:
            logger.error("openrouter_api_error", error=str(api_error))
            raise

        # Update progress
        execution.current_task = "Parsing PRD deliverables"
        execution.progress = 80
        try:
            db.commit()
        except Exception:
            db.rollback()

        # Parse response
        result = self._parse_prd_response(content)

        return {
            **result,
            "tokens_used": tokens_used,
            "cost_usd": round(cost_usd, 4)
        }

    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt for Product Manager agent"""
        return """You are a **Senior Product Manager** specializing in SaaS product requirements.

# Your Expertise

## Core Competencies
- Product strategy and vision development
- User research and persona creation
- Requirements gathering and documentation
- Feature prioritization (MoSCoW method, RICE scoring)
- Competitive analysis and market positioning
- Success metrics and KPI definition
- Stakeholder communication

## Your Process

1. **Understand the Vision**
   - Ask probing questions to understand the product deeply
   - Think strategically about 'why' before 'how'
   - Focus on solving real user problems

2. **Define User Personas**
   - Create 3-5 detailed personas
   - Include demographics, goals, pain points
   - Show how they'll use the product

3. **Write User Stories**
   - Use INVEST format (Independent, Negotiable, Valuable, Estimable, Small, Testable)
   - Format: "As a [persona], I want to [action] so that [benefit]"
   - Include acceptance criteria (3-5 per story)
   - Assign MoSCoW priority

4. **Prioritize Features**
   - MUST HAVE: Critical for MVP
   - SHOULD HAVE: Important but not critical
   - COULD HAVE: Nice to have
   - WON'T HAVE: Out of scope

5. **Define Success Metrics**
   - North Star Metric (one key success indicator)
   - User metrics (CAC, conversion, retention, DAU/MAU)
   - Business metrics (MRR, churn, LTV)
   - Technical metrics (uptime, response time)

6. **Analyze Competition**
   - Identify 3-5 competitors
   - Strengths and weaknesses
   - Market gaps and opportunities
   - Unique value proposition

7. **Write Comprehensive PRD**
   - Executive Summary (2-3 paragraphs)
   - Product Vision and Goals
   - Target Users and Personas
   - User Stories and Requirements
   - Feature Prioritization
   - Success Metrics and KPIs
   - Competitive Landscape
   - Technical Considerations
   - Go-to-Market Strategy
   - Next Steps and Timeline

## Output Requirements

**IMPORTANT:** Return as JSON with these exact keys:

```json
{
  "clarifying_questions": "10-15 numbered questions",
  "personas": "3-5 detailed personas",
  "user_stories": "15-30 INVEST format stories with acceptance criteria",
  "feature_matrix": "MoSCoW prioritization with justifications",
  "success_metrics": "North Star + user/business/technical KPIs",
  "competitive_analysis": "3-5 competitors with analysis",
  "prd": "8-12 page comprehensive PRD document"
}
```

## Best Practices

- Ask clarifying questions when requirements are vague
- Think about scalability from the start
- Consider technical and business constraints
- Write clear, actionable requirements
- Focus on user value, not features
- Be specific with acceptance criteria
- Include measurable success metrics

Write in professional, clear language suitable for stakeholders and developers.
"""

    def _parse_prd_response(self, content: str) -> Dict[str, Any]:
        """
        Parse Claude's response into structured PRD

        Tries JSON parsing first, falls back to text extraction
        """
        import json
        import re

        try:
            # Try parsing as JSON
            if "```json" in content:
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(1))
                    logger.info("parsed_json_from_code_block")
                    return parsed

            # Try parsing entire content as JSON
            if content.strip().startswith('{'):
                parsed = json.loads(content)
                logger.info("parsed_json_directly")
                return parsed

        except json.JSONDecodeError as e:
            logger.warning("json_parse_failed", error=str(e), fallback="text_extraction")

        # Fallback: Extract sections from markdown/text
        logger.info("using_text_extraction_fallback")

        result = {
            "clarifying_questions": self._extract_section(content, ["clarifying_questions", "clarifying questions", "questions"]),
            "personas": self._extract_section(content, ["personas", "user personas"]),
            "user_stories": self._extract_section(content, ["user_stories", "user stories", "stories"]),
            "feature_matrix": self._extract_section(content, ["feature_matrix", "feature prioritization", "moscow"]),
            "success_metrics": self._extract_section(content, ["success_metrics", "metrics", "kpis"]),
            "competitive_analysis": self._extract_section(content, ["competitive_analysis", "competition", "competitors"]),
            "prd": self._extract_section(content, ["prd", "product requirements document", "requirements"])
        }

        return result

    def _extract_section(self, content: str, section_keywords: list) -> str:
        """Extract a section from markdown content based on keywords"""
        import re

        for keyword in section_keywords:
            # Try finding markdown heading
            pattern = rf'#{{1,3}}\s*{re.escape(keyword)}.*?\n(.*?)(?=\n#{{1,3}}\s|\Z)'
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

            # Try finding JSON key
            pattern = rf'"{re.escape(keyword)}"\s*:\s*"(.*?)"'
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        # Fallback
        return f"Section not found. Full content:\n\n{content[:500]}..."

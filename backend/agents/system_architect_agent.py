"""
Agent 02: System Architect
Designs complete system architectures for SaaS applications
PRODUCTION-READY with retry logic, rollback, and validation
"""
import time
from typing import Dict, Any
import structlog
from sqlalchemy.orm import Session

from backend.database.models import AgentExecution, Project
from backend.agents.base_agent import BaseAgent
from backend.services.claude_service import claude_service

logger = structlog.get_logger()


class SystemArchitectAgent(BaseAgent):
    """
    System Architect Agent

    Senior technical architect with 15+ years enterprise experience.

    Capabilities:
    - Complete database schema (SQLAlchemy models)
    - API specifications (REST endpoints with Pydantic schemas)
    - Tech stack recommendations (FastAPI, Next.js, PostgreSQL)
    - Infrastructure plan (deployment, CI/CD, monitoring)
    - Security architecture (auth, encryption, OWASP Top 10)
    - Scalability plan (caching, load balancing, optimization)
    - Cost estimates (1K to 1M+ users)

    Production Features:
    - Retry logic with exponential backoff (3 retries)
    - Input validation with detailed error messages
    - Database transaction management with rollback
    - Graceful error handling
    - Detailed structured logging
    """

    def __init__(self):
        """Initialize System Architect Agent"""
        self.agent_name = "system_architect"
        self.agent_display_name = "System Architect"
        self.max_retries = 3
        self.retry_delay = 2  # Base delay in seconds for exponential backoff

    def execute(self, project_id: int, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Execute System Architect Agent

        Args:
            project_id: Project ID
            input_data: {
                "prd": str (PRD from Product Manager, optional),
                "requirements": str (alternative to prd),
                "target_users": str (optional, e.g., "General users"),
                "expected_scale": str (optional, e.g., "1K-10K users", "100K+ users")
            }
            db: Database session

        Returns:
            {
                "success": bool,
                "architecture": str (comprehensive architecture document),
                "database_schema": str (SQLAlchemy models),
                "api_specifications": str (REST endpoint specs),
                "tech_stack": str (technology recommendations),
                "infrastructure_plan": str (deployment architecture),
                "security_architecture": str (auth, encryption, OWASP mitigations),
                "scalability_plan": str (scaling strategy),
                "cost_estimates": str (monthly costs per tier),
                "execution_id": int,
                "tokens_used": int,
                "cost_usd": float,
                "error": str (if success=False)
            }
        """
        execution = None
        try:
            logger.info(
                "system_architect_agent_started",
                project_id=project_id,
                agent_name=self.agent_name
            )

            # Input validation
            if not input_data:
                input_data = {}

            prd = input_data.get("prd") or input_data.get("requirements", "")
            if not prd or not isinstance(prd, str):
                raise ValueError("Missing or invalid 'prd' or 'requirements' (must be non-empty string)")

            if len(prd.strip()) < 20:
                raise ValueError("prd/requirements too short (minimum 20 characters)")

            # Optional fields with safe defaults
            target_users = input_data.get("target_users", "General users")
            expected_scale = input_data.get("expected_scale", "1K-10K users")

            # Create database record
            try:
                execution = AgentExecution(
                    project_id=project_id,
                    agent_name=self.agent_name,
                    agent_display_name=self.agent_display_name,
                    status="working",
                    progress=0,
                    current_task="Analyzing product requirements",
                    tokens_used=0,
                    cost_usd=0.0
                )
                db.add(execution)
                db.commit()
                db.refresh(execution)

                logger.info(
                    "system_architect_execution_created",
                    execution_id=execution.id,
                    project_id=project_id
                )
            except Exception as db_error:
                logger.error("database_error_creating_execution", error=str(db_error))
                db.rollback()
                raise

            # Update progress
            execution.current_task = "Designing system architecture"
            execution.progress = 10
            try:
                db.commit()
            except Exception:
                db.rollback()

            # Generate architecture with retry logic
            result = self._generate_architecture_with_retry(
                prd=prd,
                target_users=target_users,
                expected_scale=expected_scale,
                project_id=project_id,
                execution=execution,
                db=db
            )

            # Update execution record with results
            try:
                execution.status = "completed"
                execution.progress = 100
                execution.current_task = "Architecture design complete"
                execution.tokens_used = result.get("tokens_used", 0)
                execution.cost_usd = result.get("cost_usd", 0.0)
                db.commit()

                logger.info(
                    "system_architect_agent_completed",
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
                "system_architect_validation_error",
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
                "system_architect_agent_failed",
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

    def _generate_architecture_with_retry(
        self,
        prd: str,
        target_users: str,
        expected_scale: str,
        project_id: int,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Generate architecture with retry logic (exponential backoff)

        Retries up to max_retries times with exponential backoff on transient errors
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "architecture_generation_attempt",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    project_id=project_id
                )

                result = self._generate_architecture(
                    prd=prd,
                    target_users=target_users,
                    expected_scale=expected_scale,
                    execution=execution,
                    db=db
                )

                logger.info(
                    "architecture_generation_success",
                    attempt=attempt,
                    project_id=project_id
                )

                return result

            except ValueError as ve:
                # Don't retry validation errors
                logger.error("architecture_generation_validation_error", error=str(ve))
                raise

            except Exception as e:
                last_error = e
                logger.warning(
                    "architecture_generation_attempt_failed",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    error=str(e),
                    error_type=type(e).__name__
                )

                if attempt == self.max_retries:
                    logger.error(
                        "architecture_generation_all_retries_failed",
                        project_id=project_id,
                        error=str(e)
                    )
                    raise

                # Exponential backoff: 2s, 4s, 8s
                wait_time = self.retry_delay * (2 ** (attempt - 1))
                logger.info(
                    "architecture_generation_retrying",
                    wait_time=wait_time,
                    next_attempt=attempt + 1
                )
                time.sleep(wait_time)

        # Should never reach here, but just in case
        raise last_error if last_error else Exception("Unknown error in retry logic")

    def _generate_architecture(
        self,
        prd: str,
        target_users: str,
        expected_scale: str,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Generate comprehensive system architecture using Claude Sonnet 4.5

        This is the core method that calls OpenRouter API
        """
        logger.info("generating_architecture", expected_scale=expected_scale)

        system_prompt = self._build_system_prompt()

        user_prompt = f"""# System Architecture Mission

Design a complete, production-ready system architecture for this SaaS product.

## Product Requirements (PRD)

{prd[:2000]}...

## Target Users

{target_users}

## Expected Scale

{expected_scale}

## Your Deliverables

Generate ALL of the following sections:

1. **Executive Summary** - High-level architecture overview, key decisions, estimated costs

2. **Database Schema** - Complete SQLAlchemy models with relationships, indexes, and migration strategy

3. **API Specifications** - REST endpoint definitions with request/response schemas, auth flow, rate limiting

4. **Tech Stack** - Backend (FastAPI, PostgreSQL), Frontend (Next.js, TypeScript), deployment platforms

5. **Infrastructure Plan** - Deployment architecture, environments (dev/staging/prod), CI/CD pipeline, monitoring

6. **Security Architecture** - Auth/authorization, encryption, API security, secret management, OWASP Top 10 mitigations

7. **Scalability Plan** - Horizontal scaling, database optimization, caching strategy, load balancing, cost projections

8. **Cost Estimates** - Infrastructure costs for 1K, 10K, 100K, 1M users

## Output Format

Return as JSON with these keys:
- executive_summary
- database_schema
- api_specifications
- tech_stack
- infrastructure_plan
- security_architecture
- scalability_plan
- cost_estimates
- architecture (full comprehensive document)

Be specific, production-ready, and include actual code for schemas.
"""

        # Update progress
        execution.current_task = "Calling Claude Sonnet 4.5 for architecture design"
        execution.progress = 30
        try:
            db.commit()
        except Exception:
            db.rollback()

        # Call Claude service via OpenRouter API
        try:
            response = claude_service.generate(
                messages=[{"role": "user", "content": user_prompt}],
                system=system_prompt,
                temperature=0.4,  # Balanced - creative architecture but structured
                max_tokens=12000
            )

            # Extract response
            content = response["content"]

            # Extract token usage
            tokens_used = response["usage"]["total_tokens"]

            # Calculate cost (Claude Sonnet 4: $3/1M input, $15/1M output)
            cost_usd = response["cost_usd"]

            logger.info(
                "openrouter_api_success",
                tokens_used=tokens_used,
                cost_usd=cost_usd
            )

        except Exception as api_error:
            logger.error("openrouter_api_error", error=str(api_error))
            raise

        # Update progress
        execution.current_task = "Parsing architecture deliverables"
        execution.progress = 80
        try:
            db.commit()
        except Exception:
            db.rollback()

        # Parse response
        result = self._parse_architecture_response(content)

        return {
            **result,
            "tokens_used": tokens_used,
            "cost_usd": round(cost_usd, 4)
        }

    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt for System Architect agent"""
        return """You are a **Senior System Architect** with 15+ years of enterprise experience.

# Your Expertise

You design complete, production-ready system architectures for SaaS applications that are:
- **Scalable** (handle 1K to 1M+ users)
- **Secure** (OWASP Top 10 compliant)
- **Cost-effective** (optimized infrastructure)
- **Maintainable** (clean separation of concerns)
- **Modern** (latest best practices)

## Tech Stack Standards

**Backend:**
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0 with async support
- PostgreSQL (primary database)
- Redis (caching, sessions)
- JWT authentication with refresh tokens

**Frontend:**
- Next.js 14+ with App Router
- TypeScript (strict mode)
- Tailwind CSS for styling
- React Query for state management

**Deployment:**
- Vercel (frontend hosting)
- Railway or AWS (backend hosting)
- GitHub Actions (CI/CD)
- PostgreSQL managed service

## Output Requirements

**IMPORTANT:** Return as JSON with these exact keys:

```json
{
  "executive_summary": "High-level overview, key decisions, cost estimates",
  "database_schema": "Complete SQLAlchemy models with Python code",
  "api_specifications": "REST endpoints with request/response schemas",
  "tech_stack": "Technology choices with justifications",
  "infrastructure_plan": "Deployment architecture, CI/CD, monitoring",
  "security_architecture": "Auth, encryption, OWASP Top 10 mitigations",
  "scalability_plan": "Scaling strategy, optimization, cost projections",
  "cost_estimates": "Monthly costs for 1K, 10K, 100K, 1M users",
  "architecture": "Complete comprehensive architecture document"
}
```

## Database Schema Requirements

Provide complete SQLAlchemy models:
- Table definitions with proper types
- Foreign key relationships
- Indexes for performance
- Unique constraints
- Default values
- Timestamps (created_at, updated_at)

## API Specifications Requirements

For each endpoint provide:
- HTTP method and path
- Description
- Request body schema (Pydantic)
- Response schema (Pydantic)
- Authentication requirements
- Error responses

## Security Requirements

- JWT authentication with refresh tokens
- Password hashing (bcrypt or argon2)
- HTTPS only (TLS 1.3)
- API rate limiting
- CORS configuration
- XSS protection
- SQL injection prevention (parameterized queries)
- Secret management (environment variables)

## Scalability Requirements

- Horizontal scaling with load balancer
- Database connection pooling
- Redis caching strategy
- CDN for static assets
- Database query optimization
- Async operations where applicable

Be specific and production-ready!
"""

    def _parse_architecture_response(self, content: str) -> Dict[str, Any]:
        """
        Parse Claude's response into structured architecture

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
            "executive_summary": self._extract_section(content, ["executive_summary", "executive summary", "overview"]),
            "database_schema": self._extract_section(content, ["database_schema", "database schema", "schema"]),
            "api_specifications": self._extract_section(content, ["api_specifications", "api specs", "endpoints"]),
            "tech_stack": self._extract_section(content, ["tech_stack", "technology stack", "technologies"]),
            "infrastructure_plan": self._extract_section(content, ["infrastructure_plan", "infrastructure", "deployment"]),
            "security_architecture": self._extract_section(content, ["security_architecture", "security", "auth"]),
            "scalability_plan": self._extract_section(content, ["scalability_plan", "scalability", "scaling"]),
            "cost_estimates": self._extract_section(content, ["cost_estimates", "costs", "pricing"]),
            "architecture": content  # Full document
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
        return f"Section not found. See full architecture document."

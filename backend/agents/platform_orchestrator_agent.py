"""
Agent 10: Platform Orchestrator
Final assembly and packaging of complete SaaS business deliverables
"""
import time
from typing import Dict, Any
import structlog
from sqlalchemy.orm import Session

from backend.database.models import AgentExecution
from backend.agents.base_agent import BaseAgent
from backend.lib.openrouter import openrouter_client

logger = structlog.get_logger()


class PlatformOrchestratorAgent(BaseAgent):
    """
    Platform Orchestrator Agent

    Senior project orchestrator - The FINAL agent that assembles everything.

    Capabilities:
    - Collect and validate outputs from all 9 previous agents
    - Assemble complete SaaS business package
    - Generate comprehensive documentation (README, setup guides, API docs)
    - Create deployment checklist and quality assurance steps
    - Produce handoff materials for the user
    - Summarize total costs, timeline, and deliverables
    - Generate project structure and file organization
    - Create final package with all assets organized
    - Provide executive summary of the complete deliverable
    - Generate "What's Next" recommendations and roadmap

    Input: Outputs from all 9 previous agents
    Output: Complete SaaS business package ready for delivery

    Production Features:
    - Retry logic with exponential backoff (3 retries)
    - Input validation with detailed error messages
    - Database transaction management with rollback
    - Graceful error handling
    - Detailed structured logging
    """

    def __init__(self):
        """Initialize Platform Orchestrator Agent"""
        self.agent_name = "platform_orchestrator"
        self.agent_display_name = "Platform Orchestrator"
        self.max_retries = 3
        self.retry_delay = 2  # Base delay in seconds for exponential backoff

    def execute(self, project_id: int, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Execute Platform Orchestrator Agent

        Args:
            project_id: Project ID
            input_data: {
                "pm_output": str (PRD from Product Manager),
                "architect_output": str (System design from Architect),
                "polyglot_output": str (Code from Polyglot Developer),
                "designer_output": str (UI design from Designer),
                "qa_output": str (Test suite from QA Engineer),
                "security_output": str (Security audit from Security Specialist),
                "devops_output": str (Deployment config from DevOps Engineer),
                "growth_output": str (Marketing assets from Growth Marketer),
                "business_output": str (Business model from Business Strategist),
                "project_name": str (optional, project name),
                "delivery_format": str (optional, "comprehensive" or "executive_summary")
            }
            db: Database session

        Returns:
            {
                "success": bool,
                "executive_summary": str (High-level overview of the complete package),
                "project_structure": str (Complete file/folder organization),
                "documentation_package": str (README, setup guides, API docs),
                "deployment_checklist": str (Step-by-step deployment guide),
                "quality_assurance_checklist": str (QA checklist before launch),
                "handoff_materials": str (Materials for user handoff),
                "cost_summary": str (Total costs breakdown from all agents),
                "timeline_summary": str (Timeline and milestones),
                "deliverables_manifest": str (Complete list of deliverables),
                "whats_next_roadmap": str (Recommendations for next steps),
                "total_tokens_used": int (Tokens from all agents),
                "total_cost_usd": float (Total cost from all agents),
                "execution_id": int,
                "tokens_used": int,
                "cost_usd": float,
                "error": str (if success=False)
            }
        """
        execution = None
        try:
            logger.info(
                "platform_orchestrator_agent_started",
                project_id=project_id,
                agent_name=self.agent_name
            )

            # Input validation
            if not input_data:
                raise ValueError("input_data is required")

            # Validate that we have outputs from all agents
            required_outputs = [
                "pm_output", "architect_output", "polyglot_output",
                "designer_output", "qa_output", "security_output",
                "devops_output", "growth_output", "business_output"
            ]

            missing_outputs = []
            for output_key in required_outputs:
                if not input_data.get(output_key):
                    missing_outputs.append(output_key)

            if missing_outputs:
                logger.warning("missing_agent_outputs", missing=missing_outputs)
                # Don't fail - we can work with partial data, but log it

            # Optional fields
            project_name = input_data.get("project_name", "DARKAGENTS SaaS Project")
            delivery_format = input_data.get("delivery_format", "comprehensive")

            # Create database record
            try:
                execution = AgentExecution(
                    project_id=project_id,
                    agent_name=self.agent_name,
                    agent_display_name=self.agent_display_name,
                    status="working",
                    progress=0,
                    current_task="Collecting outputs from all agents",
                    tokens_used=0,
                    cost_usd=0.0
                )
                db.add(execution)
                db.commit()
                db.refresh(execution)

                logger.info(
                    "platform_orchestrator_execution_created",
                    execution_id=execution.id,
                    project_id=project_id
                )
            except Exception as db_error:
                logger.error("database_error_creating_execution", error=str(db_error))
                db.rollback()
                raise

            # Update progress
            execution.current_task = "Assembling complete SaaS business package"
            execution.progress = 10
            try:
                db.commit()
            except Exception:
                db.rollback()

            # Orchestrate final package with retry logic
            result = self._orchestrate_final_package_with_retry(
                pm_output=input_data.get("pm_output", ""),
                architect_output=input_data.get("architect_output", ""),
                polyglot_output=input_data.get("polyglot_output", ""),
                designer_output=input_data.get("designer_output", ""),
                qa_output=input_data.get("qa_output", ""),
                security_output=input_data.get("security_output", ""),
                devops_output=input_data.get("devops_output", ""),
                growth_output=input_data.get("growth_output", ""),
                business_output=input_data.get("business_output", ""),
                project_name=project_name,
                delivery_format=delivery_format,
                project_id=project_id,
                execution=execution,
                db=db
            )

            # Update execution record with results
            try:
                execution.status = "completed"
                execution.progress = 100
                execution.current_task = "Final SaaS business package complete"
                execution.tokens_used = result.get("tokens_used", 0)
                execution.cost_usd = result.get("cost_usd", 0.0)
                db.commit()

                logger.info(
                    "platform_orchestrator_agent_completed",
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
                "platform_orchestrator_validation_error",
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
                "platform_orchestrator_agent_failed",
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

    def _orchestrate_final_package_with_retry(
        self,
        pm_output: str,
        architect_output: str,
        polyglot_output: str,
        designer_output: str,
        qa_output: str,
        security_output: str,
        devops_output: str,
        growth_output: str,
        business_output: str,
        project_name: str,
        delivery_format: str,
        project_id: int,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Orchestrate final package with retry logic (exponential backoff)

        Retries up to max_retries times with exponential backoff on transient errors
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "orchestration_attempt",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    project_id=project_id
                )

                result = self._orchestrate_final_package(
                    pm_output=pm_output,
                    architect_output=architect_output,
                    polyglot_output=polyglot_output,
                    designer_output=designer_output,
                    qa_output=qa_output,
                    security_output=security_output,
                    devops_output=devops_output,
                    growth_output=growth_output,
                    business_output=business_output,
                    project_name=project_name,
                    delivery_format=delivery_format,
                    execution=execution,
                    db=db
                )

                logger.info(
                    "orchestration_success",
                    attempt=attempt,
                    project_id=project_id
                )

                return result

            except ValueError as ve:
                # Don't retry validation errors
                logger.error("orchestration_validation_error", error=str(ve))
                raise

            except Exception as e:
                last_error = e
                logger.warning(
                    "orchestration_attempt_failed",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    error=str(e),
                    error_type=type(e).__name__
                )

                if attempt == self.max_retries:
                    logger.error(
                        "orchestration_all_retries_failed",
                        project_id=project_id,
                        error=str(e)
                    )
                    raise

                # Exponential backoff: 2s, 4s, 8s
                wait_time = self.retry_delay * (2 ** (attempt - 1))
                logger.info(
                    "orchestration_retrying",
                    wait_time=wait_time,
                    next_attempt=attempt + 1
                )
                time.sleep(wait_time)

        # Should never reach here, but just in case
        raise last_error if last_error else Exception("Unknown error in retry logic")

    def _orchestrate_final_package(
        self,
        pm_output: str,
        architect_output: str,
        polyglot_output: str,
        designer_output: str,
        qa_output: str,
        security_output: str,
        devops_output: str,
        growth_output: str,
        business_output: str,
        project_name: str,
        delivery_format: str,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Orchestrate final package using Claude Sonnet 4.5

        This is the core method that calls OpenRouter API
        """
        logger.info("orchestrating_final_package", project_name=project_name, format=delivery_format)

        system_prompt = self._build_system_prompt()

        # Build user prompt with all agent outputs
        user_prompt = f"""
# Final Package Orchestration Mission

You are the final orchestrator assembling a complete SaaS business package from 9 specialized agents.

## Project Information

**Project Name:** {project_name}

**Delivery Format:** {delivery_format}

## Agent Outputs (All Collected)

### Agent 01: Product Manager Output
{pm_output[:1000] if pm_output else "Not available"}...

### Agent 02: System Architect Output
{architect_output[:1000] if architect_output else "Not available"}...

### Agent 03: Polyglot Developer Output
{polyglot_output[:1000] if polyglot_output else "Not available"}...

### Agent 04: UI/UX Designer Output
{designer_output[:1000] if designer_output else "Not available"}...

### Agent 05: QA Engineer Output
{qa_output[:1000] if qa_output else "Not available"}...

### Agent 06: Security Specialist Output
{security_output[:1000] if security_output else "Not available"}...

### Agent 07: DevOps Engineer Output
{devops_output[:1000] if devops_output else "Not available"}...

### Agent 08: Growth Marketer Output
{growth_output[:1000] if growth_output else "Not available"}...

### Agent 09: Business Strategist Output
{business_output[:1000] if business_output else "Not available"}...

## Your Mission

Analyze all outputs and create a comprehensive final package.

## Deliverables Required

1. **Executive Summary** - High-level overview of the complete SaaS business package (what was built, key features, value proposition, market opportunity)

2. **Project Structure** - Complete file/folder organization (directory tree showing where all deliverables are located)

3. **Documentation Package** - Comprehensive docs:
   - README.md (project overview, setup, usage)
   - SETUP.md (development environment setup)
   - API_DOCUMENTATION.md (API endpoints, examples)
   - DEPLOYMENT.md (deployment guide)
   - CONTRIBUTING.md (contribution guidelines)

4. **Deployment Checklist** - Step-by-step deployment guide:
   - Pre-deployment checks
   - Deployment steps
   - Post-deployment verification
   - Rollback procedures

5. **Quality Assurance Checklist** - QA steps before launch:
   - Functional testing checklist
   - Security audit checklist
   - Performance testing checklist
   - User acceptance testing (UAT) steps

6. **Handoff Materials** - Materials for user:
   - Quick start guide
   - Common tasks guide
   - Troubleshooting guide
   - FAQ

7. **Cost Summary** - Total costs from all agents:
   - Token usage per agent
   - Cost per agent
   - Total tokens and cost
   - Cost breakdown chart

8. **Timeline Summary** - Timeline and milestones:
   - Agent execution timeline
   - Key milestones achieved
   - Total time invested

9. **Deliverables Manifest** - Complete checklist:
   - Product requirements (PRD, personas, stories)
   - Technical architecture (database, APIs, infrastructure)
   - Code deliverables (backend, frontend, tests)
   - Design deliverables (UI components, design system)
   - Quality deliverables (test suite, bug reports)
   - Security deliverables (audit report, compliance)
   - DevOps deliverables (Docker, CI/CD, deployment configs)
   - Marketing deliverables (landing page, SEO, email sequences)
   - Business deliverables (business model, financial projections)

10. **What's Next Roadmap** - Recommendations:
    - Immediate next steps (0-30 days)
    - Short-term roadmap (1-3 months)
    - Long-term roadmap (3-12 months)
    - Key metrics to track
    - Success criteria

## Output Format

Return your response as a JSON object with these keys:
- executive_summary
- project_structure
- documentation_package
- deployment_checklist
- quality_assurance_checklist
- handoff_materials
- cost_summary
- timeline_summary
- deliverables_manifest
- whats_next_roadmap
- total_tokens_used (estimate)
- total_cost_usd (estimate)

Be comprehensive, actionable, and professional. This is the final deliverable.
"""

        # Update progress
        execution.current_task = "Calling Claude Sonnet 4.5 for final orchestration"
        execution.progress = 40
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
                temperature=0.3,  # Lower for precise, structured output
                max_tokens=12000
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
        execution.current_task = "Parsing final package deliverables"
        execution.progress = 80
        try:
            db.commit()
        except Exception:
            db.rollback()

        # Parse response
        result = self._parse_orchestration_response(content)

        # Update progress
        execution.current_task = "Finalizing complete SaaS business package"
        execution.progress = 95
        try:
            db.commit()
        except Exception:
            db.rollback()

        return {
            **result,
            "tokens_used": tokens_used,
            "cost_usd": round(cost_usd, 4)
        }

    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt for Platform Orchestrator agent"""
        return """You are a **Senior Platform Orchestrator** - The FINAL agent in the DARKAGENTS AI Product Factory.

# Your Mission

You are responsible for collecting outputs from 9 specialized agents and assembling them into a complete, production-ready SaaS business package that can be delivered to the user.

# Your Expertise

## Core Competencies
- Project orchestration and final assembly
- Documentation creation (README, setup guides, API docs)
- Quality assurance and deployment checklists
- User handoff and knowledge transfer
- Cost/timeline summarization
- Deliverable packaging and organization
- Next-step roadmap creation

## The 9 Agents You Orchestrate

1. **Product Manager** - PRD, user personas, user stories, success metrics
2. **System Architect** - Database schema, API specs, tech stack, infrastructure plan
3. **Polyglot Developer** - Full-stack production code (backend, frontend, tests)
4. **UI/UX Designer** - Design system, polished UI components, animations
5. **QA Engineer** - Test suite (unit, integration, E2E), bug reports
6. **Security Specialist** - OWASP audit, compliance checklist, security fixes
7. **DevOps Engineer** - Docker, CI/CD, deployment configs, monitoring
8. **Growth Marketer** - GTM strategy, landing page copy, SEO, email sequences
9. **Business Strategist** - Business model, financial projections, funding strategy

## Your Workflow

1. **Collect & Validate**
   - Gather outputs from all 9 agents
   - Validate completeness and quality
   - Identify any gaps or missing pieces

2. **Analyze & Synthesize**
   - Understand how all pieces fit together
   - Identify dependencies and connections
   - Create holistic view of the deliverable

3. **Document Everything**
   - Write comprehensive README
   - Create setup and deployment guides
   - Document API endpoints
   - Write troubleshooting guides

4. **Create Checklists**
   - Deployment checklist (step-by-step)
   - QA checklist (pre-launch verification)
   - Security checklist (OWASP, compliance)
   - Performance checklist (load testing, optimization)

5. **Organize Deliverables**
   - Create clear file/folder structure
   - Organize all outputs logically
   - Generate deliverables manifest
   - Package for easy handoff

6. **Summarize Costs & Timeline**
   - Calculate total tokens used
   - Calculate total costs
   - Estimate timeline for implementation
   - Identify key milestones

7. **Plan Next Steps**
   - Recommend immediate actions (0-30 days)
   - Outline short-term roadmap (1-3 months)
   - Define long-term roadmap (3-12 months)
   - Set success metrics to track

## Output Requirements

**IMPORTANT:** Return your orchestration as a well-structured JSON object with these exact keys:

```json
{
  "executive_summary": "High-level overview of complete SaaS business package",
  "project_structure": "Complete directory tree with all files and folders",
  "documentation_package": "README, SETUP, API_DOCS, DEPLOYMENT, CONTRIBUTING guides",
  "deployment_checklist": "Step-by-step deployment guide with verification",
  "quality_assurance_checklist": "Pre-launch QA steps (functional, security, performance)",
  "handoff_materials": "Quick start, common tasks, troubleshooting, FAQ",
  "cost_summary": "Token usage and costs per agent with total",
  "timeline_summary": "Timeline, milestones, time invested",
  "deliverables_manifest": "Complete checklist of all deliverables from all 9 agents",
  "whats_next_roadmap": "0-30 days, 1-3 months, 3-12 months with metrics",
  "total_tokens_used": 50000,
  "total_cost_usd": 0.75
}
```

## Best Practices

### Executive Summary
- Concise (200-300 words)
- Highlight key value proposition
- Mention technology stack
- Emphasize production-readiness
- Include market opportunity

### Project Structure
- Use standard directory conventions
- Separate backend, frontend, docs, tests
- Include configuration files (.env.example)
- Show deployment configs location

### Documentation Package
- README: Overview, setup, usage, contributing
- SETUP: Development environment setup (step-by-step)
- API_DOCS: All endpoints with examples and authentication
- DEPLOYMENT: Production deployment guide
- CONTRIBUTING: Contribution guidelines

### Deployment Checklist
- Pre-deployment (environment variables, database migrations)
- Deployment steps (build, test, deploy)
- Post-deployment verification (health checks, smoke tests)
- Rollback procedures (if deployment fails)

### QA Checklist
- Functional testing (all features work)
- Security testing (OWASP Top 10, auth, permissions)
- Performance testing (load tests, response times)
- Browser compatibility (Chrome, Firefox, Safari)
- Mobile responsiveness

### Cost Summary
- Show per-agent breakdown
- Calculate totals
- Compare to manual development costs
- Highlight ROI (time saved, cost saved)

### What's Next Roadmap
- Immediate (0-30 days): Launch MVP, gather feedback, fix critical bugs
- Short-term (1-3 months): Iterate on feedback, add features, grow users
- Long-term (3-12 months): Scale infrastructure, expand features, optimize unit economics

Be comprehensive, professional, and actionable. This is the FINAL deliverable.
"""

    def _parse_orchestration_response(self, content: str) -> Dict[str, Any]:
        """
        Parse Claude's response into structured orchestration package

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
            "project_structure": self._extract_section(content, ["project_structure", "project structure", "directory tree"]),
            "documentation_package": self._extract_section(content, ["documentation_package", "documentation", "docs"]),
            "deployment_checklist": self._extract_section(content, ["deployment_checklist", "deployment checklist", "deploy"]),
            "quality_assurance_checklist": self._extract_section(content, ["quality_assurance_checklist", "qa checklist", "testing"]),
            "handoff_materials": self._extract_section(content, ["handoff_materials", "handoff", "user guide"]),
            "cost_summary": self._extract_section(content, ["cost_summary", "cost summary", "costs"]),
            "timeline_summary": self._extract_section(content, ["timeline_summary", "timeline", "milestones"]),
            "deliverables_manifest": self._extract_section(content, ["deliverables_manifest", "deliverables", "manifest"]),
            "whats_next_roadmap": self._extract_section(content, ["whats_next_roadmap", "what's next", "roadmap"]),
            "total_tokens_used": 50000,  # Estimate
            "total_cost_usd": 0.75  # Estimate
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

"""
Agent 02: System Architect Agent
=================================

The System Architect Agent is a senior technical architect that designs
complete system architectures for SaaS applications.

Input: PRD from Product Manager Agent
Output: Complete technical architecture document including:
  - Database schema (SQLAlchemy models)
  - API specifications (REST endpoints)
  - Tech stack recommendations
  - Infrastructure plan
  - Cost estimates
  - Security architecture
  - Scalability plan

Tech Stack (Standard):
  - Backend: FastAPI + SQLAlchemy + PostgreSQL
  - Frontend: Next.js 14 + TypeScript + Tailwind CSS
  - Deployment: Vercel (frontend) + Railway (backend)
  - Auth: JWT with refresh tokens
  - Cache: Redis (optional)
  - File Storage: AWS S3 or Cloudflare R2
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import structlog

from backend.services.claude_service import claude_service
from backend.models import Project, AgentExecution

logger = structlog.get_logger(__name__)


class SystemArchitectAgent:
    """
    Agent 02: System Architect

    Senior technical architect with 15+ years enterprise experience.
    Designs production-ready, scalable, secure system architectures.
    """

    def __init__(self):
        self.agent_name = "system_architect"
        self.agent_display_name = "System Architect Agent"
        self.agent_description = "Senior technical architect - Designs complete system architecture"
        self.model = "anthropic/claude-sonnet-4.5"
        self.temperature = 0.4  # Balanced - creative architecture but structured output
        self.max_tokens = 12000  # Large output for comprehensive architecture docs

    def execute(self, project_id: int, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Execute the System Architect Agent

        Args:
            project_id: ID of the project
            input_data: Must contain 'prd' (from PM Agent) or 'requirements'
            db: Database session

        Returns:
            Architecture document with database schema, API specs, infrastructure plan
        """
        try:
            logger.info(
                "system_architect_agent.execute.start",
                project_id=project_id,
                input_data=input_data
            )

            # Create agent execution record
            execution = AgentExecution(
                project_id=project_id,
                agent_name=self.agent_name,
                agent_display_name=self.agent_display_name,
                status="running",
                started_at=datetime.utcnow()
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)

            # Get PRD from input (either from PM Agent or direct requirements)
            prd = input_data.get("prd") or input_data.get("requirements", "")
            if not prd:
                raise ValueError("Missing 'prd' or 'requirements' in input_data")

            # Optional: Get target users and business model for architecture decisions
            target_users = input_data.get("target_users", "General users")
            expected_scale = input_data.get("expected_scale", "1K-10K users")

            # Generate architecture
            logger.info("system_architect_agent.generating_architecture")
            architecture = self._generate_architecture(
                prd=prd,
                target_users=target_users,
                expected_scale=expected_scale,
                execution=execution,
                db=db
            )

            # Update execution record
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.output = architecture["content"]
            execution.tokens_used = architecture["tokens_used"]
            execution.cost_usd = architecture["cost_usd"]
            db.commit()

            logger.info(
                "system_architect_agent.execute.complete",
                execution_id=execution.id,
                tokens_used=architecture["tokens_used"],
                cost_usd=architecture["cost_usd"]
            )

            return {
                "success": True,
                "execution_id": execution.id,
                "agent_name": self.agent_name,
                "architecture": architecture["content"],
                "tokens_used": architecture["tokens_used"],
                "cost_usd": architecture["cost_usd"],
                "structured_output": architecture.get("structured_output", {}),
            }

        except Exception as e:
            logger.error(
                "system_architect_agent.execute.error",
                error=str(e),
                project_id=project_id
            )

            # Update execution record with error
            if 'execution' in locals():
                execution.status = "failed"
                execution.error_message = str(e)
                execution.completed_at = datetime.utcnow()
                db.commit()

            return {
                "success": False,
                "error": str(e),
                "agent_name": self.agent_name
            }

    def _generate_architecture(
        self,
        prd: str,
        target_users: str,
        expected_scale: str,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Generate complete system architecture using Claude

        Returns:
            {
                "content": "Full architecture document markdown",
                "tokens_used": 12500,
                "cost_usd": 0.085,
                "structured_output": {
                    "database_schema": {...},
                    "api_endpoints": [...],
                    "tech_stack": {...},
                    "infrastructure": {...}
                }
            }
        """

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(prd, target_users, expected_scale)

        # Call Claude API
        response = claude_service.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        # Extract structured data from response (if possible)
        structured_output = self._extract_structured_data(response["content"])

        return {
            "content": response["content"],
            "tokens_used": response["tokens_used"],
            "cost_usd": response["cost_usd"],
            "structured_output": structured_output
        }

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the Architect Agent"""

        return """You are the SYSTEM ARCHITECT AGENT - a senior technical architect with 15+ years of enterprise experience in the DARKAGENTS platform.

🎯 YOUR ROLE:
You design complete, production-ready system architectures for SaaS applications. Your architectures are:
- Scalable (handle 1K to 1M+ users)
- Secure (OWASP Top 10 compliant)
- Cost-effective (optimized infrastructure costs)
- Maintainable (clean separation of concerns)
- Modern (latest best practices)

📋 YOUR DELIVERABLES:
You must produce a comprehensive architecture document that includes:

1. **Executive Summary**
   - High-level architecture overview
   - Key technical decisions and rationale
   - Estimated infrastructure costs

2. **Database Schema**
   - Complete SQLAlchemy models (Python code)
   - Table relationships with foreign keys
   - Indexes for performance
   - Migration strategy

3. **API Specifications**
   - REST endpoint definitions
   - Request/response schemas (Pydantic models)
   - Authentication/authorization flow
   - Rate limiting strategy

4. **Tech Stack**
   - Backend: FastAPI + SQLAlchemy + PostgreSQL
   - Frontend: Next.js 14 + TypeScript + Tailwind CSS
   - Auth: JWT with refresh tokens
   - Cache: Redis (if needed for scale)
   - File Storage: AWS S3 or Cloudflare R2
   - Deployment: Vercel (frontend) + Railway (backend)

5. **Infrastructure Plan**
   - Deployment architecture diagram (ASCII/markdown)
   - Environment setup (dev, staging, prod)
   - CI/CD pipeline (GitHub Actions)
   - Monitoring & logging strategy

6. **Security Architecture**
   - Authentication & authorization
   - Data encryption (at rest & in transit)
   - API security (rate limiting, CORS, CSP)
   - Secret management (environment variables)
   - OWASP Top 10 mitigations

7. **Scalability Plan**
   - Horizontal scaling strategy
   - Database optimization (indexes, query optimization)
   - Caching strategy (Redis, CDN)
   - Load balancing
   - Cost projections (1K, 10K, 100K, 1M users)

8. **Cost Estimates**
   - Infrastructure costs per tier
   - API/service costs (if applicable)
   - Total monthly operating costs

🔥 CRITICAL FORMATTING RULES:

1. **Database Schema** - Provide complete SQLAlchemy models:
```python
# models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")
```

2. **API Specifications** - Provide complete endpoint definitions:
```markdown
### POST /api/auth/register
**Description:** Register new user
**Request Body:**
{
  "email": "user@example.com",
  "password": "secure_password"
}
**Response (201):**
{
  "id": 1,
  "email": "user@example.com",
  "access_token": "eyJ...",
  "refresh_token": "eyJ..."
}
**Errors:**
- 400: Invalid email format
- 409: Email already registered
```

3. **Architecture Diagrams** - Use ASCII/markdown:
```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Next.js   │─────▶│   FastAPI    │─────▶│ PostgreSQL  │
│  (Vercel)   │      │  (Railway)   │      │  (Railway)  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │    Redis    │
                     │   (Cache)   │
                     └─────────────┘
```

4. **Cost Estimates** - Provide detailed breakdown:
```markdown
### Monthly Infrastructure Costs

**1K Users:**
- Railway (backend + database): $20/month
- Vercel (frontend): $0/month (free tier)
- Total: $20/month

**10K Users:**
- Railway (backend + database): $50/month
- Vercel (frontend): $0/month (hobby tier)
- Redis (Upstash): $10/month
- Total: $60/month

**100K Users:**
- Railway (backend + database): $200/month
- Vercel (frontend): $20/month (pro tier)
- Redis (Upstash): $30/month
- AWS S3 (file storage): $20/month
- Total: $270/month
```

💡 BEST PRACTICES:

1. **Always use PostgreSQL** for relational data (users, subscriptions, etc.)
2. **Always use JWT** for authentication (access + refresh tokens)
3. **Always add indexes** on foreign keys and frequently queried fields
4. **Always plan for caching** (Redis) if > 10K users expected
5. **Always use environment variables** for secrets (never hardcode)
6. **Always plan CORS** properly for Next.js ↔ FastAPI communication
7. **Always include rate limiting** to prevent API abuse
8. **Always design for horizontal scaling** (stateless backend)

🎯 OUTPUT FORMAT:

Your response must be a comprehensive markdown document with all 8 sections above.
Use proper headings, code blocks, and formatting.
Be specific and detailed - this will be handed to the Polyglot Agent to implement.

Remember: Your architecture will directly inform the code generation. Be precise, complete, and production-ready.
"""

    def _build_user_prompt(self, prd: str, target_users: str, expected_scale: str) -> str:
        """Build the user prompt with PRD and requirements"""

        return f"""Design a complete system architecture for the following SaaS application.

📄 PRODUCT REQUIREMENTS DOCUMENT:
{prd}

👥 TARGET USERS:
{target_users}

📈 EXPECTED SCALE:
{expected_scale}

🎯 YOUR TASK:

Design a complete, production-ready system architecture that includes:

1. Executive Summary
2. Database Schema (SQLAlchemy models)
3. API Specifications (REST endpoints with request/response schemas)
4. Tech Stack (FastAPI + Next.js + PostgreSQL + Railway + Vercel)
5. Infrastructure Plan (deployment architecture + CI/CD)
6. Security Architecture (auth + encryption + OWASP mitigations)
7. Scalability Plan (caching + load balancing + cost projections)
8. Cost Estimates (1K, 10K, 100K, 1M users)

Make sure your architecture is:
- ✅ Scalable (handles expected growth)
- ✅ Secure (OWASP Top 10 compliant)
- ✅ Cost-effective (optimized for budget)
- ✅ Maintainable (clean architecture)
- ✅ Production-ready (no shortcuts or placeholders)

Provide complete code for database models and detailed API specifications.

Begin your architecture document now:
"""

    def _extract_structured_data(self, architecture_doc: str) -> Dict[str, Any]:
        """
        Extract structured data from architecture document

        This attempts to parse out:
        - Database tables list
        - API endpoints list
        - Tech stack components
        - Cost estimates

        Returns empty dict if parsing fails.
        """

        structured = {
            "database_tables": [],
            "api_endpoints": [],
            "tech_stack": {},
            "cost_estimates": {}
        }

        try:
            # Extract database table names (look for class definitions)
            import re
            table_pattern = r'class\s+(\w+)\(Base\):'
            tables = re.findall(table_pattern, architecture_doc)
            structured["database_tables"] = tables

            # Extract API endpoints (look for HTTP method + path)
            endpoint_pattern = r'###?\s+(GET|POST|PUT|DELETE|PATCH)\s+(/[\w\-/{}]+)'
            endpoints = re.findall(endpoint_pattern, architecture_doc)
            structured["api_endpoints"] = [{"method": m, "path": p} for m, p in endpoints]

            # Extract cost estimates (look for dollar amounts)
            cost_pattern = r'\$(\d+(?:,\d+)?)/month'
            costs = re.findall(cost_pattern, architecture_doc)
            if costs:
                structured["cost_estimates"]["extracted_values"] = costs

            logger.info(
                "system_architect_agent.extracted_structured_data",
                tables_count=len(structured["database_tables"]),
                endpoints_count=len(structured["api_endpoints"])
            )

        except Exception as e:
            logger.warning(
                "system_architect_agent.extract_structured_data.error",
                error=str(e)
            )
            # Return empty structured data on error
            pass

        return structured

    def validate_architecture(self, architecture_doc: str) -> Dict[str, Any]:
        """
        Validate that architecture document contains required sections

        Returns:
            {
                "valid": True/False,
                "missing_sections": [...],
                "completeness_score": 0.0-1.0
            }
        """

        required_sections = [
            "Executive Summary",
            "Database Schema",
            "API Specifications",
            "Tech Stack",
            "Infrastructure Plan",
            "Security Architecture",
            "Scalability Plan",
            "Cost Estimates"
        ]

        missing_sections = []
        for section in required_sections:
            # Case-insensitive check
            if section.lower() not in architecture_doc.lower():
                missing_sections.append(section)

        completeness_score = (len(required_sections) - len(missing_sections)) / len(required_sections)

        return {
            "valid": len(missing_sections) == 0,
            "missing_sections": missing_sections,
            "completeness_score": completeness_score
        }

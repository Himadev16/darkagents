"""
Agent Execution API Routes
Trigger and manage AI agent execution
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db, Project
from backend.database.models import User
from backend.api.dependencies import get_current_active_user
from backend.agents import ProductManagerAgent, PolyglotAgent, SystemArchitectAgent, UIUXDesignerAgent, QAEngineerAgent, SecuritySpecialistAgent, DevOpsEngineerAgent, GrowthMarketerAgent, BusinessStrategistAgent
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/api/agents", tags=["Agents"])


class AgentExecutionRequest(BaseModel):
    """Request to execute an agent"""
    project_id: int
    agent_name: str  # "product_manager", "system_architect", etc.
    input_data: dict = {}


class AgentExecutionResponse(BaseModel):
    """Response after triggering agent execution"""
    message: str
    project_id: int
    agent_name: str
    execution_id: int


def execute_agent_async(
    agent_name: str,
    project_id: int,
    input_data: dict,
    db: Session
):
    """
    Execute an agent asynchronously in the background

    This function runs in a background task so the API response is immediate
    """
    try:
        logger.info(
            "agent_execution_started",
            agent_name=agent_name,
            project_id=project_id
        )

        # Get the appropriate agent
        agent = None
        if agent_name == "product_manager":
            agent = ProductManagerAgent()
        elif agent_name == "system_architect":
            agent = SystemArchitectAgent()
        elif agent_name == "polyglot_agent":
            agent = PolyglotAgent()
        elif agent_name == "ui_ux_designer":
            agent = UIUXDesignerAgent()
        elif agent_name == "qa_engineer":
            agent = QAEngineerAgent()
        elif agent_name == "security_specialist":
            agent = SecuritySpecialistAgent()
        elif agent_name == "devops_engineer":
            agent = DevOpsEngineerAgent()
        elif agent_name == "growth_marketer":
            agent = GrowthMarketerAgent()
        elif agent_name == "business_strategist":
            agent = BusinessStrategistAgent()
        # Add more agents here as we implement them
        else:
            logger.error("unknown_agent", agent_name=agent_name)
            return

        # Execute the agent
        result = agent.execute(project_id, input_data, db)

        logger.info(
            "agent_execution_completed",
            agent_name=agent_name,
            project_id=project_id,
            result_keys=list(result.keys())
        )

    except Exception as e:
        logger.error(
            "agent_execution_failed",
            agent_name=agent_name,
            project_id=project_id,
            error=str(e)
        )


@router.post("/execute", response_model=AgentExecutionResponse)
async def execute_agent(
    request: AgentExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Trigger an AI agent to execute

    This endpoint:
    1. Validates the project belongs to the user
    2. Starts the agent in a background task
    3. Returns immediately with execution info
    4. Agent broadcasts progress via WebSocket

    Usage:
    ```bash
    curl -X POST http://localhost:8000/api/agents/execute \
      -H "Authorization: Bearer YOUR_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "project_id": 1,
        "agent_name": "product_manager",
        "input_data": {}
      }'
    ```

    Then connect to WebSocket to watch real-time progress:
    ```js
    const ws = new WebSocket('ws://localhost:8000/ws/1');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'agent_status') {
            console.log(data.data);
        }
    };
    ```
    """
    # Verify project exists and belongs to user
    project = db.query(Project).filter(
        Project.id == request.project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    # Validate agent name
    valid_agents = [
        "product_manager",
        "system_architect",
        "polyglot_agent",
        "ui_ux_designer",
        "qa_engineer",
        "security_specialist",
        "devops_engineer",
        "growth_marketer",
        "business_strategist",
        # Add more as we implement them
        # "platform_orchestrator",
        # etc.
    ]

    if request.agent_name not in valid_agents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid agent name. Valid agents: {', '.join(valid_agents)}"
        )

    # Create a new database session for the background task
    # (can't share sessions across threads)
    from backend.database import SessionLocal

    # Schedule agent execution in background
    background_tasks.add_task(
        execute_agent_async,
        agent_name=request.agent_name,
        project_id=request.project_id,
        input_data=request.input_data,
        db=SessionLocal()  # New session for background task
    )

    logger.info(
        "agent_execution_triggered",
        agent_name=request.agent_name,
        project_id=request.project_id,
        user_id=current_user.id
    )

    return {
        "message": f"{request.agent_name} execution started. Connect to WebSocket /ws/{request.project_id} for real-time updates.",
        "project_id": request.project_id,
        "agent_name": request.agent_name,
        "execution_id": 0  # Placeholder - will be created by agent
    }


@router.get("/available")
async def list_available_agents():
    """
    List all available agents

    Returns info about each agent including name, role, and status
    """
    agents = [
        {
            "name": "product_manager",
            "display_name": "Product Manager",
            "role": "Transform user ideas into detailed product requirements",
            "status": "available",
            "deliverables": [
                "Product Requirements Document (PRD)",
                "User Personas",
                "User Stories",
                "Feature Prioritization Matrix",
                "Success Metrics",
                "Competitive Analysis"
            ]
        },
        {
            "name": "system_architect",
            "display_name": "System Architect",
            "role": "Senior technical architect - Designs complete system architecture",
            "status": "available",
            "deliverables": [
                "Executive Summary",
                "Database Schema (SQLAlchemy models)",
                "API Specifications (REST endpoints)",
                "Tech Stack Recommendations",
                "Infrastructure Plan (CI/CD, deployment)",
                "Security Architecture (OWASP, encryption)",
                "Scalability Plan (caching, load balancing)",
                "Cost Estimates (1K to 1M+ users)"
            ],
            "tech_stack": {
                "backend": "FastAPI + SQLAlchemy + PostgreSQL",
                "frontend": "Next.js 14 + TypeScript + Tailwind CSS",
                "deployment": "Vercel (frontend) + Railway (backend)",
                "auth": "JWT with refresh tokens",
                "cache": "Redis (optional)",
                "storage": "AWS S3 or Cloudflare R2"
            }
        },
        {
            "name": "polyglot_agent",
            "display_name": "Polyglot Agent",
            "role": "Elite Multi-Language Software Engineer & Code Architect",
            "status": "available",
            "capabilities": [
                "Multi-language code generation (20+ languages)",
                "Code review and refactoring",
                "Debugging and problem-solving",
                "Test generation (unit, integration, e2e)",
                "Performance optimization",
                "Security analysis",
                "Cross-language code translation",
                "Architecture recommendations"
            ],
            "languages": [
                "Python", "JavaScript", "TypeScript", "Go", "Rust", "Java",
                "C++", "C#", "Ruby", "PHP", "Swift", "Kotlin", "Dart",
                "Scala", "Elixir", "Haskell", "Clojure", "Julia", "Lua", "R"
            ]
        },
        {
            "name": "ui_ux_designer",
            "display_name": "UI/UX Designer",
            "role": "Senior product designer - Polishes UI with professional design and animations",
            "status": "available",
            "deliverables": [
                "Design System (colors, typography, spacing, shadows)",
                "Enhanced Component Design (buttons, forms, cards)",
                "Animations & Micro-interactions (transitions, loading states)",
                "Responsive Design Improvements (mobile-first)",
                "Accessibility Enhancements (WCAG 2.1 AA compliance)",
                "Modern UI Patterns (gradients, glassmorphism)"
            ],
            "specialties": [
                "Tailwind CSS optimization",
                "React/Next.js component design",
                "Accessible design (ARIA labels, keyboard navigation)",
                "Animation and micro-interactions",
                "Mobile-first responsive design",
                "Design systems and visual hierarchy"
            ],
            "input": "Frontend code from Polyglot Agent",
            "output": "Enhanced code with professional design"
        },
        {
            "name": "qa_engineer",
            "display_name": "QA Engineer",
            "role": "Senior QA engineer - Generates test suite and identifies bugs",
            "status": "available",
            "deliverables": [
                "Comprehensive Test Suite (unit, integration, E2E, performance)",
                "Bug Reports (severity levels, reproduction steps)",
                "Test Coverage Report (estimated %, untested paths)",
                "Quality Score (0-100 with breakdown)",
                "Testing Recommendations (priority fixes, gaps)"
            ],
            "test_types": [
                "Unit tests (pytest, Jest)",
                "Integration tests (API testing)",
                "E2E tests (Playwright, Cypress)",
                "Performance tests (load testing, benchmarks)",
                "Security tests (vulnerability detection)",
                "Edge case tests (null, empty, large inputs)"
            ],
            "bug_severity_levels": [
                "Critical (security, data loss, system crash)",
                "High (major functionality broken)",
                "Medium (minor functionality broken)",
                "Low (cosmetic issues, typos)"
            ],
            "input": "Complete codebase from Polyglot + Designer agents",
            "output": "Test suite + bug reports + quality score"
        },
        {
            "name": "security_specialist",
            "display_name": "Security Specialist",
            "role": "Senior security engineer - Performs security audit and compliance checking",
            "status": "available",
            "deliverables": [
                "OWASP Top 10 Vulnerability Scan",
                "Security Vulnerability Reports (severity levels, fixes)",
                "Compliance Checklist (GDPR, SOC2, HIPAA, PCI-DSS)",
                "Security Score (0-100)",
                "Penetration Testing Recommendations",
                "Remediation Roadmap (prioritized fixes)"
            ],
            "vulnerability_types": [
                "SQL Injection, XSS, CSRF",
                "Authentication bypass, broken access control",
                "Cryptographic failures, weak algorithms",
                "Security misconfiguration",
                "Sensitive data exposure",
                "API security issues"
            ],
            "compliance_standards": [
                "GDPR (General Data Protection Regulation)",
                "SOC2 (Security, Availability, Confidentiality)",
                "HIPAA (Healthcare data protection)",
                "PCI-DSS (Payment card data security)"
            ],
            "features": [
                "OWASP Top 10 detection",
                "CWE vulnerability classification",
                "Proof of concept exploits",
                "Fix recommendations with code examples",
                "Security scoring algorithm",
                "Compliance gap analysis",
                "Retry logic with exponential backoff",
                "Production-grade error handling"
            ],
            "input": "Complete codebase from Polyglot + Designer + QA agents",
            "output": "Security audit report + vulnerabilities + compliance status"
        },
        {
            "name": "devops_engineer",
            "display_name": "DevOps Engineer",
            "role": "Senior DevOps engineer - Generates deployment config and CI/CD pipelines",
            "status": "available",
            "deliverables": [
                "Docker Configuration (Dockerfile, docker-compose.yml)",
                "CI/CD Pipeline (GitHub Actions, GitLab CI, Jenkins)",
                "Deployment Configuration (Vercel, Railway, AWS, GCP)",
                "Environment Configuration (.env templates)",
                "Monitoring Setup (logging, alerts, health checks)",
                "Deployment Documentation (setup, rollback, troubleshooting)"
            ],
            "deployment_targets": [
                "Vercel (Next.js frontend)",
                "Railway (FastAPI backend + PostgreSQL)",
                "AWS (EC2, ECS, Lambda)",
                "GCP (Cloud Run, App Engine)",
                "Azure (App Service)",
                "DigitalOcean (Droplets, App Platform)"
            ],
            "ci_cd_platforms": [
                "GitHub Actions",
                "GitLab CI",
                "Jenkins",
                "CircleCI"
            ],
            "features": [
                "Multi-stage Docker builds",
                "Automated testing in CI/CD",
                "Health check endpoints",
                "Graceful shutdown handling",
                "Rolling deployments",
                "Rollback mechanisms",
                "Monitoring integration",
                "Retry logic with exponential backoff",
                "Production-grade error handling"
            ],
            "input": "Complete codebase + architecture from all previous agents",
            "output": "Deployment package + CI/CD pipeline + monitoring setup"
        },
        {
            "name": "growth_marketer",
            "display_name": "Growth Marketer",
            "role": "Senior growth marketer - Develops GTM strategy and marketing assets",
            "status": "available",
            "deliverables": [
                "Go-to-Market (GTM) Strategy",
                "Landing Page Copy (headlines, CTAs, sections)",
                "SEO Strategy (keywords, meta tags, content plan)",
                "Customer Acquisition Plan (channels, tactics, budget)",
                "Content Marketing Strategy (blog, tutorials, case studies)",
                "Email Marketing Sequences (onboarding, nurture, retention)",
                "Social Media Strategy (LinkedIn, Twitter/X, Product Hunt)",
                "Growth Experiments (A/B tests, funnel optimization)",
                "Pricing Page Optimization",
                "Metrics Dashboard (CAC, LTV, conversion rates)"
            ],
            "channels": [
                "SEO & Content Marketing",
                "Paid Advertising (Google, LinkedIn, Facebook)",
                "Social Media (LinkedIn, Twitter/X, Product Hunt)",
                "Email Marketing",
                "Referral & Viral Growth",
                "Community Building",
                "Partnerships & Integrations"
            ],
            "specialties": [
                "SaaS go-to-market strategy",
                "Conversion copywriting",
                "Growth experiment design",
                "Product-led growth (PLG)",
                "Customer acquisition optimization",
                "Retention and engagement",
                "Analytics and metrics (CAC, LTV, conversion rates)"
            ],
            "features": [
                "Benefit-driven copy for landing pages",
                "SEO-optimized content strategy",
                "Channel prioritization by ROI",
                "A/B test recommendations",
                "Email sequence templates",
                "Social media launch tactics",
                "Metrics dashboard with KPI targets",
                "Retry logic with exponential backoff",
                "Production-grade error handling"
            ],
            "input": "Product details from PM, Architect, Designer agents",
            "output": "Complete growth marketing package ready for execution"
        },
        {
            "name": "business_strategist",
            "display_name": "Business Strategist",
            "role": "Senior business strategist - Develops business model and financial strategy",
            "status": "available",
            "deliverables": [
                "Business Model Canvas (9 building blocks)",
                "Revenue Model (streams, tiers, 24-month projections)",
                "Pricing Strategy (analysis, psychology, competitive comparison)",
                "Competitive Analysis (SWOT, Porter's Five Forces, positioning)",
                "Financial Model (P&L, cash flow, burn rate, runway)",
                "Market Sizing (TAM, SAM, SOM with calculations)",
                "Unit Economics (CAC, LTV, payback period, margins)",
                "Funding Strategy (options, timeline, milestones)",
                "Growth Roadmap (12-month plan with quarterly milestones)",
                "Risk Analysis (top risks with mitigation strategies)"
            ],
            "frameworks": [
                "Business Model Canvas (9 blocks)",
                "Financial Metrics (ARR, MRR, CAC, LTV, burn rate, runway)",
                "Competitive Analysis (SWOT, Porter's Five Forces)",
                "Market Sizing (TAM/SAM/SOM methodology)",
                "Pricing Strategy (value-based, freemium, tiered, usage-based)",
                "Unit Economics (LTV:CAC ratio, payback period, gross margin)",
                "Funding Strategy (bootstrap, angel, seed, Series A)"
            ],
            "specialties": [
                "SaaS business model development",
                "Financial modeling and projections",
                "Unit economics optimization (CAC, LTV, margins)",
                "Competitive strategy and positioning",
                "Pricing strategy and psychology",
                "Market analysis and sizing",
                "Fundraising strategy and planning",
                "Risk assessment and mitigation"
            ],
            "features": [
                "24-month revenue projections (3 scenarios)",
                "Complete P&L and cash flow analysis",
                "Unit economics with formulas and targets",
                "Competitive positioning map",
                "Pricing tier recommendations",
                "Funding timeline with milestones",
                "12-month growth roadmap",
                "Risk analysis with mitigation plans",
                "Retry logic with exponential backoff",
                "Production-grade error handling"
            ],
            "input": "Product details, market info, financial assumptions from previous agents",
            "output": "Comprehensive business strategy package with financial models"
        },
        # Add more agents as we implement them
    ]

    return {
        "agents": agents,
        "total": len(agents)
    }

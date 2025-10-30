"""
Agent 07: DevOps Engineer Agent
=================================

The DevOps Engineer Agent is a senior DevOps engineer that generates deployment
configurations, CI/CD pipelines, and infrastructure as code.

Input: Complete codebase + architecture from previous agents
Output: Deployment package, including:
  - Docker configuration (Dockerfile, docker-compose.yml)
  - CI/CD pipeline (GitHub Actions, GitLab CI)
  - Deployment scripts (Vercel, Railway, AWS, GCP)
  - Environment configuration (.env templates)
  - Monitoring setup (logging, alerts, health checks)
  - Infrastructure as Code (Terraform, CloudFormation)

PRODUCTION-READY: Includes retry logic, error handling, validation, logging.
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
import structlog
import time

from backend.services.claude_service import claude_service
from backend.database.models import Project, AgentExecution

logger = structlog.get_logger(__name__)


class DevOpsEngineerAgent:
    """
    Agent 07: DevOps Engineer

    Senior DevOps engineer with 10+ years of experience in cloud infrastructure,
    CI/CD, containerization, and deployment automation.

    PRODUCTION-READY: Includes comprehensive error handling, retry logic, and validation.
    """

    def __init__(self):
        self.agent_name = "devops_engineer"
        self.agent_display_name = "DevOps Engineer"
        self.agent_description = "Senior DevOps engineer - Generates deployment config and CI/CD pipelines"
        self.model = "anthropic/claude-sonnet-4.5"
        self.temperature = 0.3  # Precise for configuration files
        self.max_tokens = 12000  # Comprehensive deployment configs
        self.max_retries = 3  # Retry failed API calls
        self.retry_delay = 2  # Seconds between retries

    def execute(self, project_id: int, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Execute the DevOps Engineer Agent with production-grade error handling

        Args:
            project_id: ID of the project
            input_data: Must contain 'codebase' and 'architecture'
            db: Database session

        Returns:
            Deployment configuration package with Docker, CI/CD, deployment scripts
        """
        execution = None

        try:
            # Validate input
            if not input_data:
                raise ValueError("input_data is required")

            logger.info(
                "devops_engineer_agent.execute.start",
                project_id=project_id,
                input_data_keys=list(input_data.keys())
            )

            # Create agent execution record with transaction
            try:
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

                logger.info(
                    "devops_engineer_agent.execution_created",
                    execution_id=execution.id
                )
            except Exception as db_error:
                db.rollback()
                logger.error(
                    "devops_engineer_agent.execution_creation_failed",
                    error=str(db_error)
                )
                raise

            # Get and validate inputs
            codebase = input_data.get("codebase", "")
            architecture = input_data.get("architecture", "")

            if not codebase or not isinstance(codebase, str):
                raise ValueError("Missing or invalid 'codebase' in input_data (must be non-empty string)")

            if len(codebase.strip()) < 10:
                raise ValueError("Codebase is too short (minimum 10 characters required)")

            # Get optional parameters with defaults
            deployment_targets = input_data.get("deployment_targets", ["vercel", "railway"])
            ci_cd_platform = input_data.get("ci_cd_platform", "github-actions")  # "github-actions", "gitlab-ci", "jenkins"
            include_monitoring = input_data.get("include_monitoring", True)
            include_docker = input_data.get("include_docker", True)

            # Validate deployment targets
            valid_targets = ["vercel", "railway", "heroku", "aws", "gcp", "azure", "digitalocean"]
            deployment_targets = [t for t in deployment_targets if t in valid_targets]
            if not deployment_targets:
                deployment_targets = ["vercel", "railway"]  # Default

            # Validate CI/CD platform
            valid_ci_cd = ["github-actions", "gitlab-ci", "jenkins", "circleci"]
            if ci_cd_platform not in valid_ci_cd:
                logger.warning(
                    "devops_engineer_agent.invalid_ci_cd_platform",
                    ci_cd_platform=ci_cd_platform,
                    valid_platforms=valid_ci_cd
                )
                ci_cd_platform = "github-actions"

            # Generate deployment configuration with retry logic
            logger.info("devops_engineer_agent.starting_deployment_config")
            deployment_results = self._generate_deployment_config_with_retry(
                codebase=codebase,
                architecture=architecture,
                deployment_targets=deployment_targets,
                ci_cd_platform=ci_cd_platform,
                include_monitoring=include_monitoring,
                include_docker=include_docker,
                execution=execution,
                db=db
            )

            # Update execution record with results
            try:
                execution.status = "completed"
                execution.completed_at = datetime.utcnow()
                execution.output = deployment_results["content"]
                execution.tokens_used = deployment_results["tokens_used"]
                execution.cost_usd = deployment_results["cost_usd"]
                db.commit()

                logger.info(
                    "devops_engineer_agent.execution_completed",
                    execution_id=execution.id,
                    tokens_used=deployment_results["tokens_used"],
                    cost_usd=deployment_results["cost_usd"],
                    config_files_count=len(deployment_results.get("config_files", []))
                )
            except Exception as db_error:
                db.rollback()
                logger.error(
                    "devops_engineer_agent.execution_update_failed",
                    error=str(db_error)
                )
                # Don't raise - we have the results, just failed to save them

            return {
                "success": True,
                "execution_id": execution.id,
                "agent_name": self.agent_name,
                "deployment_config": deployment_results["content"],
                "config_files": deployment_results.get("config_files", []),
                "deployment_targets": deployment_targets,
                "ci_cd_platform": ci_cd_platform,
                "tokens_used": deployment_results["tokens_used"],
                "cost_usd": deployment_results["cost_usd"],
            }

        except ValueError as ve:
            # Validation errors - don't retry
            logger.error(
                "devops_engineer_agent.validation_error",
                error=str(ve),
                project_id=project_id
            )

            if execution:
                try:
                    execution.status = "failed"
                    execution.error_message = f"Validation error: {str(ve)}"
                    execution.completed_at = datetime.utcnow()
                    db.commit()
                except:
                    db.rollback()

            return {
                "success": False,
                "error": f"Validation error: {str(ve)}",
                "error_type": "validation_error",
                "agent_name": self.agent_name
            }

        except Exception as e:
            # Unexpected errors
            logger.error(
                "devops_engineer_agent.execute.error",
                error=str(e),
                error_type=type(e).__name__,
                project_id=project_id
            )

            # Update execution record with error
            if execution:
                try:
                    execution.status = "failed"
                    execution.error_message = str(e)
                    execution.completed_at = datetime.utcnow()
                    db.commit()
                except:
                    db.rollback()

            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "agent_name": self.agent_name
            }

    def _generate_deployment_config_with_retry(
        self,
        codebase: str,
        architecture: str,
        deployment_targets: List[str],
        ci_cd_platform: str,
        include_monitoring: bool,
        include_docker: bool,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Generate deployment configuration with retry logic for API failures

        PRODUCTION-READY: Retries with exponential backoff on API failures
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "devops_engineer_agent.deployment_config_attempt",
                    attempt=attempt,
                    max_retries=self.max_retries
                )

                result = self._generate_deployment_config(
                    codebase=codebase,
                    architecture=architecture,
                    deployment_targets=deployment_targets,
                    ci_cd_platform=ci_cd_platform,
                    include_monitoring=include_monitoring,
                    include_docker=include_docker,
                    execution=execution,
                    db=db
                )

                logger.info(
                    "devops_engineer_agent.deployment_config_success",
                    attempt=attempt
                )

                return result

            except Exception as e:
                last_error = e
                logger.warning(
                    "devops_engineer_agent.deployment_config_attempt_failed",
                    attempt=attempt,
                    error=str(e),
                    error_type=type(e).__name__
                )

                # Don't retry on validation errors
                if isinstance(e, ValueError):
                    raise

                # If this was the last attempt, raise the error
                if attempt == self.max_retries:
                    logger.error(
                        "devops_engineer_agent.deployment_config_all_retries_failed",
                        max_retries=self.max_retries,
                        last_error=str(last_error)
                    )
                    raise

                # Wait before retrying (exponential backoff)
                wait_time = self.retry_delay * (2 ** (attempt - 1))
                logger.info(
                    "devops_engineer_agent.retry_wait",
                    wait_seconds=wait_time,
                    next_attempt=attempt + 1
                )
                time.sleep(wait_time)

        # Should never reach here, but just in case
        raise last_error if last_error else Exception("Deployment config generation failed after all retries")

    def _generate_deployment_config(
        self,
        codebase: str,
        architecture: str,
        deployment_targets: List[str],
        ci_cd_platform: str,
        include_monitoring: bool,
        include_docker: bool,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Generate comprehensive deployment configuration using Claude

        Returns:
            {
                "content": "Full deployment documentation markdown",
                "tokens_used": 12500,
                "cost_usd": 0.07,
                "config_files": [
                    {"name": "Dockerfile", "content": "..."},
                    {"name": "docker-compose.yml", "content": "..."},
                    {"name": ".github/workflows/deploy.yml", "content": "..."}
                ]
            }
        """

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            codebase,
            architecture,
            deployment_targets,
            ci_cd_platform,
            include_monitoring,
            include_docker
        )

        # Call Claude API (this may raise exceptions)
        response = claude_service.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        # Extract configuration files from response
        config_files = self._extract_config_files(response["content"])

        return {
            "content": response["content"],
            "tokens_used": response["tokens_used"],
            "cost_usd": response["cost_usd"],
            "config_files": config_files
        }

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the DevOps Engineer Agent"""

        return """You are the DEVOPS ENGINEER AGENT - a senior DevOps engineer with 10+ years of experience in cloud infrastructure, CI/CD, containerization, and deployment automation in the DARKAGENTS platform.

🎯 YOUR ROLE:
You generate production-ready deployment configurations, CI/CD pipelines, and infrastructure as code. You specialize in:
- Docker and containerization
- CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins)
- Cloud deployment (Vercel, Railway, AWS, GCP, Azure)
- Infrastructure as Code (Terraform, CloudFormation)
- Monitoring and logging (Datadog, New Relic, Sentry)
- Environment configuration and secrets management
- Auto-scaling and load balancing
- Health checks and graceful shutdowns

🚀 YOUR EXPERTISE:
- Docker (multi-stage builds, layer caching, security)
- CI/CD (automated testing, build, deploy)
- Cloud Platforms (Vercel, Railway, Heroku, AWS, GCP, Azure)
- Monitoring (logs, metrics, alerts, APM)
- Security (secrets management, least privilege, network isolation)
- Performance (CDN, caching, compression, auto-scaling)
- Reliability (health checks, rolling deployments, rollback)

📋 YOUR DELIVERABLES:
You must produce a comprehensive deployment package with:

1. **Docker Configuration**
   - Dockerfile (multi-stage build for production)
   - docker-compose.yml (local development + production)
   - .dockerignore (optimize image size)
   - Health check configuration
   - Security best practices (non-root user, minimal base image)

2. **CI/CD Pipeline**
   - GitHub Actions workflow (.github/workflows/deploy.yml)
   - Or GitLab CI (.gitlab-ci.yml)
   - Or Jenkins pipeline (Jenkinsfile)
   - Automated testing (unit, integration, E2E)
   - Build and push Docker images
   - Deploy to target platforms
   - Rollback on failure

3. **Deployment Configuration**
   - Vercel configuration (vercel.json)
   - Railway configuration (railway.json)
   - AWS/GCP deployment scripts
   - Environment variable templates (.env.example)
   - Database migration scripts
   - Nginx configuration (if needed)

4. **Monitoring Setup**
   - Logging configuration (structured logs)
   - Health check endpoints
   - APM integration (Datadog, New Relic)
   - Error tracking (Sentry)
   - Metrics collection (Prometheus)
   - Alert configuration

5. **Infrastructure as Code (Optional)**
   - Terraform configuration
   - AWS CloudFormation templates
   - Kubernetes manifests (if needed)

6. **Deployment Documentation**
   - Step-by-step deployment guide
   - Environment setup instructions
   - Rollback procedures
   - Troubleshooting guide
   - Cost estimates

🔥 CRITICAL DEVOPS RULES:

1. **Dockerfile Best Practices:**
```dockerfile
# Multi-stage build for Python FastAPI
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies in separate layer for caching
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user for security
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

# Set PATH and switch to non-root user
ENV PATH=/home/appuser/.local/bin:$PATH
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. **GitHub Actions CI/CD:**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest

      - name: Run tests
        run: pytest tests/

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Deploy to Railway
        run: |
          curl -X POST ${{ secrets.RAILWAY_WEBHOOK_URL }}
```

3. **Docker Compose for Development:**
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/appdb
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=appdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

4. **Vercel Configuration:**
```json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    }
  ],
  "env": {
    "NEXT_PUBLIC_API_URL": "@api_url"
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

5. **Environment Variables Template:**
```bash
# .env.example
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/appdb

# Redis
REDIS_URL=redis://localhost:6379

# API Keys (DO NOT COMMIT ACTUAL VALUES)
OPENROUTER_API_KEY=your_api_key_here
SECRET_KEY=generate_random_secret_key

# Environment
NODE_ENV=production
DEBUG=false

# Monitoring
SENTRY_DSN=your_sentry_dsn
DATADOG_API_KEY=your_datadog_key
```

6. **Health Check Endpoint:**
```python
# backend/api/routes/health.py
from fastapi import APIRouter
from sqlalchemy import text

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    # Check database connection
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Check Redis connection
    try:
        redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
        "database": db_status,
        "redis": redis_status,
        "version": "1.0.0"
    }
```

💡 DEPLOYMENT BEST PRACTICES:

**Security:**
- Use non-root user in Docker
- Scan images for vulnerabilities (Trivy, Snyk)
- Use secrets management (never commit secrets)
- Enable HTTPS only
- Implement rate limiting
- Use least privilege access

**Performance:**
- Use multi-stage Docker builds
- Enable layer caching
- Use CDN for static assets
- Enable compression (gzip, brotli)
- Implement caching (Redis, CDN)
- Use connection pooling

**Reliability:**
- Health checks (liveness, readiness)
- Graceful shutdown
- Rolling deployments
- Auto-scaling
- Database migrations before deploy
- Rollback mechanism

**Monitoring:**
- Structured logging (JSON)
- APM integration
- Error tracking
- Metrics collection
- Alert thresholds
- Dashboard creation

🎯 OUTPUT FORMAT:

Return a comprehensive deployment package with:

1. Complete Docker configuration (Dockerfile, docker-compose.yml, .dockerignore)
2. CI/CD pipeline (GitHub Actions, GitLab CI, or Jenkins)
3. Deployment configuration for each target platform
4. Environment variable templates
5. Health check implementation
6. Monitoring setup
7. Step-by-step deployment guide
8. Troubleshooting guide

Use proper code blocks with filenames:
```dockerfile
# Dockerfile
...
```

```yaml
# .github/workflows/deploy.yml
...
```

Be production-ready, secure, and scalable. Include all necessary configuration files and documentation.

Remember: Your deployment configuration will be used in production. Make it secure, reliable, and well-documented.
"""

    def _build_user_prompt(
        self,
        codebase: str,
        architecture: str,
        deployment_targets: List[str],
        ci_cd_platform: str,
        include_monitoring: bool,
        include_docker: bool
    ) -> str:
        """Build the user prompt with codebase and requirements"""

        targets_str = ", ".join(deployment_targets)
        monitoring_str = "Include monitoring setup" if include_monitoring else "Skip monitoring setup"
        docker_str = "Include Docker configuration" if include_docker else "Skip Docker configuration"

        architecture_section = f"""

SYSTEM ARCHITECTURE:
{architecture}
""" if architecture else ""

        return f"""Generate a comprehensive deployment package for the following application.

🚀 DEPLOYMENT REQUIREMENTS:
- Target Platforms: {targets_str}
- CI/CD Platform: {ci_cd_platform}
- {docker_str}
- {monitoring_str}

🎯 YOUR TASK:

Generate production-ready deployment configuration including:

1. **Docker Configuration** (if enabled):
   - Dockerfile with multi-stage build
   - docker-compose.yml for local development
   - .dockerignore
   - Health checks
   - Security best practices (non-root user)

2. **CI/CD Pipeline** ({ci_cd_platform}):
   - Automated testing
   - Build and push Docker images
   - Deploy to {targets_str}
   - Rollback on failure

3. **Deployment Configuration**:
   - Configuration files for: {targets_str}
   - Environment variable templates (.env.example)
   - Database migration scripts
   - Nginx config (if needed)

4. **Monitoring Setup** (if enabled):
   - Structured logging
   - Health check endpoints
   - Error tracking integration
   - Metrics collection

5. **Documentation**:
   - Step-by-step deployment guide
   - Environment setup
   - Rollback procedures
   - Troubleshooting

CODEBASE:
{codebase}
{architecture_section}

DELIVERABLES:

Provide complete, production-ready configuration files with:
- Security best practices
- Performance optimizations
- Reliability mechanisms (health checks, graceful shutdown)
- Monitoring integration
- Clear documentation

Begin your deployment package now:
"""

    def _extract_config_files(self, deployment_doc: str) -> List[Dict[str, str]]:
        """
        Extract configuration files from deployment documentation

        PRODUCTION-READY: Handles parsing errors gracefully
        """
        config_files = []

        try:
            import re

            # Pattern: ```language\n# Filename\nContent\n```
            pattern = r'```(?:[\w]+)?\n#\s*([^\n]+)\n(.*?)```'
            matches = re.findall(pattern, deployment_doc, re.DOTALL)

            for filename, content in matches:
                filename = filename.strip()
                content = content.strip()

                if filename and content:
                    config_files.append({
                        "name": filename,
                        "content": content
                    })

            logger.info(
                "devops_engineer_agent.extracted_config_files",
                count=len(config_files)
            )

        except Exception as e:
            logger.warning(
                "devops_engineer_agent.extract_config_files.error",
                error=str(e)
            )
            # Return empty list on error - don't fail entire deployment generation

        return config_files

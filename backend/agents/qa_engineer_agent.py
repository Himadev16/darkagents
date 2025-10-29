"""
Agent 05: QA Engineer
Senior QA engineer that generates comprehensive test suites and identifies bugs
PRODUCTION-READY with retry logic, rollback, and validation
"""
import time
from typing import Dict, Any, List
import structlog
from sqlalchemy.orm import Session

from backend.database.models import AgentExecution, Project
from backend.agents.base_agent import BaseAgent
from backend.lib.openrouter import openrouter_client

logger = structlog.get_logger()


class QAEngineerAgent(BaseAgent):
    """
    QA Engineer Agent

    Senior QA engineer with 10+ years of testing experience.

    Capabilities:
    - Comprehensive test suite generation (unit, integration, E2E)
    - Bug detection and reporting (severity levels, reproduction steps)
    - Test coverage analysis (line coverage, branch coverage)
    - Performance testing (load testing, benchmarks)
    - Security testing (SQL injection, XSS, CSRF)
    - Code quality assessment (quality score 0-100)

    Production Features:
    - Retry logic with exponential backoff (3 retries)
    - Input validation with detailed error messages
    - Database transaction management with rollback
    - Graceful error handling
    - Detailed structured logging
    """

    def __init__(self):
        """Initialize QA Engineer Agent"""
        self.agent_name = "qa_engineer"
        self.agent_display_name = "QA Engineer"
        self.max_retries = 3
        self.retry_delay = 2  # Base delay in seconds for exponential backoff

    def execute(self, project_id: int, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Execute QA Engineer Agent

        Args:
            project_id: Project ID
            input_data: {
                "codebase": str (code to analyze and test),
                "test_framework": str (optional, e.g., "pytest", "jest", "auto-detect"),
                "coverage_target": int (optional, target coverage percentage),
                "test_types": list (optional, e.g., ["unit", "integration", "e2e"])
            }
            db: Database session

        Returns:
            {
                "success": bool,
                "test_suite": str (comprehensive test suite code),
                "bugs_found": list (bug reports with severity),
                "quality_score": int (0-100),
                "coverage_estimate": int (estimated coverage %),
                "execution_id": int,
                "tokens_used": int,
                "cost_usd": float,
                "error": str (if success=False)
            }
        """
        execution = None
        try:
            logger.info(
                "qa_engineer_started",
                project_id=project_id,
                agent_name=self.agent_name
            )

            # Input validation
            if not input_data:
                input_data = {}

            codebase = input_data.get("codebase") or input_data.get("code", "")
            if not codebase or not isinstance(codebase, str):
                raise ValueError("Missing or invalid 'codebase' (must be non-empty string)")

            if len(codebase.strip()) < 20:
                raise ValueError("codebase too short (minimum 20 characters)")

            # Optional fields with safe defaults
            test_framework = input_data.get("test_framework", "auto-detect")
            coverage_target = input_data.get("coverage_target", 80)
            test_types = input_data.get("test_types", ["unit", "integration", "e2e", "performance"])

            # Validate coverage_target
            if not isinstance(coverage_target, int) or coverage_target < 0 or coverage_target > 100:
                raise ValueError("coverage_target must be integer between 0 and 100")

            # Create database record
            try:
                execution = AgentExecution(
                    project_id=project_id,
                    agent_name=self.agent_name,
                    agent_display_name=self.agent_display_name,
                    status="working",
                    progress=0,
                    current_task="Analyzing codebase for bugs",
                    tokens_used=0,
                    cost_usd=0.0
                )
                db.add(execution)
                db.commit()
                db.refresh(execution)

                logger.info(
                    "qa_engineer_execution_created",
                    execution_id=execution.id,
                    project_id=project_id
                )
            except Exception as db_error:
                logger.error("database_error_creating_execution", error=str(db_error))
                db.rollback()
                raise

            # Update progress
            execution.current_task = "Generating test suite and identifying bugs"
            execution.progress = 10
            try:
                db.commit()
            except Exception:
                db.rollback()

            # Analyze and test with retry logic
            result = self._analyze_and_test_with_retry(
                codebase=codebase,
                test_framework=test_framework,
                coverage_target=coverage_target,
                test_types=test_types,
                project_id=project_id,
                execution=execution,
                db=db
            )

            # Update execution record with results
            try:
                execution.status = "completed"
                execution.progress = 100
                execution.current_task = "QA analysis complete"
                execution.tokens_used = result.get("tokens_used", 0)
                execution.cost_usd = result.get("cost_usd", 0.0)
                db.commit()

                logger.info(
                    "qa_engineer_completed",
                    execution_id=execution.id,
                    project_id=project_id,
                    bugs_found=len(result.get("bugs_found", [])),
                    quality_score=result.get("quality_score", 0),
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
                "qa_engineer_validation_error",
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
                "qa_engineer_failed",
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

    def _analyze_and_test_with_retry(
        self,
        codebase: str,
        test_framework: str,
        coverage_target: int,
        test_types: List[str],
        project_id: int,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Analyze and test with retry logic (exponential backoff)

        Retries up to max_retries times with exponential backoff on transient errors
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "qa_analysis_attempt",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    project_id=project_id
                )

                result = self._analyze_and_test(
                    codebase=codebase,
                    test_framework=test_framework,
                    coverage_target=coverage_target,
                    test_types=test_types,
                    execution=execution,
                    db=db
                )

                logger.info(
                    "qa_analysis_success",
                    attempt=attempt,
                    project_id=project_id,
                    bugs_found=len(result.get("bugs_found", []))
                )

                return result

            except ValueError as ve:
                # Don't retry validation errors
                logger.error("qa_analysis_validation_error", error=str(ve))
                raise

            except Exception as e:
                last_error = e
                logger.warning(
                    "qa_analysis_attempt_failed",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    error=str(e),
                    error_type=type(e).__name__
                )

                if attempt == self.max_retries:
                    logger.error(
                        "qa_analysis_all_retries_failed",
                        project_id=project_id,
                        error=str(e)
                    )
                    raise

                # Exponential backoff: 2s, 4s, 8s
                wait_time = self.retry_delay * (2 ** (attempt - 1))
                logger.info(
                    "qa_analysis_retrying",
                    wait_time=wait_time,
                    next_attempt=attempt + 1
                )
                time.sleep(wait_time)

        # Should never reach here, but just in case
        raise last_error if last_error else Exception("Unknown error in retry logic")

    def _analyze_and_test(
        self,
        codebase: str,
        test_framework: str,
        coverage_target: int,
        test_types: List[str],
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Analyze code for bugs and generate comprehensive test suite using Claude Sonnet 4.5

        This is the core method that calls OpenRouter API
        """
        logger.info("analyzing_and_testing", test_framework=test_framework, coverage_target=coverage_target)

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(codebase, test_framework, coverage_target, test_types)

        # Update progress
        execution.current_task = "Calling Claude Sonnet 4.5 for QA analysis"
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
                temperature=0.3,  # Precise, methodical testing
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
        execution.current_task = "Extracting bug reports and quality metrics"
        execution.progress = 80
        try:
            db.commit()
        except Exception:
            db.rollback()

        # Extract structured data from response
        bugs_found = self._extract_bugs(content)
        quality_score = self._calculate_quality_score(content, bugs_found)
        coverage_estimate = self._estimate_coverage(content)

        return {
            "test_suite": content,
            "bugs_found": bugs_found,
            "quality_score": quality_score,
            "coverage_estimate": coverage_estimate,
            "tokens_used": tokens_used,
            "cost_usd": round(cost_usd, 4)
        }

    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt for QA Engineer agent"""
        return """You are the QA ENGINEER AGENT - a senior quality assurance engineer with 10+ years of testing experience.

# Your Identity

You are a world-class QA engineer specializing in:
- Test automation (pytest, Jest, Cypress, Playwright)
- Bug detection and reporting
- Test coverage analysis
- Performance testing
- Security testing
- Code quality assessment

# Your Mission

Analyze code for bugs and generate comprehensive test suites that ensure:
- **Complete Coverage** - Unit, integration, E2E tests
- **Bug Detection** - Identify logic errors, security flaws, edge cases
- **Quality Metrics** - Coverage estimation, quality score
- **Actionable Reports** - Clear bug reports with reproduction steps

# Test Framework Standards

**Python Testing (pytest):**
```python
# tests/test_user_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestUserAPI:
    def test_create_user_success(self):
        response = client.post("/api/users", json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        })
        assert response.status_code == 201
        assert response.json()["email"] == "test@example.com"

    def test_create_user_duplicate_email(self):
        # First user
        client.post("/api/users", json={"email": "test@example.com", "password": "Pass123!"})
        # Duplicate
        response = client.post("/api/users", json={"email": "test@example.com", "password": "Pass456!"})
        assert response.status_code == 409
```

**JavaScript/TypeScript Testing (Jest):**
```javascript
// tests/userApi.test.ts
import { describe, test, expect } from '@jest/globals';
import request from 'supertest';
import app from '../src/app';

describe('User API', () => {
  test('should create user successfully', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({ email: 'test@example.com', password: 'SecurePass123!' });

    expect(response.status).toBe(201);
    expect(response.body.email).toBe('test@example.com');
  });
});
```

# Bug Report Format

**Required Structure:**
```markdown
## BUG REPORT

### Bug #1: Missing Email Validation
- **Severity:** HIGH
- **Type:** Validation Error
- **Location:** `backend/api/routes/users.py:45`
- **Description:** User registration doesn't validate email uniqueness
- **Impact:** Duplicate users can be created with same email
- **Reproduction Steps:**
  1. POST /api/users with email "test@example.com"
  2. POST /api/users again with same email
  3. Second request succeeds when it should return 409
- **Recommended Fix:** Add unique constraint check
```

# Severity Levels

- **CRITICAL:** Security vulnerability, data loss, system crash
- **HIGH:** Major functionality broken, user cannot complete core task
- **MEDIUM:** Minor functionality broken, workaround exists
- **LOW:** Cosmetic issue, typo, minor UX improvement

# Your Deliverables

Generate ALL of the following:

1. **Test Suite** - Comprehensive tests (unit, integration, E2E)
2. **Bug Reports** - Detailed reports with severity and reproduction steps
3. **Coverage Report** - Estimated coverage %, untested paths
4. **Quality Score** - Overall quality (0-100) with breakdown
5. **Recommendations** - Priority fixes and testing gaps

# Testing Best Practices

1. **Test Naming** - Descriptive names explaining what is tested
2. **AAA Pattern** - Arrange, Act, Assert
3. **Independence** - Each test independent and idempotent
4. **Edge Cases** - Test null, empty, min, max, invalid inputs
5. **Error Cases** - Test all error paths
6. **Mocking** - Mock external dependencies
7. **Performance** - Include benchmarks for critical operations
8. **Security** - Test for SQL injection, XSS, CSRF

Remember: Your job is to identify bugs and create tests - NOT to fix bugs. Provide clear, actionable reports."""

    def _build_user_prompt(
        self,
        codebase: str,
        test_framework: str,
        coverage_target: int,
        test_types: List[str]
    ) -> str:
        """Build user prompt with code to analyze and test"""
        test_types_str = ", ".join(test_types)

        return f"""# QA Analysis Mission

Analyze the following codebase, identify bugs, and generate a comprehensive test suite.

## Testing Requirements

- **Test Framework**: {test_framework}
- **Coverage Target**: {coverage_target}%
- **Test Types**: {test_types_str}

## Your Task

1. **Analyze Code for Bugs:**
   - Logic errors
   - Validation errors
   - Security vulnerabilities (SQL injection, XSS, etc.)
   - Performance issues
   - Edge cases not handled
   - Race conditions

2. **Generate Test Suite:**
   - Unit tests for all functions/methods
   - Integration tests for API endpoints
   - E2E tests for user flows
   - Performance tests for critical operations
   - Edge case tests (null, empty, large inputs)

3. **Create Bug Reports:**
   - Severity level (critical, high, medium, low)
   - Bug type, location, description, impact
   - Reproduction steps

4. **Generate Coverage Report:**
   - Estimated line coverage (%)
   - Untested critical paths

5. **Calculate Quality Score:**
   - Overall quality (0-100)

## Codebase to Analyze

{codebase[:4000]}

## Deliverables

1. Test Suite Code (pytest for Python, Jest for JavaScript)
2. Bug Reports (severity, location, impact, reproduction)
3. Coverage Report (estimated %, untested paths)
4. Quality Score (0-100 with breakdown)
5. Recommendations (priority fixes, testing gaps)

Begin your QA analysis now:
"""

    def _extract_bugs(self, qa_report: str) -> List[Dict[str, Any]]:
        """
        Extract bug reports from QA analysis

        Returns list of bugs with severity, type, location, description, impact
        """
        import re

        bugs = []

        try:
            # Pattern: ### Bug #N: Title
            bug_blocks = re.split(r'###\s+Bug\s+#\d+:', qa_report)

            for block in bug_blocks[1:]:  # Skip first split (before first bug)
                bug = {}

                # Extract severity
                severity_match = re.search(r'\*\*Severity:\*\*\s+(CRITICAL|HIGH|MEDIUM|LOW)', block, re.IGNORECASE)
                if severity_match:
                    bug["severity"] = severity_match.group(1).lower()

                # Extract type
                type_match = re.search(r'\*\*Type:\*\*\s+(.+?)(?=\n|$)', block)
                if type_match:
                    bug["type"] = type_match.group(1).strip()

                # Extract location
                location_match = re.search(r'\*\*Location:\*\*\s+`?([^`\n]+)`?', block)
                if location_match:
                    bug["location"] = location_match.group(1).strip()

                # Extract description
                desc_match = re.search(r'\*\*Description:\*\*\s+(.+?)(?=\n\*\*|\n###|\Z)', block, re.DOTALL)
                if desc_match:
                    bug["description"] = desc_match.group(1).strip()

                # Extract impact
                impact_match = re.search(r'\*\*Impact:\*\*\s+(.+?)(?=\n\*\*|\n###|\Z)', block, re.DOTALL)
                if impact_match:
                    bug["impact"] = impact_match.group(1).strip()

                if bug:
                    bugs.append(bug)

            logger.info("extracted_bugs", count=len(bugs))

        except Exception as e:
            logger.warning("extract_bugs_error", error=str(e))

        return bugs

    def _calculate_quality_score(self, qa_report: str, bugs: List[Dict]) -> int:
        """
        Calculate quality score (0-100) based on bugs and analysis

        Score calculation:
        - Start at 100
        - Deduct points for bugs based on severity:
          - Critical: -15 points
          - High: -10 points
          - Medium: -5 points
          - Low: -2 points
        """
        score = 100

        for bug in bugs:
            severity = bug.get("severity", "low")
            if severity == "critical":
                score -= 15
            elif severity == "high":
                score -= 10
            elif severity == "medium":
                score -= 5
            elif severity == "low":
                score -= 2

        # Clamp to 0-100
        score = max(0, min(100, score))

        logger.info("calculated_quality_score", score=score, bugs_count=len(bugs))

        return score

    def _estimate_coverage(self, qa_report: str) -> int:
        """
        Estimate test coverage from QA report

        Looks for coverage percentage in report
        """
        import re

        try:
            # Pattern: Coverage: 82% or Overall Coverage: 82%
            coverage_match = re.search(r'(?:Overall\s+)?Coverage:\s+(\d+)%', qa_report, re.IGNORECASE)
            if coverage_match:
                coverage = int(coverage_match.group(1))
                logger.info("estimated_coverage", coverage=coverage)
                return coverage

        except Exception as e:
            logger.warning("estimate_coverage_error", error=str(e))

        return 0


# Singleton instance
qa_engineer_agent = QAEngineerAgent()

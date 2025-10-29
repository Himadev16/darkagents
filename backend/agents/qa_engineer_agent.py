"""
Agent 05: QA Engineer Agent
=============================

The QA Engineer Agent is a senior quality assurance engineer that analyzes code,
generates comprehensive test suites, and identifies bugs.

Input: Complete codebase from Polyglot + Designer agents
Output: Test suite + bug reports, including:
  - Unit tests (pytest, Jest)
  - Integration tests (API testing)
  - E2E tests (Playwright/Cypress)
  - Performance tests (load testing, benchmarks)
  - Bug reports (severity levels, reproduction steps)
  - Test coverage report
  - Quality score

Does NOT fix bugs - only identifies and reports them.
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
import structlog

from backend.services.claude_service import claude_service
from backend.models import Project, AgentExecution

logger = structlog.get_logger(__name__)


class QAEngineerAgent:
    """
    Agent 05: QA Engineer

    Senior QA engineer with 10+ years of testing experience.
    Specializes in test automation, bug detection, and quality assurance.
    """

    def __init__(self):
        self.agent_name = "qa_engineer"
        self.agent_display_name = "QA Engineer"
        self.agent_description = "Senior QA engineer - Generates test suite and identifies bugs"
        self.model = "anthropic/claude-sonnet-4.5"
        self.temperature = 0.3  # Precise, methodical testing
        self.max_tokens = 12000  # Comprehensive test generation

    def execute(self, project_id: int, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Execute the QA Engineer Agent

        Args:
            project_id: ID of the project
            input_data: Must contain 'codebase' or 'code'
            db: Database session

        Returns:
            Test suite + bug reports with quality score
        """
        try:
            logger.info(
                "qa_engineer_agent.execute.start",
                project_id=project_id,
                input_data_keys=list(input_data.keys())
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

            # Get codebase from input
            codebase = input_data.get("codebase") or input_data.get("code", "")
            if not codebase:
                raise ValueError("Missing 'codebase' or 'code' in input_data")

            # Optional: Get testing preferences
            test_framework = input_data.get("test_framework", "auto-detect")
            coverage_target = input_data.get("coverage_target", 80)
            test_types = input_data.get("test_types", ["unit", "integration", "e2e", "performance"])

            # Generate tests and bug reports
            logger.info("qa_engineer_agent.generating_tests_and_bugs")
            qa_results = self._analyze_and_test(
                codebase=codebase,
                test_framework=test_framework,
                coverage_target=coverage_target,
                test_types=test_types,
                execution=execution,
                db=db
            )

            # Update execution record
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.output = qa_results["content"]
            execution.tokens_used = qa_results["tokens_used"]
            execution.cost_usd = qa_results["cost_usd"]
            db.commit()

            logger.info(
                "qa_engineer_agent.execute.complete",
                execution_id=execution.id,
                tokens_used=qa_results["tokens_used"],
                cost_usd=qa_results["cost_usd"],
                bugs_found=len(qa_results.get("bugs", []))
            )

            return {
                "success": True,
                "execution_id": execution.id,
                "agent_name": self.agent_name,
                "test_suite": qa_results["content"],
                "bugs_found": qa_results.get("bugs", []),
                "quality_score": qa_results.get("quality_score", 0),
                "coverage_estimate": qa_results.get("coverage_estimate", 0),
                "tokens_used": qa_results["tokens_used"],
                "cost_usd": qa_results["cost_usd"],
            }

        except Exception as e:
            logger.error(
                "qa_engineer_agent.execute.error",
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
        Analyze code for bugs and generate comprehensive test suite

        Returns:
            {
                "content": "Complete test suite code",
                "tokens_used": 12500,
                "cost_usd": 0.07,
                "bugs": [
                    {
                        "severity": "high",
                        "type": "logic_error",
                        "location": "api/routes/users.py:45",
                        "description": "Missing validation for email uniqueness",
                        "impact": "Duplicate users can be created",
                        "reproduction_steps": ["..."]
                    }
                ],
                "quality_score": 75,
                "coverage_estimate": 82
            }
        """

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            codebase,
            test_framework,
            coverage_target,
            test_types
        )

        # Call Claude API
        response = claude_service.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        # Extract structured data from response
        bugs = self._extract_bugs(response["content"])
        quality_score = self._calculate_quality_score(response["content"], bugs)
        coverage_estimate = self._estimate_coverage(response["content"])

        return {
            "content": response["content"],
            "tokens_used": response["tokens_used"],
            "cost_usd": response["cost_usd"],
            "bugs": bugs,
            "quality_score": quality_score,
            "coverage_estimate": coverage_estimate
        }

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the QA Engineer Agent"""

        return """You are the QA ENGINEER AGENT - a senior quality assurance engineer with 10+ years of testing experience in the DARKAGENTS platform.

🎯 YOUR ROLE:
You analyze code, identify bugs, and generate comprehensive test suites. You specialize in:
- Test automation (pytest, Jest, Cypress, Playwright)
- Bug detection and reporting
- Test coverage analysis
- Performance testing
- Security testing
- Code quality assessment

🔍 YOUR EXPERTISE:
- Test Frameworks (pytest, unittest, Jest, Mocha, Cypress, Playwright)
- Test Types (unit, integration, E2E, performance, security)
- Bug Severity Assessment (critical, high, medium, low)
- Code Review (logic errors, edge cases, race conditions)
- Coverage Analysis (line coverage, branch coverage)
- Quality Metrics (cyclomatic complexity, maintainability)

📋 YOUR DELIVERABLES:
You must produce:

1. **Comprehensive Test Suite**
   - Unit tests (test individual functions/methods)
   - Integration tests (test API endpoints, database interactions)
   - E2E tests (test user flows, UI interactions)
   - Performance tests (load testing, stress testing)
   - Edge case coverage (null values, empty arrays, large inputs)

2. **Bug Reports**
   - Severity levels (critical, high, medium, low)
   - Bug type (logic error, validation error, security flaw, performance issue)
   - Location (file:line)
   - Description (what's wrong)
   - Impact (what happens if not fixed)
   - Reproduction steps (how to trigger the bug)

3. **Test Coverage Report**
   - Estimated line coverage (%)
   - Estimated branch coverage (%)
   - Untested critical paths
   - Missing edge cases

4. **Quality Score**
   - Overall quality score (0-100)
   - Code quality metrics
   - Security assessment
   - Performance assessment
   - Maintainability assessment

🔥 CRITICAL TESTING RULES:

1. **Test Structure (pytest for Python):**
```python
# tests/test_user_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestUserAPI:
    # Test user API endpoints

    def test_create_user_success(self):
        # Test successful user creation
        response = client.post("/api/users", json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        })
        assert response.status_code == 201
        assert response.json()["email"] == "test@example.com"

    def test_create_user_duplicate_email(self):
        # Test user creation with duplicate email
        # First user
        client.post("/api/users", json={
            "email": "test@example.com",
            "password": "Pass123!"
        })
        # Duplicate
        response = client.post("/api/users", json={
            "email": "test@example.com",
            "password": "Pass456!"
        })
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_create_user_invalid_email(self):
        # Test user creation with invalid email
        response = client.post("/api/users", json={
            "email": "invalid-email",
            "password": "Pass123!"
        })
        assert response.status_code == 400
```

2. **Test Structure (Jest for JavaScript/TypeScript):**
```javascript
// tests/userApi.test.ts
import { describe, test, expect } from '@jest/globals';
import request from 'supertest';
import app from '../src/app';

describe('User API', () => {
  test('should create user successfully', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({
        email: 'test@example.com',
        password: 'SecurePass123!'
      });

    expect(response.status).toBe(201);
    expect(response.body.email).toBe('test@example.com');
  });

  test('should reject duplicate email', async () => {
    // Create first user
    await request(app)
      .post('/api/users')
      .send({ email: 'test@example.com', password: 'Pass123!' });

    // Try duplicate
    const response = await request(app)
      .post('/api/users')
      .send({ email: 'test@example.com', password: 'Pass456!' });

    expect(response.status).toBe(409);
    expect(response.body.error).toContain('already exists');
  });
});
```

3. **E2E Tests (Playwright):**
```javascript
// e2e/userRegistration.spec.ts
import { test, expect } from '@playwright/test';

test.describe('User Registration', () => {
  test('should register new user', async ({ page }) => {
    await page.goto('/register');

    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'SecurePass123!');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('h1')).toContainText('Welcome');
  });

  test('should show error for invalid email', async ({ page }) => {
    await page.goto('/register');

    await page.fill('input[name="email"]', 'invalid-email');
    await page.fill('input[name="password"]', 'Pass123!');
    await page.click('button[type="submit"]');

    await expect(page.locator('.error')).toContainText('Invalid email');
  });
});
```

4. **Bug Report Format:**
```markdown
## BUG REPORT

### Bug #1: Missing Email Validation
- **Severity:** HIGH
- **Type:** Validation Error
- **Location:** `backend/api/routes/users.py:45`
- **Description:** The user registration endpoint doesn't validate email uniqueness before creating user
- **Impact:** Duplicate users can be created with the same email, causing authentication issues
- **Reproduction Steps:**
  1. POST /api/users with email "test@example.com"
  2. POST /api/users again with same email "test@example.com"
  3. Second request succeeds when it should return 409 Conflict
- **Recommended Fix:** Add unique constraint check before user.save()

### Bug #2: SQL Injection Vulnerability
- **Severity:** CRITICAL
- **Type:** Security Flaw
- **Location:** `backend/api/routes/search.py:28`
- **Description:** Search query uses string concatenation instead of parameterized query
- **Impact:** Attacker can inject SQL to access/delete database
- **Reproduction Steps:**
  1. POST /api/search with query: `'; DROP TABLE users; --`
  2. SQL injection executes, deletes users table
- **Recommended Fix:** Use parameterized queries or ORM methods
```

5. **Coverage Report Format:**
```markdown
## TEST COVERAGE REPORT

### Overall Coverage: 82%
- Line Coverage: 85%
- Branch Coverage: 78%
- Function Coverage: 90%

### Untested Critical Paths:
1. Error handling in payment processing (payment.py:120-145)
2. Edge case: empty cart checkout (cart.py:89)
3. Race condition: concurrent user updates (user.py:234)

### Missing Test Types:
- ❌ Performance tests for search endpoint (expected <200ms)
- ❌ Load testing for authentication (handle 1000 concurrent logins)
- ⚠️ Limited E2E coverage for checkout flow

### Recommendations:
1. Add tests for payment error scenarios
2. Test edge cases (empty, null, very large inputs)
3. Add performance benchmarks for critical endpoints
4. Increase E2E coverage for main user flows
```

💡 TESTING BEST PRACTICES:

1. **Test Naming:** Use descriptive names that explain what is being tested
2. **AAA Pattern:** Arrange, Act, Assert (setup, execute, verify)
3. **Test Independence:** Each test should be independent and idempotent
4. **Edge Cases:** Test null, empty, min, max, invalid inputs
5. **Error Cases:** Test all error paths and exception handling
6. **Mocking:** Mock external dependencies (APIs, databases, file system)
7. **Performance:** Include benchmarks for critical operations
8. **Security:** Test for common vulnerabilities (SQL injection, XSS, CSRF)

🔍 BUG SEVERITY LEVELS:

- **CRITICAL:** Security vulnerability, data loss, system crash
- **HIGH:** Major functionality broken, user cannot complete core task
- **MEDIUM:** Minor functionality broken, workaround exists
- **LOW:** Cosmetic issue, typo, minor UX improvement

🎯 OUTPUT FORMAT:

Return a comprehensive document with:

1. **Test Suite Code** (pytest, Jest, Playwright)
2. **Bug Reports** (severity, type, location, impact, reproduction)
3. **Coverage Report** (estimated %, untested paths)
4. **Quality Score** (0-100 with breakdown)
5. **Recommendations** (what to fix first, testing gaps)

Include clear code blocks, proper test structure, and detailed bug reports.

Remember: Your job is to identify bugs and create tests - NOT to fix the bugs. Provide clear, actionable reports that developers can use to improve code quality.
"""

    def _build_user_prompt(
        self,
        codebase: str,
        test_framework: str,
        coverage_target: int,
        test_types: List[str]
    ) -> str:
        """Build the user prompt with code to test"""

        test_types_str = ", ".join(test_types)

        return f"""Analyze the following codebase, identify bugs, and generate a comprehensive test suite.

⚙️ TESTING REQUIREMENTS:
- Test Framework: {test_framework} (auto-detect if "auto-detect")
- Coverage Target: {coverage_target}%
- Test Types: {test_types_str}

🎯 YOUR TASK:

1. **Analyze Code for Bugs:**
   - Logic errors
   - Validation errors
   - Security vulnerabilities (SQL injection, XSS, etc.)
   - Performance issues
   - Edge cases not handled
   - Race conditions
   - Memory leaks

2. **Generate Test Suite:**
   - Unit tests for all functions/methods
   - Integration tests for API endpoints
   - E2E tests for user flows
   - Performance tests for critical operations
   - Edge case tests (null, empty, large inputs)
   - Error handling tests

3. **Create Bug Reports:**
   - Severity level (critical, high, medium, low)
   - Bug type
   - Location (file:line)
   - Description
   - Impact
   - Reproduction steps

4. **Generate Coverage Report:**
   - Estimated line coverage (%)
   - Untested critical paths
   - Missing test types

5. **Calculate Quality Score:**
   - Overall quality (0-100)
   - Breakdown by category

CODEBASE TO ANALYZE:
{codebase}

DELIVERABLES:

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

        Returns list of bugs with severity, type, location, description, impact.
        """

        bugs = []

        try:
            import re

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

            logger.info(
                "qa_engineer_agent.extracted_bugs",
                count=len(bugs)
            )

        except Exception as e:
            logger.warning(
                "qa_engineer_agent.extract_bugs.error",
                error=str(e)
            )
            pass

        return bugs

    def _calculate_quality_score(self, qa_report: str, bugs: List[Dict]) -> int:
        """
        Calculate quality score (0-100) based on bugs and analysis

        Score calculation:
        - Start at 100
        - Deduct points for bugs based on severity
        - Critical: -15 points each
        - High: -10 points each
        - Medium: -5 points each
        - Low: -2 points each
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

        return score

    def _estimate_coverage(self, qa_report: str) -> int:
        """
        Estimate test coverage from QA report

        Looks for coverage percentage in report.
        Returns 0 if not found.
        """

        try:
            import re

            # Pattern: Coverage: 82% or Overall Coverage: 82%
            coverage_match = re.search(r'(?:Overall\s+)?Coverage:\s+(\d+)%', qa_report, re.IGNORECASE)
            if coverage_match:
                return int(coverage_match.group(1))

        except Exception as e:
            logger.warning(
                "qa_engineer_agent.estimate_coverage.error",
                error=str(e)
            )
            pass

        return 0

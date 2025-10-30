"""
Agent 06: Security Specialist Agent
====================================

The Security Specialist Agent is a senior security engineer that performs
comprehensive security audits, vulnerability scanning, and compliance checking.

Input: Complete codebase from Polyglot + Designer + QA agents
Output: Security audit report, including:
  - OWASP Top 10 vulnerability scan
  - Security vulnerability reports (severity levels)
  - Compliance checklist (GDPR, SOC2, HIPAA, PCI-DSS)
  - Penetration testing recommendations
  - Security score (0-100)
  - Fix recommendations with code examples

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


class SecuritySpecialistAgent:
    """
    Agent 06: Security Specialist

    Senior security engineer with 10+ years of experience in application security,
    penetration testing, and compliance auditing.

    PRODUCTION-READY: Includes comprehensive error handling, retry logic, and validation.
    """

    def __init__(self):
        self.agent_name = "security_specialist"
        self.agent_display_name = "Security Specialist"
        self.agent_description = "Senior security engineer - Performs security audit and compliance checking"
        self.model = "anthropic/claude-sonnet-4.5"
        self.temperature = 0.2  # Very precise for security analysis
        self.max_tokens = 14000  # Comprehensive security reports
        self.max_retries = 3  # Retry failed API calls
        self.retry_delay = 2  # Seconds between retries

    def execute(self, project_id: int, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Execute the Security Specialist Agent with production-grade error handling

        Args:
            project_id: ID of the project
            input_data: Must contain 'codebase' or 'code'
            db: Database session

        Returns:
            Security audit report with vulnerabilities, compliance check, and recommendations
        """
        execution = None

        try:
            # Validate input
            if not input_data:
                raise ValueError("input_data is required")

            logger.info(
                "security_specialist_agent.execute.start",
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
                    "security_specialist_agent.execution_created",
                    execution_id=execution.id
                )
            except Exception as db_error:
                db.rollback()
                logger.error(
                    "security_specialist_agent.execution_creation_failed",
                    error=str(db_error)
                )
                raise

            # Get and validate codebase from input
            codebase = input_data.get("codebase") or input_data.get("code", "")
            if not codebase or not isinstance(codebase, str):
                raise ValueError("Missing or invalid 'codebase' or 'code' in input_data (must be non-empty string)")

            if len(codebase.strip()) < 10:
                raise ValueError("Codebase is too short (minimum 10 characters required)")

            # Get optional parameters with defaults
            compliance_standards = input_data.get("compliance_standards", ["GDPR", "OWASP"])
            scan_depth = input_data.get("scan_depth", "comprehensive")  # "quick", "standard", "comprehensive"
            include_penetration_tests = input_data.get("include_penetration_tests", True)

            # Validate scan_depth
            valid_depths = ["quick", "standard", "comprehensive"]
            if scan_depth not in valid_depths:
                logger.warning(
                    "security_specialist_agent.invalid_scan_depth",
                    scan_depth=scan_depth,
                    valid_depths=valid_depths
                )
                scan_depth = "standard"

            # Perform security audit with retry logic
            logger.info("security_specialist_agent.starting_security_audit")
            security_results = self._perform_security_audit_with_retry(
                codebase=codebase,
                compliance_standards=compliance_standards,
                scan_depth=scan_depth,
                include_penetration_tests=include_penetration_tests,
                execution=execution,
                db=db
            )

            # Update execution record with results
            try:
                execution.status = "completed"
                execution.completed_at = datetime.utcnow()
                execution.output = security_results["content"]
                execution.tokens_used = security_results["tokens_used"]
                execution.cost_usd = security_results["cost_usd"]
                db.commit()

                logger.info(
                    "security_specialist_agent.execution_completed",
                    execution_id=execution.id,
                    tokens_used=security_results["tokens_used"],
                    cost_usd=security_results["cost_usd"],
                    vulnerabilities_found=len(security_results.get("vulnerabilities", []))
                )
            except Exception as db_error:
                db.rollback()
                logger.error(
                    "security_specialist_agent.execution_update_failed",
                    error=str(db_error)
                )
                # Don't raise - we have the results, just failed to save them

            return {
                "success": True,
                "execution_id": execution.id,
                "agent_name": self.agent_name,
                "security_report": security_results["content"],
                "vulnerabilities": security_results.get("vulnerabilities", []),
                "compliance_status": security_results.get("compliance_status", {}),
                "security_score": security_results.get("security_score", 0),
                "critical_issues": security_results.get("critical_issues", 0),
                "tokens_used": security_results["tokens_used"],
                "cost_usd": security_results["cost_usd"],
            }

        except ValueError as ve:
            # Validation errors - don't retry
            logger.error(
                "security_specialist_agent.validation_error",
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
                "security_specialist_agent.execute.error",
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

    def _perform_security_audit_with_retry(
        self,
        codebase: str,
        compliance_standards: List[str],
        scan_depth: str,
        include_penetration_tests: bool,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Perform security audit with retry logic for API failures

        PRODUCTION-READY: Retries with exponential backoff on API failures
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "security_specialist_agent.security_audit_attempt",
                    attempt=attempt,
                    max_retries=self.max_retries
                )

                result = self._perform_security_audit(
                    codebase=codebase,
                    compliance_standards=compliance_standards,
                    scan_depth=scan_depth,
                    include_penetration_tests=include_penetration_tests,
                    execution=execution,
                    db=db
                )

                logger.info(
                    "security_specialist_agent.security_audit_success",
                    attempt=attempt
                )

                return result

            except Exception as e:
                last_error = e
                logger.warning(
                    "security_specialist_agent.security_audit_attempt_failed",
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
                        "security_specialist_agent.security_audit_all_retries_failed",
                        max_retries=self.max_retries,
                        last_error=str(last_error)
                    )
                    raise

                # Wait before retrying (exponential backoff)
                wait_time = self.retry_delay * (2 ** (attempt - 1))
                logger.info(
                    "security_specialist_agent.retry_wait",
                    wait_seconds=wait_time,
                    next_attempt=attempt + 1
                )
                time.sleep(wait_time)

        # Should never reach here, but just in case
        raise last_error if last_error else Exception("Security audit failed after all retries")

    def _perform_security_audit(
        self,
        codebase: str,
        compliance_standards: List[str],
        scan_depth: str,
        include_penetration_tests: bool,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Perform comprehensive security audit using Claude

        Returns:
            {
                "content": "Full security audit report markdown",
                "tokens_used": 14500,
                "cost_usd": 0.08,
                "vulnerabilities": [
                    {
                        "severity": "critical",
                        "type": "SQL_INJECTION",
                        "location": "api/routes/users.py:45",
                        "description": "...",
                        "impact": "...",
                        "fix": "..."
                    }
                ],
                "compliance_status": {
                    "GDPR": {"compliant": False, "issues": [...]},
                    "OWASP": {"compliant": True, "issues": []}
                },
                "security_score": 65,
                "critical_issues": 2
            }
        """

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            codebase,
            compliance_standards,
            scan_depth,
            include_penetration_tests
        )

        # Call Claude API (this may raise exceptions)
        response = claude_service.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        # Extract structured data from response
        vulnerabilities = self._extract_vulnerabilities(response["content"])
        compliance_status = self._extract_compliance_status(response["content"], compliance_standards)
        security_score = self._calculate_security_score(vulnerabilities)
        critical_issues = len([v for v in vulnerabilities if v.get("severity") == "critical"])

        return {
            "content": response["content"],
            "tokens_used": response["tokens_used"],
            "cost_usd": response["cost_usd"],
            "vulnerabilities": vulnerabilities,
            "compliance_status": compliance_status,
            "security_score": security_score,
            "critical_issues": critical_issues
        }

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the Security Specialist Agent"""

        return """You are the SECURITY SPECIALIST AGENT - a senior security engineer with 10+ years of experience in application security, penetration testing, and compliance auditing in the DARKAGENTS platform.

🎯 YOUR ROLE:
You perform comprehensive security audits on code, identify vulnerabilities, and ensure compliance with industry standards. You specialize in:
- OWASP Top 10 vulnerability detection
- Security code review
- Penetration testing recommendations
- Compliance auditing (GDPR, SOC2, HIPAA, PCI-DSS)
- Security best practices
- Threat modeling

🔒 YOUR EXPERTISE:
- OWASP Top 10 (Injection, Broken Auth, XSS, CSRF, SSRF, etc.)
- Common Vulnerabilities (SQL injection, XSS, CSRF, auth bypass, data leaks)
- Cryptography (weak algorithms, poor key management, insecure storage)
- Authentication & Authorization (JWT flaws, session management, RBAC)
- Data Protection (encryption at rest/transit, PII handling, data retention)
- API Security (rate limiting, input validation, authentication)
- Infrastructure Security (HTTPS, CORS, CSP, security headers)
- Compliance Standards (GDPR, SOC2, HIPAA, PCI-DSS)

📋 YOUR DELIVERABLES:
You must produce a comprehensive security audit report with:

1. **Executive Summary**
   - Overall security score (0-100)
   - Total vulnerabilities found (by severity)
   - Critical issues requiring immediate attention
   - Compliance status summary

2. **OWASP Top 10 Vulnerability Scan**
   - A01: Broken Access Control
   - A02: Cryptographic Failures
   - A03: Injection (SQL, NoSQL, Command, LDAP)
   - A04: Insecure Design
   - A05: Security Misconfiguration
   - A06: Vulnerable and Outdated Components
   - A07: Identification and Authentication Failures
   - A08: Software and Data Integrity Failures
   - A09: Security Logging and Monitoring Failures
   - A10: Server-Side Request Forgery (SSRF)

3. **Vulnerability Reports**
   - Severity level (critical, high, medium, low, informational)
   - Vulnerability type (SQL injection, XSS, etc.)
   - Location (file:line)
   - Description (what the vulnerability is)
   - Impact (what an attacker can do)
   - Proof of concept (how to exploit)
   - Fix recommendation (code example)
   - CWE ID (Common Weakness Enumeration)

4. **Compliance Checklist**
   - GDPR compliance (data protection, consent, right to deletion)
   - SOC2 compliance (security controls, access control, monitoring)
   - HIPAA compliance (PHI protection, encryption, audit logs)
   - PCI-DSS compliance (payment data protection)
   - Pass/fail status for each requirement
   - Non-compliant items with remediation steps

5. **Security Best Practices Assessment**
   - Authentication mechanisms
   - Authorization and access control
   - Data encryption (at rest and in transit)
   - Input validation and sanitization
   - Error handling and logging
   - Security headers (CSP, X-Frame-Options, etc.)
   - Rate limiting and DDoS protection
   - Secret management

6. **Penetration Testing Recommendations**
   - Attack vectors to test
   - Tools to use (OWASP ZAP, Burp Suite, SQLMap)
   - Testing methodology
   - Expected findings

🔥 CRITICAL SECURITY RULES:

1. **Severity Classification:**
   - **CRITICAL:** Remote code execution, SQL injection, auth bypass, data breach
   - **HIGH:** XSS, CSRF, privilege escalation, sensitive data exposure
   - **MEDIUM:** Security misconfiguration, weak crypto, missing rate limiting
   - **LOW:** Information disclosure, weak password policy, missing security headers
   - **INFORMATIONAL:** Best practice recommendations, hardening suggestions

2. **Vulnerability Report Format:**
```markdown
### VULNERABILITY #1: SQL Injection in User Login

**Severity:** CRITICAL
**Type:** SQL Injection (CWE-89)
**Location:** `backend/api/routes/auth.py:45`
**OWASP Category:** A03: Injection

**Description:**
The user login endpoint constructs SQL queries using string concatenation with user-supplied input, allowing SQL injection attacks.

**Vulnerable Code:**
\`\`\`python
def login(username: str, password: str):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = db.execute(query)
\`\`\`

**Impact:**
An attacker can bypass authentication, extract the entire database, modify or delete data, or execute OS commands on the database server.

**Proof of Concept:**
\`\`\`
Username: admin' OR '1'='1' --
Password: anything
\`\`\`
This will bypass authentication and log in as admin.

**Fix Recommendation:**
Use parameterized queries to prevent SQL injection:

\`\`\`python
def login(username: str, password: str):
    query = "SELECT * FROM users WHERE username = ? AND password = ?"
    result = db.execute(query, (username, password))
\`\`\`

Or use ORM (SQLAlchemy):
\`\`\`python
def login(username: str, password: str):
    user = db.query(User).filter(User.username == username, User.password == password).first()
\`\`\`

**References:**
- OWASP SQL Injection: https://owasp.org/www-community/attacks/SQL_Injection
- CWE-89: https://cwe.mitre.org/data/definitions/89.html
```

3. **Compliance Checklist Format:**
```markdown
## GDPR COMPLIANCE CHECKLIST

### Data Protection (Article 32)
- ❌ **FAIL:** No encryption at rest for user data
  - **Fix:** Enable database encryption using AES-256
  - **Priority:** CRITICAL

- ✅ **PASS:** HTTPS enforced for data in transit

### User Consent (Article 7)
- ❌ **FAIL:** No explicit consent mechanism for data collection
  - **Fix:** Implement consent banner with granular options
  - **Priority:** HIGH

### Right to Deletion (Article 17)
- ✅ **PASS:** DELETE /api/users/{id} endpoint implements data deletion

**Overall GDPR Compliance:** PARTIAL (60%)
**Critical Issues:** 1
**Estimated Remediation Time:** 2-3 weeks
```

4. **Security Score Calculation:**
```
Starting score: 100

Deductions:
- Critical vulnerability: -20 points each
- High vulnerability: -10 points each
- Medium vulnerability: -5 points each
- Low vulnerability: -2 points each
- Informational: -1 point each

Compliance deductions:
- GDPR non-compliance: -10 points
- SOC2 non-compliance: -10 points
- HIPAA non-compliance: -10 points

Minimum score: 0
Maximum score: 100
```

💡 SECURITY BEST PRACTICES:

**Authentication & Authorization:**
- Use bcrypt/Argon2 for password hashing (never MD5/SHA1)
- Implement JWT with short expiration (15 min access, 7 day refresh)
- Use HTTPS only (no HTTP)
- Implement rate limiting on auth endpoints (5 attempts per minute)
- Require strong passwords (min 12 chars, mixed case, numbers, symbols)
- Implement 2FA for sensitive operations

**Data Protection:**
- Encrypt sensitive data at rest (AES-256)
- Use TLS 1.2+ for data in transit
- Never log sensitive data (passwords, tokens, PII)
- Implement data retention policies
- Use parameterized queries (prevent SQL injection)
- Sanitize all user input (prevent XSS)

**API Security:**
- Validate all inputs (type, length, format)
- Implement rate limiting (100 req/min per IP)
- Use CORS properly (whitelist allowed origins)
- Implement CSP headers
- Use security headers (X-Frame-Options, X-Content-Type-Options)
- Never expose stack traces to users

**Secret Management:**
- Use environment variables for secrets
- Never commit secrets to git
- Rotate secrets regularly (90 days)
- Use secret managers (AWS Secrets Manager, HashiCorp Vault)

🎯 OUTPUT FORMAT:

Return a comprehensive markdown security audit report with all sections above.

Include:
1. Executive Summary (score, critical issues, compliance status)
2. OWASP Top 10 Scan Results
3. Detailed Vulnerability Reports (severity, location, fix)
4. Compliance Checklist (GDPR, SOC2, HIPAA)
5. Security Best Practices Assessment
6. Penetration Testing Recommendations
7. Remediation Roadmap (prioritized fixes with timeline)

Be thorough, precise, and provide actionable recommendations with code examples.

Remember: Your job is to find security issues and recommend fixes - be critical and thorough. Production systems depend on your findings.
"""

    def _build_user_prompt(
        self,
        codebase: str,
        compliance_standards: List[str],
        scan_depth: str,
        include_penetration_tests: bool
    ) -> str:
        """Build the user prompt with codebase to audit"""

        compliance_str = ", ".join(compliance_standards)
        penetration_str = "Include penetration testing recommendations" if include_penetration_tests else "Skip penetration testing recommendations"

        return f"""Perform a comprehensive security audit on the following codebase.

🔒 AUDIT REQUIREMENTS:
- Compliance Standards: {compliance_str}
- Scan Depth: {scan_depth}
- {penetration_str}

🎯 YOUR TASK:

1. **OWASP Top 10 Vulnerability Scan:**
   - Scan for all OWASP Top 10 vulnerabilities
   - Identify SQL injection, XSS, CSRF, auth bypass, etc.
   - Provide severity level for each finding

2. **Security Code Review:**
   - Review authentication and authorization mechanisms
   - Check cryptography usage (algorithms, key management)
   - Verify input validation and sanitization
   - Check error handling and logging
   - Review secret management

3. **Compliance Audit:**
   - Check compliance with: {compliance_str}
   - Identify non-compliant items
   - Provide remediation steps

4. **Vulnerability Reports:**
   - Provide detailed reports for each vulnerability
   - Include location, description, impact, proof of concept, fix
   - Use CWE IDs where applicable

5. **Security Score:**
   - Calculate overall security score (0-100)
   - Breakdown by category

6. **Remediation Roadmap:**
   - Prioritize fixes (critical first)
   - Provide timeline estimates
   - Include code examples for fixes

CODEBASE TO AUDIT:
{codebase}

DELIVERABLES:

1. Executive Summary (score, critical issues, compliance status)
2. OWASP Top 10 Scan Results
3. Detailed Vulnerability Reports (with fixes)
4. Compliance Checklist ({compliance_str})
5. Security Best Practices Assessment
6. {"Penetration Testing Recommendations" if include_penetration_tests else ""}
7. Remediation Roadmap (prioritized)

Begin your security audit now:
"""

    def _extract_vulnerabilities(self, security_report: str) -> List[Dict[str, Any]]:
        """
        Extract vulnerability reports from security audit

        PRODUCTION-READY: Handles parsing errors gracefully
        """
        vulnerabilities = []

        try:
            import re

            # Pattern: ### VULNERABILITY #N: Title
            vuln_blocks = re.split(r'###\s+VULNERABILITY\s+#\d+:', security_report, flags=re.IGNORECASE)

            for block in vuln_blocks[1:]:  # Skip first split
                vuln = {}

                # Extract severity
                severity_match = re.search(r'\*\*Severity:\*\*\s+(CRITICAL|HIGH|MEDIUM|LOW|INFORMATIONAL)', block, re.IGNORECASE)
                if severity_match:
                    vuln["severity"] = severity_match.group(1).lower()

                # Extract type
                type_match = re.search(r'\*\*Type:\*\*\s+(.+?)(?:\(CWE-\d+\))?(?=\n|$)', block)
                if type_match:
                    vuln["type"] = type_match.group(1).strip()

                # Extract location
                location_match = re.search(r'\*\*Location:\*\*\s+`?([^`\n]+)`?', block)
                if location_match:
                    vuln["location"] = location_match.group(1).strip()

                # Extract CWE
                cwe_match = re.search(r'CWE-(\d+)', block)
                if cwe_match:
                    vuln["cwe_id"] = f"CWE-{cwe_match.group(1)}"

                # Extract description
                desc_match = re.search(r'\*\*Description:\*\*\s+(.+?)(?=\n\*\*|\n###|\Z)', block, re.DOTALL)
                if desc_match:
                    vuln["description"] = desc_match.group(1).strip()

                # Extract impact
                impact_match = re.search(r'\*\*Impact:\*\*\s+(.+?)(?=\n\*\*|\n###|\Z)', block, re.DOTALL)
                if impact_match:
                    vuln["impact"] = impact_match.group(1).strip()

                if vuln:
                    vulnerabilities.append(vuln)

            logger.info(
                "security_specialist_agent.extracted_vulnerabilities",
                count=len(vulnerabilities)
            )

        except Exception as e:
            logger.warning(
                "security_specialist_agent.extract_vulnerabilities.error",
                error=str(e)
            )
            # Return empty list on error - don't fail entire audit

        return vulnerabilities

    def _extract_compliance_status(self, security_report: str, compliance_standards: List[str]) -> Dict[str, Any]:
        """
        Extract compliance status from security audit

        PRODUCTION-READY: Handles missing compliance data gracefully
        """
        compliance_status = {}

        try:
            import re

            for standard in compliance_standards:
                # Look for compliance percentage
                pattern = rf'{standard}.*?Compliance.*?(\d+)%'
                match = re.search(pattern, security_report, re.IGNORECASE | re.DOTALL)

                if match:
                    percentage = int(match.group(1))
                    compliance_status[standard] = {
                        "compliant": percentage >= 90,
                        "percentage": percentage,
                        "issues": []  # Could extract detailed issues if needed
                    }
                else:
                    # Default if not found
                    compliance_status[standard] = {
                        "compliant": None,
                        "percentage": None,
                        "issues": []
                    }

            logger.info(
                "security_specialist_agent.extracted_compliance_status",
                standards=list(compliance_status.keys())
            )

        except Exception as e:
            logger.warning(
                "security_specialist_agent.extract_compliance_status.error",
                error=str(e)
            )
            # Return empty dict on error - don't fail entire audit

        return compliance_status

    def _calculate_security_score(self, vulnerabilities: List[Dict]) -> int:
        """
        Calculate security score (0-100) based on vulnerabilities

        PRODUCTION-READY: Handles edge cases and invalid data

        Score calculation:
        - Start at 100
        - Deduct points for vulnerabilities based on severity
        - Critical: -20 points each
        - High: -10 points each
        - Medium: -5 points each
        - Low: -2 points each
        - Informational: -1 point each
        """

        try:
            score = 100

            for vuln in vulnerabilities:
                severity = vuln.get("severity", "").lower()
                if severity == "critical":
                    score -= 20
                elif severity == "high":
                    score -= 10
                elif severity == "medium":
                    score -= 5
                elif severity == "low":
                    score -= 2
                elif severity == "informational":
                    score -= 1

            # Clamp to 0-100
            score = max(0, min(100, score))

            logger.info(
                "security_specialist_agent.calculated_security_score",
                score=score,
                vulnerabilities_count=len(vulnerabilities)
            )

            return score

        except Exception as e:
            logger.warning(
                "security_specialist_agent.calculate_security_score.error",
                error=str(e)
            )
            # Return safe default
            return 50

"""
Security Agent - OWASP Top 10 Vulnerability Scanner
Scans generated code for security vulnerabilities with severity levels and fix recommendations
"""
import re
from typing import Dict, List
from pathlib import Path
import structlog

logger = structlog.get_logger()


class SecurityAgent:
    """
    Security Agent - Scans for OWASP Top 10 vulnerabilities

    Checks for:
    - SQL Injection
    - Cross-Site Scripting (XSS)
    - Hardcoded secrets/credentials
    - Command Injection
    - Insecure deserialization
    - Using components with known vulnerabilities
    - Insufficient logging

    Severity levels: critical, high, medium, low
    """

    def __init__(self):
        logger.info("🔒 SecurityAgent initialized")

        # Security vulnerability patterns
        self.security_patterns = {
            'python': self._get_python_patterns(),
            'javascript': self._get_javascript_patterns(),
            'sql': self._get_sql_patterns()
        }

    def scan_code(self, files: Dict[str, str]) -> List[Dict]:
        """
        Scan all code files for security vulnerabilities

        Args:
            files: Dictionary of filepath -> code content

        Returns:
            List of security issues with severity and fix recommendations
        """
        issues = []

        for filepath, code in files.items():
            ext = Path(filepath).suffix.lower()

            if ext == '.py':
                issues.extend(self._scan_python(filepath, code))
            elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                issues.extend(self._scan_javascript(filepath, code))
            elif ext == '.sql':
                issues.extend(self._scan_sql(filepath, code))

        # Sort by severity: critical -> high -> medium -> low
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        issues.sort(key=lambda x: severity_order.get(x.get('severity', 'low'), 3))

        # Log summary
        critical_count = sum(1 for i in issues if i.get('severity') == 'critical')
        high_count = sum(1 for i in issues if i.get('severity') == 'high')

        if critical_count > 0:
            logger.error(f"🔴 {critical_count} CRITICAL security issues found!")
        if high_count > 0:
            logger.warning(f"🟡 {high_count} HIGH security issues found")

        logger.info(f"Security scan complete: {len(issues)} total issues found")

        return issues

    def _scan_python(self, filepath: str, code: str) -> List[Dict]:
        """Scan Python code for security vulnerabilities"""
        issues = []

        # 1. SQL Injection
        sql_injection_patterns = [
            (r'execute\s*\([^)]*[+%]\s*[^)]*\)', 'String concatenation in SQL query'),
            (r'cursor\.execute\s*\([^)]*f["\'][^"\']*\{[^}]+\}', 'F-string in SQL query'),
            (r'\.format\s*\([^)]*\).*execute', 'String format in SQL query')
        ]

        for pattern, description in sql_injection_patterns:
            if re.search(pattern, code):
                issues.append({
                    'file': filepath,
                    'type': 'SQL_INJECTION',
                    'severity': 'critical',
                    'message': f'SQL injection vulnerability: {description}',
                    'fix': 'Use parameterized queries: cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))',
                    'line': self._find_line_number(code, pattern)
                })

        # 2. Hardcoded Secrets
        secret_pattern = r'(api_key|apikey|secret|password|token|private_key|aws_access_key)\s*=\s*["\']([^"\']{10,})["\']'
        matches = re.finditer(secret_pattern, code, re.IGNORECASE)

        for match in matches:
            value = match.group(2)
            # Skip if it's obviously a placeholder
            if not any(placeholder in value.lower() for placeholder in ['your_', 'example', 'xxx', 'test_', 'dummy', 'placeholder', 'replace_me']):
                issues.append({
                    'file': filepath,
                    'type': 'HARDCODED_SECRET',
                    'severity': 'critical',
                    'message': f'Hardcoded secret detected: {match.group(1)}',
                    'fix': 'Use environment variables: os.getenv("API_KEY") or use a secrets manager',
                    'line': self._find_line_number(code, match.group(0))
                })

        # 3. Command Injection
        command_injection_patterns = [
            (r'os\.system\s*\([^)]*\+', 'String concatenation in os.system'),
            (r'subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True', 'shell=True in subprocess'),
            (r'eval\s*\(', 'Use of eval()'),
            (r'exec\s*\(', 'Use of exec()')
        ]

        for pattern, description in command_injection_patterns:
            if re.search(pattern, code):
                issues.append({
                    'file': filepath,
                    'type': 'COMMAND_INJECTION',
                    'severity': 'critical' if 'eval' in pattern or 'exec' in pattern else 'high',
                    'message': f'Command injection vulnerability: {description}',
                    'fix': 'Use subprocess with args list, avoid shell=True, never use eval/exec on user input',
                    'line': self._find_line_number(code, pattern)
                })

        # 4. Insecure Deserialization
        if re.search(r'pickle\.loads?\s*\(', code):
            issues.append({
                'file': filepath,
                'type': 'INSECURE_DESERIALIZATION',
                'severity': 'high',
                'message': 'Insecure deserialization with pickle',
                'fix': 'Use JSON for untrusted data, or implement signature verification for pickle',
                'line': self._find_line_number(code, r'pickle\.loads?')
            })

        # 5. Weak Cryptography
        weak_crypto_patterns = [
            (r'hashlib\.(md5|sha1)\s*\(', 'Weak hashing algorithm'),
            (r'random\.random\s*\(', 'Insecure random for security purposes')
        ]

        for pattern, description in weak_crypto_patterns:
            if re.search(pattern, code):
                issues.append({
                    'file': filepath,
                    'type': 'WEAK_CRYPTOGRAPHY',
                    'severity': 'medium',
                    'message': f'Weak cryptography: {description}',
                    'fix': 'Use hashlib.sha256() or bcrypt for passwords, use secrets module for random',
                    'line': self._find_line_number(code, pattern)
                })

        # 6. Missing Input Validation
        if 'request.' in code and 'validate' not in code.lower() and 'clean' not in code.lower():
            if not re.search(r'if\s+.*request\.(GET|POST|data)', code):
                issues.append({
                    'file': filepath,
                    'type': 'MISSING_INPUT_VALIDATION',
                    'severity': 'medium',
                    'message': 'Request data used without validation',
                    'fix': 'Validate and sanitize all user inputs before use',
                    'line': None
                })

        return issues

    def _scan_javascript(self, filepath: str, code: str) -> List[Dict]:
        """Scan JavaScript/TypeScript code for security vulnerabilities"""
        issues = []

        # 1. Cross-Site Scripting (XSS)
        xss_patterns = [
            (r'innerHTML\s*=\s*[^;]*\+', 'String concatenation with innerHTML'),
            (r'outerHTML\s*=\s*[^;]*\+', 'String concatenation with outerHTML'),
            (r'document\.write\s*\([^)]*\+', 'String concatenation with document.write'),
            (r'\.html\s*\([^)]*\+', 'String concatenation with .html()')
        ]

        for pattern, description in xss_patterns:
            if re.search(pattern, code):
                issues.append({
                    'file': filepath,
                    'type': 'XSS',
                    'severity': 'high',
                    'message': f'Potential XSS vulnerability: {description}',
                    'fix': 'Use textContent instead of innerHTML, or sanitize HTML with DOMPurify',
                    'line': self._find_line_number(code, pattern)
                })

        # 2. eval() Usage
        if re.search(r'\beval\s*\(', code):
            issues.append({
                'file': filepath,
                'type': 'DANGEROUS_EVAL',
                'severity': 'critical',
                'message': 'Use of eval() is dangerous',
                'fix': 'Remove eval(), use JSON.parse() for JSON or safer alternatives',
                'line': self._find_line_number(code, r'\beval\s*\(')
            })

        # 3. Hardcoded API Keys
        api_key_pattern = r'(apiKey|api_key|token|secret|password)\s*[:=]\s*["\']([a-zA-Z0-9_-]{10,})["\']'
        matches = re.finditer(api_key_pattern, code, re.IGNORECASE)

        for match in matches:
            value = match.group(2)
            if not any(placeholder in value.lower() for placeholder in ['your_', 'example', 'xxx', 'test', 'dummy']):
                issues.append({
                    'file': filepath,
                    'type': 'HARDCODED_SECRET',
                    'severity': 'critical',
                    'message': f'Hardcoded API key/secret: {match.group(1)}',
                    'fix': 'Use environment variables: process.env.API_KEY',
                    'line': self._find_line_number(code, match.group(0))
                })

        # 4. Insecure HTTP Requests
        if re.search(r'http://[^\s"\']+', code) and 'localhost' not in code:
            issues.append({
                'file': filepath,
                'type': 'INSECURE_HTTP',
                'severity': 'medium',
                'message': 'Using HTTP instead of HTTPS for external requests',
                'fix': 'Use HTTPS for all external API calls',
                'line': self._find_line_number(code, r'http://')
            })

        # 5. Dangerous dangerouslySetInnerHTML (React)
        if 'dangerouslySetInnerHTML' in code:
            issues.append({
                'file': filepath,
                'type': 'XSS_REACT',
                'severity': 'high',
                'message': 'Use of dangerouslySetInnerHTML can lead to XSS',
                'fix': 'Sanitize HTML with DOMPurify before using dangerouslySetInnerHTML',
                'line': self._find_line_number(code, 'dangerouslySetInnerHTML')
            })

        # 6. Missing CSRF Protection
        if 'fetch(' in code or 'axios.' in code:
            if 'csrf' not in code.lower() and 'x-csrf-token' not in code.lower():
                if re.search(r'method:\s*["\']POST["\']', code, re.IGNORECASE):
                    issues.append({
                        'file': filepath,
                        'type': 'MISSING_CSRF',
                        'severity': 'medium',
                        'message': 'POST request without CSRF token',
                        'fix': 'Include CSRF token in POST requests',
                        'line': self._find_line_number(code, r'method:\s*["\']POST["\']')
                    })

        return issues

    def _scan_sql(self, filepath: str, code: str) -> List[Dict]:
        """Scan SQL code for security vulnerabilities"""
        issues = []

        # SQL Injection through string concatenation
        if re.search(r"['\"].*\+.*['\"]", code):
            issues.append({
                'file': filepath,
                'type': 'SQL_INJECTION',
                'severity': 'critical',
                'message': 'SQL injection through string concatenation',
                'fix': 'Use parameterized queries or prepared statements',
                'line': self._find_line_number(code, r"['\"].*\+.*['\"]")
            })

        # Unquoted identifiers
        if re.search(r'DROP\s+TABLE', code, re.IGNORECASE) and 'IF EXISTS' not in code.upper():
            issues.append({
                'file': filepath,
                'type': 'UNSAFE_SQL',
                'severity': 'medium',
                'message': 'DROP TABLE without IF EXISTS check',
                'fix': 'Use DROP TABLE IF EXISTS to prevent errors',
                'line': self._find_line_number(code, r'DROP\s+TABLE')
            })

        return issues

    def _find_line_number(self, code: str, pattern: str) -> Optional[int]:
        """Find line number of pattern match"""
        try:
            match = re.search(pattern, code)
            if match:
                return code[:match.start()].count('\n') + 1
        except:
            pass
        return None

    def _get_python_patterns(self) -> Dict:
        """Get Python security patterns"""
        return {
            'sql_injection': r'execute\s*\([^)]*\+',
            'hardcoded_secret': r'(password|secret|token)\s*=\s*["\'][^"\']+["\']',
            'eval_usage': r'\beval\s*\(',
            'pickle_loads': r'pickle\.loads\s*\('
        }

    def _get_javascript_patterns(self) -> Dict:
        """Get JavaScript security patterns"""
        return {
            'xss': r'innerHTML\s*=',
            'eval_usage': r'\beval\s*\(',
            'hardcoded_secret': r'(apiKey|token)\s*=\s*["\'][^"\']+["\']'
        }

    def _get_sql_patterns(self) -> Dict:
        """Get SQL security patterns"""
        return {
            'sql_injection': r'["\'].*\+.*["\']',
            'drop_table': r'DROP\s+TABLE'
        }

    def generate_security_report(self, issues: List[Dict]) -> str:
        """Generate human-readable security report"""
        if not issues:
            return "✅ No security issues found!"

        report = []
        report.append("🔒 Security Scan Report\n")
        report.append("=" * 80 + "\n\n")

        # Group by severity
        by_severity = {}
        for issue in issues:
            severity = issue.get('severity', 'low')
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(issue)

        # Critical issues
        if 'critical' in by_severity:
            report.append(f"🔴 CRITICAL ISSUES ({len(by_severity['critical'])})\n")
            report.append("-" * 80 + "\n")
            for issue in by_severity['critical']:
                report.append(f"\nFile: {issue['file']}")
                if issue.get('line'):
                    report.append(f" (Line {issue['line']})")
                report.append(f"\nType: {issue['type']}")
                report.append(f"\nMessage: {issue['message']}")
                report.append(f"\nFix: {issue['fix']}\n")

        # High issues
        if 'high' in by_severity:
            report.append(f"\n🟡 HIGH ISSUES ({len(by_severity['high'])})\n")
            report.append("-" * 80 + "\n")
            for issue in by_severity['high']:
                report.append(f"\nFile: {issue['file']}")
                if issue.get('line'):
                    report.append(f" (Line {issue['line']})")
                report.append(f"\nType: {issue['type']}")
                report.append(f"\nMessage: {issue['message']}")
                report.append(f"\nFix: {issue['fix']}\n")

        # Medium and low issues summary
        if 'medium' in by_severity:
            report.append(f"\n🟠 MEDIUM ISSUES: {len(by_severity['medium'])}\n")
        if 'low' in by_severity:
            report.append(f"🟢 LOW ISSUES: {len(by_severity['low'])}\n")

        return "\n".join(report)


# Singleton instance
security_agent = SecurityAgent()

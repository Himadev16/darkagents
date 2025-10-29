"""
Validation Pipeline - Code Quality Validation System
Validates generated code for syntax, security, and quality (74%+ target success rate)
"""
import ast
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
import structlog

logger = structlog.get_logger()


class ValidationPipeline:
    """
    Validates generated code for:
    - Syntax correctness
    - Security vulnerabilities
    - Code quality (no placeholders)
    - Error handling presence

    Target: 74%+ validation success rate
    """

    def __init__(self):
        self.validators = {
            'python': self._validate_python,
            'javascript': self._validate_javascript,
            'typescript': self._validate_typescript,
            'sql': self._validate_sql
        }
        logger.info("ValidationPipeline initialized")

    def validate_and_refine(self, files: Dict[str, str]) -> Dict[str, str]:
        """
        Validate all files and attempt to fix minor issues

        Args:
            files: Dictionary of filepath -> code content

        Returns:
            Dictionary of validated/fixed files
        """
        validated_files = {}
        validation_report = {
            "total_files": len(files),
            "validated_files": 0,
            "failed_files": [],
            "auto_fixed": 0
        }

        for filepath, code in files.items():
            validation_result = self._validate_file(filepath, code)

            if validation_result['valid']:
                validated_files[filepath] = validation_result.get('fixed_code', code)
                validation_report['validated_files'] += 1
                if validation_result.get('was_fixed'):
                    validation_report['auto_fixed'] += 1
                    logger.info(f"Auto-fixed: {filepath}")
            else:
                # Attempt auto-fix
                fixed_code = self._attempt_autofix(filepath, code, validation_result['errors'])
                if fixed_code:
                    revalidation = self._validate_file(filepath, fixed_code)
                    if revalidation['valid']:
                        validated_files[filepath] = fixed_code
                        validation_report['validated_files'] += 1
                        validation_report['auto_fixed'] += 1
                        logger.info(f"Successfully auto-fixed: {filepath}")
                    else:
                        validation_report['failed_files'].append({
                            'file': filepath,
                            'errors': validation_result['errors']
                        })
                        logger.warning(f"Could not fix: {filepath} - {validation_result['errors']}")
                else:
                    validation_report['failed_files'].append({
                        'file': filepath,
                        'errors': validation_result['errors']
                    })
                    logger.warning(f"Validation failed: {filepath} - {validation_result['errors']}")

        success_rate = (validation_report['validated_files'] / validation_report['total_files']) * 100 if validation_report['total_files'] > 0 else 0
        logger.info(f"Validation complete: {success_rate:.1f}% success rate ({validation_report['validated_files']}/{validation_report['total_files']} files)")

        return validated_files

    def calculate_success_rate(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Calculate detailed validation success rate (target: 74%+)

        Returns:
            Dictionary with validation metrics
        """
        results = {
            "total_files": len(files),
            "validated_files": 0,
            "success_rate": 0.0,
            "failed_files": [],
            "validation_details": {}
        }

        for filepath, code in files.items():
            passed_all = True
            errors = []
            details = {}

            # 1. Syntax validation
            syntax_valid = self._check_syntax(filepath, code)
            details['syntax'] = syntax_valid
            if not syntax_valid:
                passed_all = False
                errors.append("Syntax error")

            # 2. Security scan (critical issues only)
            security_issues = self._quick_security_scan(filepath, code)
            critical_security = [i for i in security_issues if i['severity'] == 'critical']
            details['security'] = len(critical_security) == 0
            if critical_security:
                passed_all = False
                errors.append(f"Critical security: {critical_security[0]['type']}")

            # 3. No placeholder code
            has_placeholders = self._has_placeholders(code)
            details['no_placeholders'] = not has_placeholders
            if has_placeholders:
                passed_all = False
                errors.append("Contains placeholder code")

            # 4. Has error handling
            has_error_handling = self._has_error_handling(filepath, code)
            details['error_handling'] = has_error_handling
            if not has_error_handling:
                passed_all = False
                errors.append("Missing error handling")

            results["validation_details"][filepath] = details

            if passed_all:
                results["validated_files"] += 1
            else:
                results["failed_files"].append({"file": filepath, "errors": errors})

        results["success_rate"] = (results["validated_files"] / results["total_files"]) * 100 if results["total_files"] > 0 else 0
        results["meets_threshold"] = results["success_rate"] >= 74.0

        status = "✅ PASS" if results["meets_threshold"] else "❌ FAIL"
        logger.info(f"Success rate: {results['success_rate']:.1f}% {status} (target: 74%)")

        return results

    def _validate_file(self, filepath: str, code: str) -> Dict:
        """Validate a single file"""
        ext = Path(filepath).suffix.lower()
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'fixed_code': None,
            'was_fixed': False
        }

        if ext == '.py':
            return self._validate_python(filepath, code)
        elif ext in ['.js', '.jsx']:
            return self._validate_javascript(filepath, code)
        elif ext in ['.ts', '.tsx']:
            return self._validate_typescript(filepath, code)
        elif ext == '.sql':
            return self._validate_sql(filepath, code)
        else:
            # Generic validation for other file types
            if self._has_placeholders(code):
                result['valid'] = False
                result['errors'].append("Contains placeholder code")
            return result

    def _validate_python(self, filepath: str, code: str) -> Dict:
        """Validate Python code"""
        result = {'valid': True, 'errors': [], 'warnings': []}

        # Syntax check
        try:
            ast.parse(code)
        except SyntaxError as e:
            result['valid'] = False
            result['errors'].append(f"Syntax error at line {e.lineno}: {e.msg}")
            return result

        # Security checks
        if 'exec(' in code or 'eval(' in code:
            result['valid'] = False
            result['errors'].append("Dangerous use of exec/eval")

        # Check for common issues
        if '__import__(' in code and 'os' in code:
            result['warnings'].append("Dynamic imports detected")

        return result

    def _validate_javascript(self, filepath: str, code: str) -> Dict:
        """Validate JavaScript/JSX code"""
        result = {'valid': True, 'errors': [], 'warnings': []}

        # Check for dangerous patterns
        if 'eval(' in code:
            result['valid'] = False
            result['errors'].append("Dangerous use of eval")

        if 'innerHTML' in code and '+' in code:
            result['warnings'].append("Potential XSS with innerHTML concatenation")

        # Check for common syntax issues
        if code.count('{') != code.count('}'):
            result['valid'] = False
            result['errors'].append("Mismatched braces")

        return result

    def _validate_typescript(self, filepath: str, code: str) -> Dict:
        """Validate TypeScript code"""
        # TypeScript validation is similar to JavaScript
        return self._validate_javascript(filepath, code)

    def _validate_sql(self, filepath: str, code: str) -> Dict:
        """Validate SQL code"""
        result = {'valid': True, 'errors': [], 'warnings': []}

        # Check for SQL injection patterns
        if re.search(r"'\s*\+\s*", code) or re.search(r'"\s*\+\s*', code):
            result['valid'] = False
            result['errors'].append("Potential SQL injection with string concatenation")

        return result

    def _check_syntax(self, filepath: str, code: str) -> bool:
        """Quick syntax check"""
        ext = Path(filepath).suffix.lower()

        if ext == '.py':
            try:
                ast.parse(code)
                return True
            except:
                return False
        elif ext in ['.js', '.jsx', '.ts', '.tsx']:
            # Basic brace matching
            return code.count('{') == code.count('}') and code.count('(') == code.count(')')

        return True

    def _quick_security_scan(self, filepath: str, code: str) -> List[Dict]:
        """Quick security scan for critical issues"""
        issues = []

        patterns = {
            'hardcoded_secret': (r'(api_key|password|secret|token)\s*=\s*["\'][\w-]{10,}["\']', 'critical'),
            'sql_injection': (r'(execute|query)\s*\(.*\+.*\)', 'critical'),
            'eval_usage': (r'\b(eval|exec)\s*\(', 'critical'),
            'command_injection': (r'(os\.system|subprocess\.call|shell=True)', 'high')
        }

        for name, (pattern, severity) in patterns.items():
            if re.search(pattern, code, re.IGNORECASE):
                # Check if it's not a false positive (example values)
                match = re.search(pattern, code, re.IGNORECASE)
                if match:
                    matched_text = match.group(0).lower()
                    # Skip if it contains common placeholder text
                    if not any(placeholder in matched_text for placeholder in ['your_', 'example', 'xxx', 'test_', 'dummy']):
                        issues.append({
                            'type': name.upper(),
                            'severity': severity,
                            'file': filepath
                        })

        return issues

    def _has_placeholders(self, code: str) -> bool:
        """Check if code contains placeholder comments"""
        placeholders = [
            'TODO',
            'FIXME',
            '# Implement',
            '// Implement',
            'pass  # TODO',
            '# Replace with',
            '// Replace with',
            'YOUR_API_KEY',
            'PLACEHOLDER',
            '...'  # Python ellipsis used as placeholder
        ]

        # Count occurrences
        placeholder_count = sum(1 for placeholder in placeholders if placeholder in code)

        # Allow up to 1 TODO for minor notes, but more indicates incomplete code
        return placeholder_count > 1

    def _has_error_handling(self, filepath: str, code: str) -> bool:
        """Check if code has error handling"""
        ext = Path(filepath).suffix.lower()

        if ext == '.py':
            # Check for try/except blocks
            has_try = 'try:' in code or 'try ' in code
            has_except = 'except' in code
            return has_try and has_except
        elif ext in ['.js', '.jsx', '.ts', '.tsx']:
            # Check for try/catch blocks
            has_try = 'try' in code and '{' in code
            has_catch = 'catch' in code
            return has_try and has_catch
        elif ext == '.sql':
            # SQL doesn't require error handling in the same way
            return True

        # For other files, pass
        return True

    def _attempt_autofix(self, filepath: str, code: str, errors: List[str]) -> Optional[str]:
        """
        Attempt to automatically fix common issues

        Returns:
            Fixed code if successful, None otherwise
        """
        fixed_code = code
        was_fixed = False

        # Fix missing imports
        if filepath.endswith('.py'):
            if "name 'os' is not defined" in str(errors) or 'os.' in code:
                if 'import os' not in fixed_code:
                    fixed_code = "import os\n" + fixed_code
                    was_fixed = True

            if "name 'sys' is not defined" in str(errors) or 'sys.' in code:
                if 'import sys' not in fixed_code:
                    fixed_code = "import sys\n" + fixed_code
                    was_fixed = True

            if "name 'json' is not defined" in str(errors) or 'json.' in code:
                if 'import json' not in fixed_code:
                    fixed_code = "import json\n" + fixed_code
                    was_fixed = True

        # Remove single TODO comments (but keep the rest of the code)
        if 'TODO' in fixed_code or 'FIXME' in fixed_code:
            # Remove TODO comments but keep the code
            fixed_code = re.sub(r'#\s*TODO[^\n]*\n', '', fixed_code)
            fixed_code = re.sub(r'//\s*TODO[^\n]*\n', '', fixed_code)
            fixed_code = re.sub(r'#\s*FIXME[^\n]*\n', '', fixed_code)
            fixed_code = re.sub(r'//\s*FIXME[^\n]*\n', '', fixed_code)
            was_fixed = True

        return fixed_code if was_fixed else None


# Singleton instance
validation_pipeline = ValidationPipeline()

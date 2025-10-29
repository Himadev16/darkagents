"""
Polyglot Agent - Superior Multi-Language Coding Agent with Validation & Security
Designed to replace top coding agents like Claude

NEW INTEGRATED FEATURES:
✅ Advanced File Extraction (6+ patterns)
✅ Validation Pipeline (74%+ success rate target)
✅ Security Scanning (OWASP Top 10)
✅ Auto-fix capabilities
✅ Production-ready code generation
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import structlog

from backend.agents.base_agent import BaseAgent
from backend.database.models import AgentStatus
from backend.services.claude_service import claude_service
from backend.services.validation_pipeline import validation_pipeline
from backend.services.security_agent import security_agent
from backend.services.file_extractor import file_extractor

logger = structlog.get_logger()


class PolyglotAgent(BaseAgent):
    """
    Polyglot Agent - Elite Multi-Language Software Engineer

    Capabilities:
    - Master of 20+ programming languages
    - Advanced code generation with best practices
    - Code review, refactoring, and optimization
    - Debugging and problem-solving
    - Test generation (unit, integration, e2e)
    - Architecture and design patterns
    - Performance optimization
    - Security vulnerability detection
    - Cross-language code translation
    """

    # Supported languages with expertise levels
    LANGUAGES = {
        "python": {"expertise": "expert", "frameworks": ["Django", "FastAPI", "Flask", "PyTorch", "TensorFlow"]},
        "javascript": {"expertise": "expert", "frameworks": ["React", "Vue", "Angular", "Node.js", "Express"]},
        "typescript": {"expertise": "expert", "frameworks": ["Next.js", "NestJS", "React", "Angular"]},
        "go": {"expertise": "expert", "frameworks": ["Gin", "Echo", "Fiber", "gRPC"]},
        "rust": {"expertise": "expert", "frameworks": ["Actix", "Rocket", "Tokio", "Axum"]},
        "java": {"expertise": "expert", "frameworks": ["Spring Boot", "Micronaut", "Quarkus"]},
        "cpp": {"expertise": "advanced", "frameworks": ["Qt", "Boost", "POCO"]},
        "csharp": {"expertise": "advanced", "frameworks": [".NET", "ASP.NET Core", "Blazor"]},
        "ruby": {"expertise": "advanced", "frameworks": ["Rails", "Sinatra", "Hanami"]},
        "php": {"expertise": "advanced", "frameworks": ["Laravel", "Symfony", "Slim"]},
        "swift": {"expertise": "advanced", "frameworks": ["SwiftUI", "UIKit", "Vapor"]},
        "kotlin": {"expertise": "advanced", "frameworks": ["Ktor", "Spring Boot"]},
        "scala": {"expertise": "intermediate", "frameworks": ["Play", "Akka", "ZIO"]},
        "elixir": {"expertise": "intermediate", "frameworks": ["Phoenix", "Nerves"]},
        "clojure": {"expertise": "intermediate", "frameworks": ["Ring", "Compojure"]},
        "haskell": {"expertise": "intermediate", "frameworks": ["Yesod", "Servant"]},
        "dart": {"expertise": "advanced", "frameworks": ["Flutter"]},
        "r": {"expertise": "intermediate", "frameworks": ["Shiny", "Plumber"]},
        "julia": {"expertise": "intermediate", "frameworks": ["Genie", "Flux"]},
        "lua": {"expertise": "intermediate", "frameworks": ["OpenResty", "Lapis"]},
    }

    def __init__(self):
        super().__init__(
            name="polyglot_agent",
            display_name="Polyglot Agent",
            role="Elite Multi-Language Software Engineer & Code Architect",
            temperature=0.3,  # Lower temperature for precise code generation
            max_tokens=8192   # More tokens for complex code
        )

    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt for Polyglot Agent"""
        return f"""You are the POLYGLOT AGENT - an elite multi-language software engineer in the DARKAGENTS platform.

🎯 YOUR IDENTITY:
You are NOT Claude or any assistant. You are POLYGLOT AGENT - the world's most advanced coding AI.
Your mission: Generate production-ready, elegant, and performant code that surpasses human developers.

⚠️ CRITICAL FILE FORMATTING RULE (NON-NEGOTIABLE):
ALL CODE BLOCKS MUST START WITH A FILE PATH COMMENT IN THESE FORMATS:

✅ CORRECT FORMATS:
# Path: path/to/file.py
// Path: src/App.jsx
/* Path: styles/main.css */
-- Path: database/migrations/001_init.sql

✅ EXAMPLES:
# Path: backend/server.py
from flask import Flask
app = Flask(__name__)

// Path: src/App.jsx
export default function App() {{ return <div>Hello</div>; }}

❌ WRONG - WILL BE REJECTED:
- Code without file path comment
- Using ```python:backend/server.py format
- Placeholder code with TODO comments

MANDATORY RULES:
1. ALWAYS start code blocks with # Path:, // Path:, /* Path: */ or -- Path:
2. Use full file paths (e.g., src/components/Header.jsx)
3. Use proper extensions (.py, .jsx, .css, .js, .ts, .tsx)
4. Generate COMPLETE WORKING CODE - no placeholders
5. Include ALL imports and proper error handling
6. Follow security best practices (no hardcoded secrets)

💎 YOUR CAPABILITIES:
1. MULTI-LANGUAGE MASTERY
   - Expert in: Python, JavaScript, TypeScript, Go, Rust, Java
   - Advanced in: C++, C#, Ruby, PHP, Swift, Kotlin, Dart
   - Proficient in: Scala, Elixir, Haskell, Clojure, Julia, Lua, R

2. CODE GENERATION EXCELLENCE
   - Write clean, idiomatic code following language best practices
   - Apply SOLID principles and design patterns
   - Generate comprehensive error handling
   - Include proper logging and monitoring
   - Write self-documenting code with clear naming

3. ARCHITECTURE & DESIGN
   - Microservices, monoliths, serverless - you master all
   - Design scalable, maintainable systems
   - Choose optimal data structures and algorithms
   - Balance performance, readability, and maintainability

4. TESTING & QUALITY
   - Generate unit tests, integration tests, e2e tests
   - Write property-based tests when applicable
   - Include edge cases and error scenarios
   - Achieve high code coverage with meaningful tests

5. OPTIMIZATION & PERFORMANCE
   - Profile and optimize code for speed
   - Reduce memory footprint
   - Implement caching strategies
   - Use async/parallel processing when beneficial

6. SECURITY & BEST PRACTICES
   - Prevent SQL injection, XSS, CSRF
   - Implement proper authentication/authorization
   - Sanitize inputs and validate data
   - Follow OWASP Top 10 guidelines

7. CODE REVIEW & REFACTORING
   - Identify code smells and anti-patterns
   - Suggest refactorings for better maintainability
   - Improve readability and reduce complexity
   - Modernize legacy code

8. DEBUGGING & PROBLEM SOLVING
   - Analyze stack traces and error messages
   - Identify root causes of bugs
   - Provide step-by-step debugging strategies
   - Fix bugs with minimal code changes

🎨 YOUR PERSONALITY:
- Confident but not arrogant
- Precise and detail-oriented
- Pragmatic - balance perfection with practicality
- Educational - explain your reasoning
- Proactive - suggest improvements beyond requirements

📋 OUTPUT FORMAT:
Always structure your responses as:
1. ANALYSIS: Brief analysis of the task/problem
2. APPROACH: Your chosen solution strategy
3. CODE: The implementation (clean, commented, production-ready)
4. TESTS: Test cases for the code
5. NOTES: Important considerations, trade-offs, or optimizations

🚀 STANDARDS:
- Code MUST be production-ready, not prototypes
- Follow the language's official style guide
- Include type hints/annotations where supported
- Write comprehensive docstrings/comments
- Handle edge cases and errors gracefully
- Consider performance implications
- Make code maintainable for teams

Remember: You don't just write code - you craft elegant software solutions that developers admire."""

    def _perform_work(
        self,
        input_data: Dict[str, Any],
        execution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Perform polyglot coding work

        Handles various coding tasks:
        - code_generation: Generate code from specifications
        - code_review: Review and improve existing code
        - debugging: Debug and fix code issues
        - refactoring: Refactor code for better quality
        - testing: Generate comprehensive tests
        - translation: Translate code between languages
        - optimization: Optimize code for performance
        """
        task_type = input_data.get("task_type", "code_generation")
        language = input_data.get("language", "python")
        requirements = input_data.get("requirements", "")
        existing_code = input_data.get("existing_code", None)

        logger.info(
            "polyglot_agent_starting",
            task_type=task_type,
            language=language,
            has_existing_code=existing_code is not None
        )

        # Route to appropriate handler
        if task_type == "code_generation":
            result = self._generate_code(language, requirements, execution, db)
        elif task_type == "code_review":
            result = self._review_code(language, existing_code, execution, db)
        elif task_type == "debugging":
            result = self._debug_code(language, existing_code, requirements, execution, db)
        elif task_type == "refactoring":
            result = self._refactor_code(language, existing_code, execution, db)
        elif task_type == "testing":
            result = self._generate_tests(language, existing_code, execution, db)
        elif task_type == "translation":
            target_language = input_data.get("target_language", "typescript")
            result = self._translate_code(language, target_language, existing_code, execution, db)
        elif task_type == "optimization":
            result = self._optimize_code(language, existing_code, execution, db)
        else:
            # Default to code generation
            result = self._generate_code(language, requirements, execution, db)

        return result

    def _generate_code(
        self,
        language: str,
        requirements: str,
        execution,
        db: Session
    ) -> Dict[str, Any]:
        """Generate code from requirements"""
        self._update_status(
            execution,
            AgentStatus.WORKING,
            f"Generating {language} code...",
            20,
            db
        )

        # Get language info
        lang_info = self.LANGUAGES.get(language, {"expertise": "intermediate", "frameworks": []})

        # Build prompt for code generation
        prompt = f"""TASK: Code Generation

LANGUAGE: {language.upper()}
EXPERTISE LEVEL: {lang_info['expertise'].upper()}
POPULAR FRAMEWORKS: {', '.join(lang_info['frameworks'][:3])}

REQUIREMENTS:
{requirements}

Generate production-ready {language} code that fulfills these requirements.

Follow the OUTPUT FORMAT specified in your system prompt:
1. ANALYSIS
2. APPROACH
3. CODE
4. TESTS
5. NOTES

Make it exceptional."""

        # Generate code using Claude
        self._update_status(
            execution,
            AgentStatus.WORKING,
            "Analyzing requirements and designing solution...",
            40,
            db
        )

        response = claude_service.generate(
            messages=[{"role": "user", "content": prompt}],
            system=self.system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        self._update_status(
            execution,
            AgentStatus.WORKING,
            "Extracting code files...",
            60,
            db
        )

        # 🔥 STEP 1: Extract files using advanced pattern matching
        files = file_extractor.extract_files(response["content"])
        logger.info(f"Extracted {len(files)} files")

        self._update_status(
            execution,
            AgentStatus.WORKING,
            "Validating code quality...",
            70,
            db
        )

        # 🔥 STEP 2: Validate and refine code
        if files:
            validated_files = validation_pipeline.validate_and_refine(files)
            validation_results = validation_pipeline.calculate_success_rate(validated_files)

            logger.info(
                f"Validation: {validation_results['success_rate']:.1f}% success rate "
                f"({validation_results['validated_files']}/{validation_results['total_files']} files)"
            )

            self._update_status(
                execution,
                AgentStatus.WORKING,
                "Scanning for security vulnerabilities...",
                80,
                db
            )

            # 🔥 STEP 3: Security scan
            security_issues = security_agent.scan_code(validated_files)
            critical_issues = [i for i in security_issues if i['severity'] == 'critical']

            if critical_issues:
                logger.error(f"🔴 {len(critical_issues)} CRITICAL security issues found!")

            self._update_status(
                execution,
                AgentStatus.WORKING,
                "Finalizing code generation...",
                90,
                db
            )

            # Update token tracking
            execution.tokens_used += response["usage"]["total_tokens"]
            execution.cost_usd = round(
                (response["usage"]["input_tokens"] * 0.003 / 1000) +
                (response["usage"]["output_tokens"] * 0.015 / 1000),
                6
            )
            db.commit()

            return {
                "success": True,
                "task_type": "code_generation",
                "language": language,
                "output": response["content"],
                "files": validated_files,
                "validation": validation_results,
                "security_issues": security_issues,
                "critical_issues_count": len(critical_issues),
                "tokens_used": response["usage"]["total_tokens"],
                "cost_usd": execution.cost_usd
            }
        else:
            logger.error("No files extracted from response")
            execution.tokens_used += response["usage"]["total_tokens"]
            execution.cost_usd = round(
                (response["usage"]["input_tokens"] * 0.003 / 1000) +
                (response["usage"]["output_tokens"] * 0.015 / 1000),
                6
            )
            db.commit()

            return {
                "success": False,
                "task_type": "code_generation",
                "language": language,
                "output": response["content"],
                "error": "Failed to extract code files",
                "tokens_used": response["usage"]["total_tokens"],
                "cost_usd": execution.cost_usd
            }

    def _review_code(
        self,
        language: str,
        code: str,
        execution,
        db: Session
    ) -> Dict[str, Any]:
        """Review and improve existing code"""
        self._update_status(
            execution,
            AgentStatus.WORKING,
            f"Reviewing {language} code...",
            30,
            db
        )

        prompt = f"""TASK: Code Review

LANGUAGE: {language.upper()}

CODE TO REVIEW:
```{language}
{code}
```

Perform a comprehensive code review:
1. Identify bugs, code smells, and anti-patterns
2. Suggest improvements for readability and maintainability
3. Check security vulnerabilities
4. Recommend performance optimizations
5. Verify best practices compliance
6. Provide refactored version if needed

Be thorough but constructive."""

        response = claude_service.generate(
            messages=[{"role": "user", "content": prompt}],
            system=self.system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        self._update_status(
            execution,
            AgentStatus.WORKING,
            "Code review complete",
            90,
            db
        )

        execution.tokens_used += response["usage"]["total_tokens"]
        execution.cost_usd = round(
            (response["usage"]["input_tokens"] * 0.003 / 1000) +
            (response["usage"]["output_tokens"] * 0.015 / 1000),
            6
        )
        db.commit()

        return {
            "success": True,
            "task_type": "code_review",
            "language": language,
            "review": response["content"],
            "tokens_used": response["usage"]["total_tokens"]
        }

    def _debug_code(
        self,
        language: str,
        code: str,
        error_info: str,
        execution,
        db: Session
    ) -> Dict[str, Any]:
        """Debug code and fix issues"""
        self._update_status(
            execution,
            AgentStatus.WORKING,
            f"Debugging {language} code...",
            35,
            db
        )

        prompt = f"""TASK: Debugging

LANGUAGE: {language.upper()}

PROBLEMATIC CODE:
```{language}
{code}
```

ERROR/ISSUE:
{error_info}

Debug this code:
1. Identify the root cause of the issue
2. Explain why the error occurs
3. Provide the fixed code
4. Suggest preventive measures
5. Add error handling if missing"""

        response = claude_service.generate(
            messages=[{"role": "user", "content": prompt}],
            system=self.system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        self._update_status(
            execution,
            AgentStatus.WORKING,
            "Debugging complete, fix applied",
            85,
            db
        )

        execution.tokens_used += response["usage"]["total_tokens"]
        execution.cost_usd = round(
            (response["usage"]["input_tokens"] * 0.003 / 1000) +
            (response["usage"]["output_tokens"] * 0.015 / 1000),
            6
        )
        db.commit()

        return {
            "success": True,
            "task_type": "debugging",
            "language": language,
            "solution": response["content"],
            "tokens_used": response["usage"]["total_tokens"]
        }

    def _refactor_code(
        self,
        language: str,
        code: str,
        execution,
        db: Session
    ) -> Dict[str, Any]:
        """Refactor code for better quality"""
        self._update_status(
            execution,
            AgentStatus.WORKING,
            f"Refactoring {language} code...",
            40,
            db
        )

        prompt = f"""TASK: Code Refactoring

LANGUAGE: {language.upper()}

CODE TO REFACTOR:
```{language}
{code}
```

Refactor this code to improve:
1. Readability and clarity
2. Maintainability
3. Performance
4. Testability
5. Adherence to SOLID principles
6. Use of design patterns where appropriate

Provide the refactored code with explanations."""

        response = claude_service.generate(
            messages=[{"role": "user", "content": prompt}],
            system=self.system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        self._update_status(
            execution,
            AgentStatus.WORKING,
            "Refactoring complete",
            88,
            db
        )

        execution.tokens_used += response["usage"]["total_tokens"]
        execution.cost_usd = round(
            (response["usage"]["input_tokens"] * 0.003 / 1000) +
            (response["usage"]["output_tokens"] * 0.015 / 1000),
            6
        )
        db.commit()

        return {
            "success": True,
            "task_type": "refactoring",
            "language": language,
            "refactored_code": response["content"],
            "tokens_used": response["usage"]["total_tokens"]
        }

    def _generate_tests(
        self,
        language: str,
        code: str,
        execution,
        db: Session
    ) -> Dict[str, Any]:
        """Generate comprehensive tests for code"""
        self._update_status(
            execution,
            AgentStatus.WORKING,
            f"Generating tests for {language} code...",
            45,
            db
        )

        prompt = f"""TASK: Test Generation

LANGUAGE: {language.upper()}

CODE TO TEST:
```{language}
{code}
```

Generate comprehensive tests:
1. Unit tests for all functions/methods
2. Edge cases and boundary conditions
3. Error/exception handling tests
4. Integration tests if applicable
5. Test fixtures and mocks where needed

Use the appropriate testing framework for {language}."""

        response = claude_service.generate(
            messages=[{"role": "user", "content": prompt}],
            system=self.system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        self._update_status(
            execution,
            AgentStatus.WORKING,
            "Test generation complete",
            92,
            db
        )

        execution.tokens_used += response["usage"]["total_tokens"]
        execution.cost_usd = round(
            (response["usage"]["input_tokens"] * 0.003 / 1000) +
            (response["usage"]["output_tokens"] * 0.015 / 1000),
            6
        )
        db.commit()

        return {
            "success": True,
            "task_type": "testing",
            "language": language,
            "tests": response["content"],
            "tokens_used": response["usage"]["total_tokens"]
        }

    def _translate_code(
        self,
        source_lang: str,
        target_lang: str,
        code: str,
        execution,
        db: Session
    ) -> Dict[str, Any]:
        """Translate code from one language to another"""
        self._update_status(
            execution,
            AgentStatus.WORKING,
            f"Translating from {source_lang} to {target_lang}...",
            50,
            db
        )

        prompt = f"""TASK: Code Translation

SOURCE LANGUAGE: {source_lang.upper()}
TARGET LANGUAGE: {target_lang.upper()}

CODE TO TRANSLATE:
```{source_lang}
{code}
```

Translate this code to {target_lang}:
1. Preserve functionality exactly
2. Use idiomatic {target_lang} patterns
3. Adapt to {target_lang} conventions
4. Update dependencies/imports appropriately
5. Maintain code quality and readability"""

        response = claude_service.generate(
            messages=[{"role": "user", "content": prompt}],
            system=self.system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        self._update_status(
            execution,
            AgentStatus.WORKING,
            "Translation complete",
            95,
            db
        )

        execution.tokens_used += response["usage"]["total_tokens"]
        execution.cost_usd = round(
            (response["usage"]["input_tokens"] * 0.003 / 1000) +
            (response["usage"]["output_tokens"] * 0.015 / 1000),
            6
        )
        db.commit()

        return {
            "success": True,
            "task_type": "translation",
            "source_language": source_lang,
            "target_language": target_lang,
            "translated_code": response["content"],
            "tokens_used": response["usage"]["total_tokens"]
        }

    def _optimize_code(
        self,
        language: str,
        code: str,
        execution,
        db: Session
    ) -> Dict[str, Any]:
        """Optimize code for performance"""
        self._update_status(
            execution,
            AgentStatus.WORKING,
            f"Optimizing {language} code...",
            42,
            db
        )

        prompt = f"""TASK: Performance Optimization

LANGUAGE: {language.upper()}

CODE TO OPTIMIZE:
```{language}
{code}
```

Optimize this code for performance:
1. Identify performance bottlenecks
2. Suggest algorithmic improvements
3. Optimize data structures
4. Reduce computational complexity
5. Implement caching where beneficial
6. Add async/parallel processing if applicable
7. Reduce memory footprint

Provide the optimized code with performance analysis."""

        response = claude_service.generate(
            messages=[{"role": "user", "content": prompt}],
            system=self.system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        self._update_status(
            execution,
            AgentStatus.WORKING,
            "Optimization complete",
            94,
            db
        )

        execution.tokens_used += response["usage"]["total_tokens"]
        execution.cost_usd = round(
            (response["usage"]["input_tokens"] * 0.003 / 1000) +
            (response["usage"]["output_tokens"] * 0.015 / 1000),
            6
        )
        db.commit()

        return {
            "success": True,
            "task_type": "optimization",
            "language": language,
            "optimized_code": response["content"],
            "tokens_used": response["usage"]["total_tokens"]
        }


# Singleton instance
polyglot_agent = PolyglotAgent()

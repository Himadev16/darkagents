"""
Agent 03: Polyglot Developer
Elite multi-language software engineer for code generation
PRODUCTION-READY with retry logic, rollback, and validation
"""
import time
from typing import Dict, Any
import structlog
from sqlalchemy.orm import Session

from backend.database.models import AgentExecution, Project
from backend.agents.base_agent import BaseAgent
from backend.services.claude_service import claude_service

logger = structlog.get_logger()


class PolyglotAgent(BaseAgent):
    """
    Polyglot Developer Agent

    Elite multi-language software engineer with expertise in 20+ languages.

    Capabilities:
    - Master of Python, JavaScript, TypeScript, Go, Rust, Java, C++, and more
    - Production-ready code generation with best practices
    - Code review, refactoring, and optimization
    - Debugging and problem-solving
    - Test generation (unit, integration, e2e)
    - Architecture and design patterns
    - Performance optimization
    - Security-aware coding

    Production Features:
    - Retry logic with exponential backoff (3 retries)
    - Input validation with detailed error messages
    - Database transaction management with rollback
    - Graceful error handling
    - Detailed structured logging
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
        "dart": {"expertise": "advanced", "frameworks": ["Flutter"]},
    }

    def __init__(self):
        """Initialize Polyglot Developer Agent"""
        self.agent_name = "polyglot_agent"
        self.agent_display_name = "Polyglot Developer"
        self.max_retries = 3
        self.retry_delay = 2  # Base delay in seconds for exponential backoff

    def execute(self, project_id: int, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Execute Polyglot Developer Agent

        Args:
            project_id: Project ID
            input_data: {
                "task_type": str (code_generation, code_review, debugging, refactoring, testing, optimization),
                "language": str (python, javascript, typescript, etc.),
                "requirements": str (task requirements),
                "existing_code": str (optional, for review/debugging/refactoring)
            }
            db: Database session

        Returns:
            {
                "success": bool,
                "task_type": str,
                "language": str,
                "output": str (generated code or analysis),
                "execution_id": int,
                "tokens_used": int,
                "cost_usd": float,
                "error": str (if success=False)
            }
        """
        execution = None
        try:
            logger.info(
                "polyglot_agent_started",
                project_id=project_id,
                agent_name=self.agent_name
            )

            # Input validation
            if not input_data:
                input_data = {}

            task_type = input_data.get("task_type", "code_generation")
            if task_type not in ["code_generation", "code_review", "debugging", "refactoring", "testing", "optimization"]:
                raise ValueError(f"Invalid task_type '{task_type}' (must be: code_generation, code_review, debugging, refactoring, testing, optimization)")

            language = input_data.get("language", "python")
            if not language or not isinstance(language, str):
                raise ValueError("Missing or invalid 'language' (must be non-empty string)")

            language = language.lower()
            if language not in self.LANGUAGES:
                raise ValueError(f"Unsupported language '{language}' (supported: {', '.join(list(self.LANGUAGES.keys())[:10])}...)")

            requirements = input_data.get("requirements", "")
            existing_code = input_data.get("existing_code", "")

            # Validate based on task type
            if task_type == "code_generation":
                if not requirements or not isinstance(requirements, str):
                    raise ValueError("Missing or invalid 'requirements' for code_generation (must be non-empty string)")
                if len(requirements.strip()) < 10:
                    raise ValueError("requirements too short (minimum 10 characters)")
            elif task_type in ["code_review", "debugging", "refactoring", "testing", "optimization"]:
                if not existing_code or not isinstance(existing_code, str):
                    raise ValueError(f"Missing or invalid 'existing_code' for {task_type} (must be non-empty string)")
                if len(existing_code.strip()) < 10:
                    raise ValueError("existing_code too short (minimum 10 characters)")

            # Create database record
            try:
                execution = AgentExecution(
                    project_id=project_id,
                    agent_name=self.agent_name,
                    agent_display_name=self.agent_display_name,
                    status="working",
                    progress=0,
                    current_task=f"{task_type.replace('_', ' ').title()} in {language}",
                    tokens_used=0,
                    cost_usd=0.0
                )
                db.add(execution)
                db.commit()
                db.refresh(execution)

                logger.info(
                    "polyglot_execution_created",
                    execution_id=execution.id,
                    project_id=project_id,
                    task_type=task_type,
                    language=language
                )
            except Exception as db_error:
                logger.error("database_error_creating_execution", error=str(db_error))
                db.rollback()
                raise

            # Update progress
            execution.current_task = f"Processing {task_type} for {language}"
            execution.progress = 10
            try:
                db.commit()
            except Exception:
                db.rollback()

            # Execute task with retry logic
            result = self._execute_task_with_retry(
                task_type=task_type,
                language=language,
                requirements=requirements,
                existing_code=existing_code,
                project_id=project_id,
                execution=execution,
                db=db
            )

            # Update execution record with results
            try:
                execution.status = "completed"
                execution.progress = 100
                execution.current_task = f"{task_type.replace('_', ' ').title()} complete"
                execution.tokens_used = result.get("tokens_used", 0)
                execution.cost_usd = result.get("cost_usd", 0.0)
                db.commit()

                logger.info(
                    "polyglot_agent_completed",
                    execution_id=execution.id,
                    project_id=project_id,
                    task_type=task_type,
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
                "polyglot_validation_error",
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
                "polyglot_agent_failed",
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

    def _execute_task_with_retry(
        self,
        task_type: str,
        language: str,
        requirements: str,
        existing_code: str,
        project_id: int,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Execute task with retry logic (exponential backoff)

        Retries up to max_retries times with exponential backoff on transient errors
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "task_execution_attempt",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    task_type=task_type,
                    project_id=project_id
                )

                result = self._execute_task(
                    task_type=task_type,
                    language=language,
                    requirements=requirements,
                    existing_code=existing_code,
                    execution=execution,
                    db=db
                )

                logger.info(
                    "task_execution_success",
                    attempt=attempt,
                    project_id=project_id,
                    task_type=task_type
                )

                return result

            except ValueError as ve:
                # Don't retry validation errors
                logger.error("task_execution_validation_error", error=str(ve))
                raise

            except Exception as e:
                last_error = e
                logger.warning(
                    "task_execution_attempt_failed",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    error=str(e),
                    error_type=type(e).__name__
                )

                if attempt == self.max_retries:
                    logger.error(
                        "task_execution_all_retries_failed",
                        project_id=project_id,
                        task_type=task_type,
                        error=str(e)
                    )
                    raise

                # Exponential backoff: 2s, 4s, 8s
                wait_time = self.retry_delay * (2 ** (attempt - 1))
                logger.info(
                    "task_execution_retrying",
                    wait_time=wait_time,
                    next_attempt=attempt + 1
                )
                time.sleep(wait_time)

        # Should never reach here, but just in case
        raise last_error if last_error else Exception("Unknown error in retry logic")

    def _execute_task(
        self,
        task_type: str,
        language: str,
        requirements: str,
        existing_code: str,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Execute coding task using Claude Sonnet 4.5

        This is the core method that calls OpenRouter API
        """
        logger.info("executing_task", task_type=task_type, language=language)

        system_prompt = self._build_system_prompt(language)
        user_prompt = self._build_user_prompt(task_type, language, requirements, existing_code)

        # Update progress
        execution.current_task = f"Calling Claude Sonnet 4.5 for {task_type}"
        execution.progress = 30
        try:
            db.commit()
        except Exception:
            db.rollback()

        # Call OpenRouter API
        try:
            response = claude_service.generate(
                
                messages=[
                    system=system_prompt,
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower for precise code generation
                max_tokens=12000
            )

            # Extract response
            content = response["content"]

            # Extract token usage
            tokens_used = response["usage"]["total_tokens"]

            # Calculate cost (Claude Sonnet 4: $3/1M input, $15/1M output)
            cost_usd = response["cost_usd"]

            logger.info(
                "openrouter_api_success",
                tokens_used=tokens_used,
                cost_usd=cost_usd,
                task_type=task_type
            )

        except Exception as api_error:
            logger.error("openrouter_api_error", error=str(api_error), task_type=task_type)
            raise

        # Update progress
        execution.current_task = f"Finalizing {task_type}"
        execution.progress = 90
        try:
            db.commit()
        except Exception:
            db.rollback()

        return {
            "task_type": task_type,
            "language": language,
            "output": content,
            "tokens_used": tokens_used,
            "cost_usd": round(cost_usd, 4)
        }

    def _build_system_prompt(self, language: str) -> str:
        """Build comprehensive system prompt for Polyglot Agent"""
        lang_info = self.LANGUAGES.get(language, {"expertise": "intermediate", "frameworks": []})
        frameworks = ", ".join(lang_info["frameworks"][:5])

        return f"""You are the POLYGLOT AGENT - an elite multi-language software engineer.

# Your Identity

You are a world-class software engineer with expert-level proficiency in {language.upper()}.
Your expertise level in {language}: {lang_info['expertise'].upper()}
Popular frameworks you master: {frameworks}

# Your Mission

Generate production-ready, elegant, and performant code that surpasses human developers.
Your code should be:
- **Clean** - Following language idioms and best practices
- **Secure** - No vulnerabilities, proper input validation
- **Performant** - Optimized algorithms and data structures
- **Maintainable** - Clear naming, proper documentation
- **Tested** - Include test cases when appropriate

# Multi-Language Expertise

You are proficient in 20+ languages:
- **Expert**: Python, JavaScript, TypeScript, Go, Rust, Java
- **Advanced**: C++, C#, Ruby, PHP, Swift, Kotlin, Dart
- **Intermediate**: Scala, Elixir, Haskell, Clojure, Julia, Lua, R

# Code Generation Standards

1. **Best Practices**
   - Follow the language's official style guide
   - Use type hints/annotations where supported
   - Include comprehensive error handling
   - Add logging for production code
   - Consider edge cases

2. **Security**
   - Prevent SQL injection, XSS, CSRF
   - Sanitize inputs and validate data
   - No hardcoded secrets or credentials
   - Follow OWASP Top 10 guidelines

3. **Performance**
   - Choose optimal data structures
   - Avoid unnecessary loops
   - Use async/parallel processing when beneficial
   - Consider memory footprint

4. **Architecture**
   - Apply SOLID principles
   - Use appropriate design patterns
   - Maintain separation of concerns
   - Make code testable

# Output Format

Structure your responses clearly:

1. **ANALYSIS** - Brief analysis of the task
2. **APPROACH** - Your solution strategy
3. **CODE** - Clean, production-ready implementation
4. **EXPLANATION** - Key decisions and trade-offs
5. **NOTES** - Important considerations or optimizations

# Quality Standards

- Code MUST be production-ready, not prototypes
- Include proper imports and dependencies
- Add docstrings/comments for complex logic
- Handle errors gracefully
- Make code maintainable for teams

Remember: You craft elegant software solutions that developers admire."""

    def _build_user_prompt(self, task_type: str, language: str, requirements: str, existing_code: str) -> str:
        """Build user prompt based on task type"""
        if task_type == "code_generation":
            return f"""# Task: Code Generation

**Language**: {language.upper()}

**Requirements**:
{requirements}

Generate production-ready {language} code that fulfills these requirements.

Follow the OUTPUT FORMAT specified in your system prompt:
1. ANALYSIS
2. APPROACH
3. CODE
4. EXPLANATION
5. NOTES

Make it exceptional."""

        elif task_type == "code_review":
            return f"""# Task: Code Review

**Language**: {language.upper()}

**Code to Review**:
```{language}
{existing_code[:3000]}
```

Perform a comprehensive code review:
1. Identify bugs, code smells, and anti-patterns
2. Suggest improvements for readability and maintainability
3. Check security vulnerabilities
4. Recommend performance optimizations
5. Verify best practices compliance
6. Provide refactored version if needed

Be thorough but constructive."""

        elif task_type == "debugging":
            error_info = requirements or "Debug this code and fix any issues"
            return f"""# Task: Debugging

**Language**: {language.upper()}

**Problematic Code**:
```{language}
{existing_code[:3000]}
```

**Issue/Error**:
{error_info}

Debug this code:
1. Identify the root cause
2. Explain why the error occurs
3. Provide the fixed code
4. Suggest preventive measures
5. Add error handling if missing"""

        elif task_type == "refactoring":
            return f"""# Task: Code Refactoring

**Language**: {language.upper()}

**Code to Refactor**:
```{language}
{existing_code[:3000]}
```

Refactor this code to improve:
1. Readability and clarity
2. Maintainability
3. Performance
4. Testability
5. Adherence to SOLID principles
6. Use of design patterns where appropriate

Provide the refactored code with explanations."""

        elif task_type == "testing":
            return f"""# Task: Test Generation

**Language**: {language.upper()}

**Code to Test**:
```{language}
{existing_code[:3000]}
```

Generate comprehensive tests:
1. Unit tests for all functions/methods
2. Edge cases and boundary conditions
3. Error/exception handling tests
4. Integration tests if applicable
5. Test fixtures and mocks where needed

Use the appropriate testing framework for {language}."""

        elif task_type == "optimization":
            return f"""# Task: Performance Optimization

**Language**: {language.upper()}

**Code to Optimize**:
```{language}
{existing_code[:3000]}
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

        else:
            return f"Task: {task_type}\nLanguage: {language}\nRequirements: {requirements}"


# Singleton instance
polyglot_agent = PolyglotAgent()

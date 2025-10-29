"""
Agent 04: UI/UX Designer
Senior product designer that polishes frontend code with professional UI design
PRODUCTION-READY with retry logic, rollback, and validation
"""
import time
from typing import Dict, Any
import structlog
from sqlalchemy.orm import Session

from backend.database.models import AgentExecution, Project
from backend.agents.base_agent import BaseAgent
from backend.lib.openrouter import openrouter_client

logger = structlog.get_logger()


class UIUXDesignerAgent(BaseAgent):
    """
    UI/UX Designer Agent

    Senior product designer with 10+ years of experience in modern web design.

    Capabilities:
    - Design system creation (colors, typography, spacing, shadows)
    - Component design improvements (buttons, forms, cards, navigation)
    - Animations and micro-interactions (hover, transitions, loading states)
    - Responsive design enhancements (mobile-first, breakpoints)
    - Accessibility improvements (WCAG 2.1 AA compliance, ARIA labels)
    - Modern UI patterns (glassmorphism, gradients, shadows)

    Production Features:
    - Retry logic with exponential backoff (3 retries)
    - Input validation with detailed error messages
    - Database transaction management with rollback
    - Graceful error handling
    - Detailed structured logging
    """

    def __init__(self):
        """Initialize UI/UX Designer Agent"""
        self.agent_name = "ui_ux_designer"
        self.agent_display_name = "UI/UX Designer"
        self.max_retries = 3
        self.retry_delay = 2  # Base delay in seconds for exponential backoff

    def execute(self, project_id: int, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Execute UI/UX Designer Agent

        Args:
            project_id: Project ID
            input_data: {
                "frontend_code": str (React/Next.js code to enhance),
                "design_style": str (optional, e.g., "modern-minimalist", "vibrant"),
                "color_scheme": str (optional, e.g., "professional", "playful"),
                "target_audience": str (optional, e.g., "business professionals")
            }
            db: Database session

        Returns:
            {
                "success": bool,
                "enhanced_code": str (frontend code with design improvements),
                "design_improvements": list (summary of improvements),
                "execution_id": int,
                "tokens_used": int,
                "cost_usd": float,
                "error": str (if success=False)
            }
        """
        execution = None
        try:
            logger.info(
                "ui_ux_designer_started",
                project_id=project_id,
                agent_name=self.agent_name
            )

            # Input validation
            if not input_data:
                input_data = {}

            frontend_code = input_data.get("frontend_code") or input_data.get("code", "")
            if not frontend_code or not isinstance(frontend_code, str):
                raise ValueError("Missing or invalid 'frontend_code' (must be non-empty string)")

            if len(frontend_code.strip()) < 20:
                raise ValueError("frontend_code too short (minimum 20 characters)")

            # Optional fields with safe defaults
            design_style = input_data.get("design_style", "modern-minimalist")
            color_scheme = input_data.get("color_scheme", "professional")
            target_audience = input_data.get("target_audience", "business professionals")

            # Create database record
            try:
                execution = AgentExecution(
                    project_id=project_id,
                    agent_name=self.agent_name,
                    agent_display_name=self.agent_display_name,
                    status="working",
                    progress=0,
                    current_task="Analyzing frontend code",
                    tokens_used=0,
                    cost_usd=0.0
                )
                db.add(execution)
                db.commit()
                db.refresh(execution)

                logger.info(
                    "ui_ux_designer_execution_created",
                    execution_id=execution.id,
                    project_id=project_id
                )
            except Exception as db_error:
                logger.error("database_error_creating_execution", error=str(db_error))
                db.rollback()
                raise

            # Update progress
            execution.current_task = "Enhancing UI/UX design"
            execution.progress = 10
            try:
                db.commit()
            except Exception:
                db.rollback()

            # Enhance design with retry logic
            result = self._enhance_design_with_retry(
                frontend_code=frontend_code,
                design_style=design_style,
                color_scheme=color_scheme,
                target_audience=target_audience,
                project_id=project_id,
                execution=execution,
                db=db
            )

            # Update execution record with results
            try:
                execution.status = "completed"
                execution.progress = 100
                execution.current_task = "Design enhancement complete"
                execution.tokens_used = result.get("tokens_used", 0)
                execution.cost_usd = result.get("cost_usd", 0.0)
                db.commit()

                logger.info(
                    "ui_ux_designer_completed",
                    execution_id=execution.id,
                    project_id=project_id,
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
                "ui_ux_designer_validation_error",
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
                "ui_ux_designer_failed",
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

    def _enhance_design_with_retry(
        self,
        frontend_code: str,
        design_style: str,
        color_scheme: str,
        target_audience: str,
        project_id: int,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Enhance design with retry logic (exponential backoff)

        Retries up to max_retries times with exponential backoff on transient errors
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "design_enhancement_attempt",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    project_id=project_id
                )

                result = self._enhance_design(
                    frontend_code=frontend_code,
                    design_style=design_style,
                    color_scheme=color_scheme,
                    target_audience=target_audience,
                    execution=execution,
                    db=db
                )

                logger.info(
                    "design_enhancement_success",
                    attempt=attempt,
                    project_id=project_id
                )

                return result

            except ValueError as ve:
                # Don't retry validation errors
                logger.error("design_enhancement_validation_error", error=str(ve))
                raise

            except Exception as e:
                last_error = e
                logger.warning(
                    "design_enhancement_attempt_failed",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    error=str(e),
                    error_type=type(e).__name__
                )

                if attempt == self.max_retries:
                    logger.error(
                        "design_enhancement_all_retries_failed",
                        project_id=project_id,
                        error=str(e)
                    )
                    raise

                # Exponential backoff: 2s, 4s, 8s
                wait_time = self.retry_delay * (2 ** (attempt - 1))
                logger.info(
                    "design_enhancement_retrying",
                    wait_time=wait_time,
                    next_attempt=attempt + 1
                )
                time.sleep(wait_time)

        # Should never reach here, but just in case
        raise last_error if last_error else Exception("Unknown error in retry logic")

    def _enhance_design(
        self,
        frontend_code: str,
        design_style: str,
        color_scheme: str,
        target_audience: str,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Enhance frontend code with professional UI/UX design using Claude Sonnet 4.5

        This is the core method that calls OpenRouter API
        """
        logger.info("enhancing_design", design_style=design_style, color_scheme=color_scheme)

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(frontend_code, design_style, color_scheme, target_audience)

        # Update progress
        execution.current_task = "Calling Claude Sonnet 4.5 for design enhancement"
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
                temperature=0.5,  # More creative for design work
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
        execution.current_task = "Extracting design improvements"
        execution.progress = 80
        try:
            db.commit()
        except Exception:
            db.rollback()

        # Extract improvements summary
        design_improvements = self._extract_improvements_summary(content)

        return {
            "enhanced_code": content,
            "design_improvements": design_improvements,
            "tokens_used": tokens_used,
            "cost_usd": round(cost_usd, 4)
        }

    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt for UI/UX Designer agent"""
        return """You are the UI/UX DESIGNER AGENT - a senior product designer with 10+ years of experience.

# Your Identity

You are a world-class product designer specializing in:
- Tailwind CSS and modern CSS techniques
- React/Next.js component design
- Accessible design (WCAG 2.1 AA compliance)
- Animation and micro-interactions
- Responsive design (mobile-first approach)
- Modern design systems

# Your Mission

Enhance existing frontend code with professional UI/UX design that is:
- **Beautiful** - Visually stunning and modern
- **Accessible** - WCAG 2.1 AA compliant with ARIA labels
- **Responsive** - Mobile-first, optimized for all screen sizes
- **Animated** - Smooth transitions and micro-interactions
- **Performant** - Optimized CSS, minimal reflows

# Design System Standards

**Color Palette:**
- Primary: blue-600 (buttons, links, brand)
- Secondary: gray-700 (text, headings)
- Accent: emerald-500 (success, highlights)
- Danger: red-500 (errors, destructive actions)
- Background: gray-50 (light mode), gray-900 (dark mode)

**Typography Scale:**
- h1: text-4xl or text-5xl, font-bold, tracking-tight
- h2: text-3xl or text-4xl, font-bold
- h3: text-2xl or text-3xl, font-semibold
- body: text-base, leading-relaxed
- small: text-sm, text-gray-600

**Spacing System:**
- Section gaps: gap-8, gap-12, gap-16
- Card padding: p-6, p-8
- Button padding: px-6 py-3 (medium), px-4 py-2 (small)
- Container max-width: max-w-7xl, max-w-6xl

**Shadow System:**
- Subtle: shadow-sm
- Medium: shadow-md
- Strong: shadow-lg, shadow-xl

**Animation Standards:**
- Hover: hover:scale-105 transition-transform duration-200
- Focus: focus:ring-2 focus:ring-blue-500 focus:outline-none
- Button press: active:scale-95
- Transitions: transition-all duration-200 ease-in-out

# Your Deliverables

Enhance the provided frontend code with:

1. **Design System** - Cohesive colors, typography, spacing, shadows
2. **Component Polish** - Better buttons, forms, cards, navigation
3. **Animations** - Smooth transitions, hover effects, loading states
4. **Responsive Design** - Mobile-first, optimized breakpoints
5. **Accessibility** - WCAG 2.1 AA compliance, ARIA labels, keyboard navigation
6. **Modern Patterns** - Gradients, glassmorphism, subtle shadows

# Critical Rules

- ❌ DO NOT change functionality or remove features
- ❌ DO NOT break existing behavior
- ✅ DO enhance visual design with Tailwind CSS
- ✅ DO add smooth animations and transitions
- ✅ DO ensure accessibility (ARIA, focus states, color contrast)
- ✅ DO optimize for mobile (responsive, touch-friendly)
- ✅ DO use semantic HTML elements
- ✅ DO provide hover states for all interactive elements

# Output Format

Return the enhanced code with a summary of improvements at the top:

```tsx
// DESIGN IMPROVEMENTS:
// 1. Added cohesive color palette (blue-600 primary, emerald-500 accent)
// 2. Enhanced typography with font-bold headings and leading-relaxed body
// 3. Added smooth hover animations (scale-105, duration-200)
// 4. Improved accessibility (ARIA labels, focus states, color contrast)
// 5. Enhanced responsive design (mobile-first, touch-friendly)

// Path: components/Dashboard.tsx
import { useState } from 'react';

export default function Dashboard() {
  // [Enhanced component code here]
}
```

Remember: You are enhancing EXISTING code, not creating new features. Focus on making it visually stunning, accessible, and delightful to use."""

    def _build_user_prompt(self, frontend_code: str, design_style: str, color_scheme: str, target_audience: str) -> str:
        """Build user prompt with code to enhance"""
        return f"""# Design Enhancement Mission

Enhance the following frontend code with professional UI/UX design.

## Design Preferences

- **Design Style**: {design_style}
- **Color Scheme**: {color_scheme}
- **Target Audience**: {target_audience}

## Your Task

Take the existing code and enhance it with:

1. **Design System** - Cohesive colors, typography, spacing, shadows
2. **Component Polish** - Better button styles, form inputs, cards, navigation
3. **Animations** - Smooth transitions, hover effects, loading states
4. **Responsive Design** - Mobile-first, optimized breakpoints
5. **Accessibility** - WCAG 2.1 AA compliance, ARIA labels, keyboard navigation
6. **Modern Patterns** - Gradients, glassmorphism, subtle shadows

## Critical Rules

- ❌ DO NOT change functionality or remove features
- ❌ DO NOT break existing behavior
- ✅ DO enhance visual design with Tailwind CSS
- ✅ DO add smooth animations and transitions
- ✅ DO ensure accessibility (ARIA, focus states, color contrast)
- ✅ DO optimize for mobile (responsive, touch-friendly)

## Code to Enhance

{frontend_code[:4000]}

Return the enhanced code with a summary of improvements at the top.

Begin your enhanced code now:
"""

    def _extract_improvements_summary(self, enhanced_code: str) -> list:
        """
        Extract design improvements summary from enhanced code

        Looks for comment blocks with numbered improvements
        """
        import re

        improvements = []

        try:
            # Pattern: // 1. Some improvement
            pattern = r'//\s*\d+\.\s*(.+?)(?=\n|$)'
            matches = re.findall(pattern, enhanced_code, re.MULTILINE)

            if matches:
                improvements = [match.strip() for match in matches[:10]]  # Limit to 10

            logger.info("extracted_improvements", count=len(improvements))

        except Exception as e:
            logger.warning("extract_improvements_error", error=str(e))

        return improvements


# Singleton instance
ui_ux_designer_agent = UIUXDesignerAgent()

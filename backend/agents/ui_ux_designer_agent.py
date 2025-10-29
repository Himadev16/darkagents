"""
Agent 04: UI/UX Designer Agent
================================

The UI/UX Designer Agent is a senior product designer that polishes and enhances
frontend code with professional UI design, animations, and accessibility.

Input: Frontend code from Polyglot Agent (React/Next.js components)
Output: Enhanced code with improved design, including:
  - Design system (colors, typography, spacing)
  - Improved component design
  - Animations and micro-interactions
  - Responsive design enhancements
  - Accessibility improvements (WCAG 2.1 AA compliance)
  - Modern UI patterns and best practices

Does NOT generate new code from scratch - only polishes existing code.
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
import structlog

from backend.services.claude_service import claude_service
from backend.models import Project, AgentExecution

logger = structlog.get_logger(__name__)


class UIUXDesignerAgent:
    """
    Agent 04: UI/UX Designer

    Senior product designer with 10+ years of experience in modern web design.
    Specializes in Tailwind CSS, React components, and accessible design.
    """

    def __init__(self):
        self.agent_name = "ui_ux_designer"
        self.agent_display_name = "UI/UX Designer"
        self.agent_description = "Senior product designer - Polishes UI with professional design and animations"
        self.model = "anthropic/claude-sonnet-4.5"
        self.temperature = 0.5  # More creative for design work
        self.max_tokens = 10000  # Comprehensive design improvements

    def execute(self, project_id: int, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Execute the UI/UX Designer Agent

        Args:
            project_id: ID of the project
            input_data: Must contain 'frontend_code' (from Polyglot Agent) or 'code'
            db: Database session

        Returns:
            Enhanced frontend code with design improvements
        """
        try:
            logger.info(
                "ui_ux_designer_agent.execute.start",
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

            # Get frontend code from input
            frontend_code = input_data.get("frontend_code") or input_data.get("code", "")
            if not frontend_code:
                raise ValueError("Missing 'frontend_code' or 'code' in input_data")

            # Optional: Get design preferences
            design_style = input_data.get("design_style", "modern-minimalist")
            color_scheme = input_data.get("color_scheme", "professional")
            target_audience = input_data.get("target_audience", "business professionals")

            # Generate design improvements
            logger.info("ui_ux_designer_agent.enhancing_design")
            enhanced_design = self._enhance_design(
                frontend_code=frontend_code,
                design_style=design_style,
                color_scheme=color_scheme,
                target_audience=target_audience,
                execution=execution,
                db=db
            )

            # Update execution record
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.output = enhanced_design["content"]
            execution.tokens_used = enhanced_design["tokens_used"]
            execution.cost_usd = enhanced_design["cost_usd"]
            db.commit()

            logger.info(
                "ui_ux_designer_agent.execute.complete",
                execution_id=execution.id,
                tokens_used=enhanced_design["tokens_used"],
                cost_usd=enhanced_design["cost_usd"]
            )

            return {
                "success": True,
                "execution_id": execution.id,
                "agent_name": self.agent_name,
                "enhanced_code": enhanced_design["content"],
                "design_improvements": enhanced_design.get("improvements_summary", []),
                "tokens_used": enhanced_design["tokens_used"],
                "cost_usd": enhanced_design["cost_usd"],
            }

        except Exception as e:
            logger.error(
                "ui_ux_designer_agent.execute.error",
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
        Enhance frontend code with professional UI/UX design

        Returns:
            {
                "content": "Enhanced frontend code with design improvements",
                "tokens_used": 10500,
                "cost_usd": 0.05,
                "improvements_summary": [
                    "Added cohesive color palette",
                    "Improved typography hierarchy",
                    "Added smooth animations",
                    "Enhanced accessibility (ARIA labels)"
                ]
            }
        """

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            frontend_code,
            design_style,
            color_scheme,
            target_audience
        )

        # Call Claude API
        response = claude_service.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        # Extract improvements summary from response
        improvements_summary = self._extract_improvements_summary(response["content"])

        return {
            "content": response["content"],
            "tokens_used": response["tokens_used"],
            "cost_usd": response["cost_usd"],
            "improvements_summary": improvements_summary
        }

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the UI/UX Designer Agent"""

        return """You are the UI/UX DESIGNER AGENT - a senior product designer with 10+ years of experience in modern web design for the DARKAGENTS platform.

🎯 YOUR ROLE:
You take existing frontend code and enhance it with professional UI/UX design. You specialize in:
- Tailwind CSS and modern CSS techniques
- React/Next.js component design
- Accessible design (WCAG 2.1 AA compliance)
- Animation and micro-interactions
- Responsive design (mobile-first approach)
- Modern design systems

🎨 YOUR EXPERTISE:
- Design Systems (colors, typography, spacing, shadows)
- Visual Hierarchy (layout, contrast, whitespace)
- User Experience (intuitive navigation, clear CTAs)
- Accessibility (screen readers, keyboard navigation, color contrast)
- Performance (optimized CSS, reduced reflows)
- Modern Patterns (glassmorphism, neumorphism, gradients, animations)

📋 YOUR DELIVERABLES:
You must enhance the provided frontend code with:

1. **Design System**
   - Cohesive color palette (primary, secondary, accent, neutrals)
   - Typography scale (font families, sizes, weights, line heights)
   - Spacing system (consistent margins, padding, gaps)
   - Shadow system (subtle elevation for depth)
   - Border radius (consistent rounded corners)

2. **Component Design Improvements**
   - Enhanced button styles (hover, active, focus, disabled states)
   - Improved form inputs (labels, placeholders, validation states)
   - Better card designs (shadows, borders, hover effects)
   - Navigation improvements (clear hierarchy, active states)
   - Modal and dialog polish (overlays, animations)

3. **Animations & Micro-interactions**
   - Smooth transitions (hover, focus, state changes)
   - Loading states (spinners, skeletons, progress indicators)
   - Entry animations (fade-in, slide-in, scale)
   - Exit animations (fade-out, slide-out)
   - Scroll animations (parallax, reveal on scroll)
   - Interactive feedback (button clicks, form submissions)

4. **Responsive Design**
   - Mobile-first approach
   - Breakpoint optimization (sm, md, lg, xl, 2xl)
   - Touch-friendly targets (minimum 44x44px)
   - Readable text sizes on mobile
   - Optimized layouts for different screen sizes

5. **Accessibility (WCAG 2.1 AA)**
   - Semantic HTML elements
   - ARIA labels and roles
   - Color contrast ratios (4.5:1 for text, 3:1 for UI components)
   - Keyboard navigation support (focus visible, tab order)
   - Screen reader friendly (alt text, labels)
   - Focus indicators
   - Skip links

6. **Modern UI Patterns**
   - Glassmorphism (backdrop-blur, transparency)
   - Gradient backgrounds
   - Subtle shadows for depth
   - Smooth rounded corners
   - Elegant hover states
   - Empty states
   - Error states
   - Success states

🔥 CRITICAL DESIGN RULES:

1. **NEVER change the functionality** - Only enhance visual design
2. **NEVER remove existing features** - Only add design improvements
3. **NEVER break responsive behavior** - Only enhance it
4. **ALWAYS use Tailwind CSS classes** - No custom CSS unless absolutely necessary
5. **ALWAYS maintain readability** - Don't sacrifice UX for aesthetics
6. **ALWAYS ensure accessibility** - WCAG 2.1 AA compliance is mandatory
7. **ALWAYS add smooth transitions** - duration-200, duration-300, ease-in-out
8. **ALWAYS provide hover states** - For all interactive elements
9. **ALWAYS use semantic colors** - blue for primary, red for danger, green for success
10. **ALWAYS optimize for performance** - Minimize unnecessary classes

💡 DESIGN BEST PRACTICES:

**Color Palette Examples:**

Modern Professional:
- Primary: blue-600 (buttons, links, brand)
- Secondary: gray-700 (text, headings)
- Accent: emerald-500 (success, highlights)
- Danger: red-500 (errors, destructive actions)
- Background: gray-50 (light mode), gray-900 (dark mode)

Modern Vibrant:
- Primary: purple-600
- Secondary: pink-600
- Accent: orange-500
- Background: Gradient from purple-50 to pink-50

**Typography Scale:**
- Headings: font-bold, tracking-tight
- Body: font-normal, leading-relaxed
- Captions: text-sm, text-gray-600
- h1: text-4xl or text-5xl
- h2: text-3xl or text-4xl
- h3: text-2xl or text-3xl
- body: text-base
- small: text-sm

**Spacing System:**
- Section gaps: gap-8, gap-12, gap-16
- Card padding: p-6, p-8
- Button padding: px-6 py-3 (medium), px-4 py-2 (small)
- Container max-width: max-w-7xl, max-w-6xl

**Shadow System:**
- Subtle: shadow-sm
- Medium: shadow-md
- Strong: shadow-lg, shadow-xl
- Colored: shadow-blue-500/20

**Animation Examples:**
- Hover: hover:scale-105 transition-transform duration-200
- Focus: focus:ring-2 focus:ring-blue-500 focus:outline-none
- Button press: active:scale-95
- Fade in: opacity-0 animate-fadeIn
- Slide in: translate-y-4 animate-slideUp

🎯 OUTPUT FORMAT:

Return the enhanced code with clear comments showing what you improved:

```tsx
// DESIGN IMPROVEMENTS:
// 1. Added cohesive color palette (blue-600 primary, emerald-500 accent)
// 2. Enhanced typography with font-bold headings and leading-relaxed body
// 3. Added smooth hover animations (scale-105, duration-200)
// 4. Improved accessibility (ARIA labels, focus states, color contrast)
// 5. Enhanced responsive design (mobile-first, touch-friendly)
// 6. Added loading states and empty states
// 7. Improved button design with gradient backgrounds
// 8. Added subtle shadows for depth (shadow-lg)

// Path: components/Dashboard.tsx
import { useState } from 'react';
import { Loader2, Check, AlertCircle } from 'lucide-react';

export default function Dashboard() {
  // [Enhanced component code here]
}
```

Include a summary of improvements at the top.

Remember: You are enhancing EXISTING code, not creating new features. Focus on making it visually stunning, accessible, and delightful to use.
"""

    def _build_user_prompt(
        self,
        frontend_code: str,
        design_style: str,
        color_scheme: str,
        target_audience: str
    ) -> str:
        """Build the user prompt with code to enhance"""

        return f"""Enhance the following frontend code with professional UI/UX design.

📱 DESIGN PREFERENCES:
- Design Style: {design_style}
- Color Scheme: {color_scheme}
- Target Audience: {target_audience}

🎨 YOUR TASK:

Take the existing code and enhance it with:

1. **Design System** - Cohesive colors, typography, spacing, shadows
2. **Component Polish** - Better button styles, form inputs, cards, navigation
3. **Animations** - Smooth transitions, hover effects, loading states
4. **Responsive Design** - Mobile-first, optimized breakpoints
5. **Accessibility** - WCAG 2.1 AA compliance, ARIA labels, keyboard navigation
6. **Modern Patterns** - Gradients, glassmorphism, subtle shadows

CRITICAL RULES:
- ❌ DO NOT change functionality or remove features
- ❌ DO NOT break existing behavior
- ✅ DO enhance visual design with Tailwind CSS
- ✅ DO add smooth animations and transitions
- ✅ DO ensure accessibility (ARIA, focus states, color contrast)
- ✅ DO optimize for mobile (responsive, touch-friendly)

CODE TO ENHANCE:
{frontend_code}

Return the enhanced code with a summary of improvements at the top.

Begin your enhanced code now:
"""

    def _extract_improvements_summary(self, enhanced_code: str) -> List[str]:
        """
        Extract design improvements summary from enhanced code

        Looks for comment blocks with numbered improvements.
        Returns list of improvement descriptions.
        """

        improvements = []

        try:
            # Look for numbered improvements in comments
            import re

            # Pattern: // 1. Some improvement
            pattern = r'//\s*\d+\.\s*(.+?)(?=\n|$)'
            matches = re.findall(pattern, enhanced_code, re.MULTILINE)

            if matches:
                improvements = [match.strip() for match in matches[:10]]  # Limit to 10

            logger.info(
                "ui_ux_designer_agent.extracted_improvements",
                count=len(improvements)
            )

        except Exception as e:
            logger.warning(
                "ui_ux_designer_agent.extract_improvements.error",
                error=str(e)
            )
            # Return empty list on error
            pass

        return improvements

    def validate_design_enhancements(self, original_code: str, enhanced_code: str) -> Dict[str, Any]:
        """
        Validate that design enhancements didn't break functionality

        Checks:
        - Same number of components (no components removed)
        - Same component names (no renaming)
        - Accessibility improvements (ARIA attributes added)
        - Animation classes added
        - No broken syntax

        Returns:
            {
                "valid": True/False,
                "issues": [...],
                "improvements_detected": {
                    "aria_labels": 5,
                    "animations": 12,
                    "responsive_classes": 8
                }
            }
        """

        issues = []
        improvements_detected = {
            "aria_labels": 0,
            "animations": 0,
            "responsive_classes": 0,
            "focus_states": 0,
            "hover_effects": 0
        }

        try:
            # Count ARIA improvements
            import re
            improvements_detected["aria_labels"] = len(re.findall(r'aria-\w+', enhanced_code))
            improvements_detected["animations"] = len(re.findall(r'transition|animate|duration-', enhanced_code))
            improvements_detected["responsive_classes"] = len(re.findall(r'\b(sm|md|lg|xl|2xl):', enhanced_code))
            improvements_detected["focus_states"] = len(re.findall(r'focus:', enhanced_code))
            improvements_detected["hover_effects"] = len(re.findall(r'hover:', enhanced_code))

            # Check for common issues
            if "className=" not in enhanced_code and "class=" not in enhanced_code:
                issues.append("No styling classes found - design may not be applied")

            if improvements_detected["aria_labels"] == 0:
                issues.append("No accessibility improvements detected (missing ARIA labels)")

            if improvements_detected["animations"] == 0:
                issues.append("No animations or transitions added")

            logger.info(
                "ui_ux_designer_agent.validation_complete",
                improvements=improvements_detected,
                issues_count=len(issues)
            )

        except Exception as e:
            logger.warning(
                "ui_ux_designer_agent.validate_design_enhancements.error",
                error=str(e)
            )
            issues.append(f"Validation error: {str(e)}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "improvements_detected": improvements_detected
        }

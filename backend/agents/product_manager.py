"""
Agent 01: Product Manager
Transforms user ideas into detailed Product Requirements Documents
"""
from typing import Dict, Any
from sqlalchemy.orm import Session

from backend.agents.base_agent import BaseAgent
from backend.database import AgentExecution, GeneratedArtifact


class ProductManagerAgent(BaseAgent):
    """
    Product Manager Agent

    Personality:
    - Inquisitive, asks probing questions
    - Strategic thinker, focuses on 'why'
    - User-centric, problem-solving mindset
    - Conversational, empathetic, methodical

    Deliverables:
    - 8-12 page Product Requirements Document (PRD)
    - 3-5 user personas
    - 15-30 user stories (INVEST format)
    - Feature prioritization matrix (MoSCoW)
    - Success metrics and KPIs
    - Competitive analysis summary
    """

    def __init__(self):
        super().__init__(
            name="product_manager",
            display_name="Product Manager",
            role="Transform user ideas into detailed, actionable product requirements",
            temperature=0.7  # Creative but structured thinking
        )

    def _build_system_prompt(self) -> str:
        return """You are a Product Manager at DARKAGENTS, an AI-powered SaaS development platform.

PERSONALITY & COMMUNICATION STYLE:
- You are inquisitive and ask probing questions to deeply understand the product vision
- You think strategically and always ask 'why' before 'how'
- You are user-centric and focus on solving real problems
- You communicate in a conversational, empathetic, and methodical manner
- You never accept vague requirements - you dig deeper

YOUR EXPERTISE:
- Product strategy and vision
- User research and persona development
- Requirements gathering and documentation
- Feature prioritization (MoSCoW method)
- Competitive analysis
- Success metrics and KPIs

YOUR PROCESS:
1. Ask clarifying questions about the user's idea (10-15 targeted questions)
2. Understand target users, market, and business goals
3. Define the problem being solved
4. Create detailed user personas
5. Write comprehensive user stories
6. Prioritize features
7. Define success criteria
8. Document everything in a professional PRD

CRITICAL RULES:
- Always ask for clarification when something is unclear
- Think about scalability from the start
- Consider both technical and business constraints
- Write clear, actionable requirements
- Use industry-standard formats (INVEST user stories, MoSCoW prioritization)

Remember: You're not just documenting features - you're defining a product vision that will guide an entire development team."""

    def _perform_work(
        self,
        input_data: Dict[str, Any],
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Execute the Product Manager's workflow

        Steps:
        1. Analyze the user's initial idea
        2. Ask clarifying questions (if needed)
        3. Generate user personas
        4. Create user stories
        5. Build feature matrix
        6. Write comprehensive PRD
        7. Save everything to database
        """
        project = self.get_project(execution.project_id, db)
        user_idea = input_data.get("user_idea") or project.user_idea
        target_scale = input_data.get("target_scale") or project.target_scale

        # Update progress: Analyzing idea
        self._update_status(execution, execution.status, "Analyzing product idea...", 10, db)

        # Step 1: Analyze the idea and ask clarifying questions
        analysis_prompt = f"""I need you to analyze this product idea and create a comprehensive Product Requirements Document.

USER'S IDEA:
{user_idea}

TARGET SCALE: {target_scale if target_scale else 'Not specified'}

TASK 1: Ask Clarifying Questions
First, generate 10-15 probing questions that will help you understand this product deeply. Focus on:
- Target users and their pain points
- Core problems being solved
- Key features and functionality
- Business model and monetization
- Technical requirements and constraints
- Success criteria

Format your questions as a numbered list."""

        clarifying_questions = self.chat(analysis_prompt, execution, db)

        # Update progress: Generating personas
        self._update_status(execution, execution.status, "Creating user personas...", 25, db)

        # Step 2: Generate user personas (assuming questions are answered)
        personas_prompt = """Based on the product idea, create 3-5 detailed user personas.

For each persona, include:
- Name and demographic info (age, occupation, location)
- Background and context
- Goals and motivations
- Pain points and frustrations
- How they would use the product
- Quote that captures their mindset

Format as a structured list with clear sections."""

        personas = self.chat(personas_prompt, execution, db)

        # Update progress: Writing user stories
        self._update_status(execution, execution.status, "Writing user stories...", 40, db)

        # Step 3: Generate user stories
        user_stories_prompt = """Create 15-30 user stories for this product in INVEST format (Independent, Negotiable, Valuable, Estimable, Small, Testable).

Format:
"As a [persona], I want to [action] so that [benefit]"

Group stories by feature area:
- Core Features
- User Management
- Data Management
- Integrations
- Analytics/Reporting

For each story, add:
- Acceptance criteria (3-5 criteria)
- Priority (Must Have, Should Have, Could Have, Won't Have)"""

        user_stories = self.chat(user_stories_prompt, execution, db)

        # Update progress: Prioritizing features
        self._update_status(execution, execution.status, "Prioritizing features...", 60, db)

        # Step 4: Build feature prioritization matrix
        feature_matrix_prompt = """Create a feature prioritization matrix using the MoSCoW method.

For each major feature category:
- MUST HAVE (critical for MVP)
- SHOULD HAVE (important but not critical)
- COULD HAVE (nice to have)
- WON'T HAVE (out of scope for now)

Include brief justification for each priority level."""

        feature_matrix = self.chat(feature_matrix_prompt, execution, db)

        # Update progress: Defining success metrics
        self._update_status(execution, execution.status, "Defining success metrics...", 75, db)

        # Step 5: Define success metrics
        metrics_prompt = """Define success metrics and KPIs for this product.

Include:
- North Star Metric (one key metric that defines success)
- User Acquisition metrics (CAC, conversion rates)
- User Engagement metrics (DAU/MAU, retention, feature adoption)
- Business metrics (MRR, churn, LTV)
- Technical metrics (uptime, response time, error rate)

Provide specific, measurable targets."""

        success_metrics = self.chat(metrics_prompt, execution, db)

        # Update progress: Competitive analysis
        self._update_status(execution, execution.status, "Analyzing competition...", 85, db)

        # Step 6: Competitive analysis
        competitive_analysis_prompt = """Conduct a brief competitive analysis.

Identify:
- 3-5 direct or indirect competitors
- Their strengths and weaknesses
- Market gaps and opportunities
- This product's unique value proposition
- Differentiation strategy"""

        competitive_analysis = self.chat(competitive_analysis_prompt, execution, db)

        # Update progress: Writing final PRD
        self._update_status(execution, execution.status, "Writing final PRD...", 90, db)

        # Step 7: Generate comprehensive PRD
        prd_prompt = f"""Now compile everything into a comprehensive Product Requirements Document (PRD).

Structure:
1. Executive Summary (2-3 paragraphs)
2. Product Vision and Goals
3. Target Users and Personas
4. User Stories and Requirements
5. Feature Prioritization
6. Success Metrics and KPIs
7. Competitive Landscape
8. Technical Considerations (for {target_scale if target_scale else '10K users'})
9. Go-to-Market Strategy (brief)
10. Next Steps and Timeline

Write in professional, clear language suitable for sharing with stakeholders and developers.
Length: 8-12 pages worth of content."""

        final_prd = self.chat(prd_prompt, execution, db)

        # Save PRD as artifact
        artifact = GeneratedArtifact(
            project_id=execution.project_id,
            agent_name=self.name,
            artifact_type="prd",
            artifact_name="Product Requirements Document",
            content=final_prd,
            content_type="text/markdown",
            artifact_metadata={
                "sections": [
                    "Executive Summary",
                    "Product Vision",
                    "User Personas",
                    "User Stories",
                    "Feature Prioritization",
                    "Success Metrics",
                    "Competitive Analysis",
                    "Technical Considerations",
                    "Go-to-Market Strategy",
                    "Next Steps"
                ]
            }
        )
        db.add(artifact)
        db.commit()

        # Prepare deliverables
        result = {
            "prd": final_prd,
            "personas": personas,
            "user_stories": user_stories,
            "feature_matrix": feature_matrix,
            "success_metrics": success_metrics,
            "competitive_analysis": competitive_analysis,
            "clarifying_questions": clarifying_questions,
            "artifact_id": artifact.id
        }

        return result

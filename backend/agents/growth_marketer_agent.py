"""
Agent 08: Growth Marketer
Go-to-market strategy and growth marketing for SaaS products
"""
import time
from typing import Dict, Any
import structlog
from sqlalchemy.orm import Session

from backend.database.models import AgentExecution
from backend.agents.base_agent import BaseAgent
from backend.services.claude_service import claude_service

logger = structlog.get_logger()


class GrowthMarketerAgent(BaseAgent):
    """
    Growth Marketer Agent

    Senior growth marketer specializing in SaaS go-to-market strategy.

    Capabilities:
    - Go-to-market (GTM) strategy development
    - Landing page copywriting (headlines, CTAs, social proof)
    - SEO optimization (keywords, meta tags, schema markup)
    - Growth experiments (A/B tests, funnels, conversion optimization)
    - Customer acquisition strategy (channels, budget, CAC/LTV)
    - Content marketing strategy (blog, tutorials, case studies)
    - Email marketing (onboarding, nurture, retention sequences)
    - Social media strategy (LinkedIn, Twitter/X, Product Hunt)
    - Pricing page optimization
    - Product-led growth tactics

    Input: Product details from PM, Architect, and Designer agents
    Output: Comprehensive growth marketing package ready for execution

    Production Features:
    - Retry logic with exponential backoff (3 retries)
    - Input validation with detailed error messages
    - Database transaction management with rollback
    - Graceful error handling
    - Detailed structured logging
    """

    def __init__(self):
        """Initialize Growth Marketer Agent"""
        self.agent_name = "growth_marketer"
        self.agent_display_name = "Growth Marketer"
        self.max_retries = 3
        self.retry_delay = 2  # Base delay in seconds for exponential backoff

    def execute(self, project_id: int, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Execute Growth Marketer Agent

        Args:
            project_id: Project ID
            input_data: {
                "product_details": str (PRD or product description),
                "target_audience": str (optional, e.g., "B2B SaaS founders"),
                "value_proposition": str (optional),
                "pricing_model": str (optional, e.g., "freemium", "subscription"),
                "budget_range": str (optional, e.g., "$0-1K/month", "$1K-5K/month"),
                "growth_stage": str (optional, e.g., "pre-launch", "early-growth", "scaling"),
                "competitors": list (optional, e.g., ["Notion", "Airtable"]),
                "unique_features": list (optional)
            }
            db: Database session

        Returns:
            {
                "success": bool,
                "growth_strategy": str (GTM strategy document),
                "landing_page_copy": str (Headlines, CTAs, sections),
                "seo_strategy": str (Keywords, meta tags, content plan),
                "acquisition_channels": list (Prioritized channels with tactics),
                "content_strategy": str (Blog topics, tutorials, case studies),
                "email_sequences": str (Onboarding, nurture, retention emails),
                "social_media_strategy": str (Platform-specific tactics),
                "growth_experiments": list (A/B tests, funnel optimizations),
                "pricing_page_copy": str (Pricing tiers, comparisons),
                "metrics_dashboard": str (KPIs to track),
                "execution_id": int,
                "tokens_used": int,
                "cost_usd": float,
                "error": str (if success=False)
            }
        """
        execution = None
        try:
            logger.info(
                "growth_marketer_agent_started",
                project_id=project_id,
                agent_name=self.agent_name
            )

            # Input validation
            if not input_data:
                raise ValueError("input_data is required")

            product_details = input_data.get("product_details", "")
            if not product_details or not isinstance(product_details, str):
                raise ValueError("Missing or invalid 'product_details' (must be non-empty string)")

            if len(product_details.strip()) < 20:
                raise ValueError("product_details too short (minimum 20 characters)")

            # Optional fields with safe defaults
            target_audience = input_data.get("target_audience", "SaaS entrepreneurs and startup founders")
            value_proposition = input_data.get("value_proposition", "")
            pricing_model = input_data.get("pricing_model", "subscription")
            budget_range = input_data.get("budget_range", "$0-1K/month")
            growth_stage = input_data.get("growth_stage", "pre-launch")
            competitors = input_data.get("competitors", [])
            unique_features = input_data.get("unique_features", [])

            # Validate optional fields
            if not isinstance(competitors, list):
                competitors = []
            if not isinstance(unique_features, list):
                unique_features = []

            # Create database record
            try:
                execution = AgentExecution(
                    project_id=project_id,
                    agent_name=self.agent_name,
                    agent_display_name=self.agent_display_name,
                    status="working",
                    progress=0,
                    current_task="Analyzing product and market fit",
                    tokens_used=0,
                    cost_usd=0.0
                )
                db.add(execution)
                db.commit()
                db.refresh(execution)

                logger.info(
                    "growth_marketer_execution_created",
                    execution_id=execution.id,
                    project_id=project_id
                )
            except Exception as db_error:
                logger.error("database_error_creating_execution", error=str(db_error))
                db.rollback()
                raise

            # Update progress
            execution.current_task = "Developing go-to-market strategy"
            execution.progress = 10
            try:
                db.commit()
            except Exception:
                db.rollback()

            # Perform growth marketing analysis with retry logic
            result = self._develop_growth_strategy_with_retry(
                product_details=product_details,
                target_audience=target_audience,
                value_proposition=value_proposition,
                pricing_model=pricing_model,
                budget_range=budget_range,
                growth_stage=growth_stage,
                competitors=competitors,
                unique_features=unique_features,
                project_id=project_id,
                execution=execution,
                db=db
            )

            # Update execution record with results
            try:
                execution.status = "completed"
                execution.progress = 100
                execution.current_task = "Growth marketing package complete"
                execution.tokens_used = result.get("tokens_used", 0)
                execution.cost_usd = result.get("cost_usd", 0.0)
                db.commit()

                logger.info(
                    "growth_marketer_agent_completed",
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
                "growth_marketer_validation_error",
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
                "growth_marketer_agent_failed",
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

    def _develop_growth_strategy_with_retry(
        self,
        product_details: str,
        target_audience: str,
        value_proposition: str,
        pricing_model: str,
        budget_range: str,
        growth_stage: str,
        competitors: list,
        unique_features: list,
        project_id: int,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Develop growth strategy with retry logic (exponential backoff)

        Retries up to max_retries times with exponential backoff on transient errors
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "growth_strategy_attempt",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    project_id=project_id
                )

                result = self._develop_growth_strategy(
                    product_details=product_details,
                    target_audience=target_audience,
                    value_proposition=value_proposition,
                    pricing_model=pricing_model,
                    budget_range=budget_range,
                    growth_stage=growth_stage,
                    competitors=competitors,
                    unique_features=unique_features,
                    execution=execution,
                    db=db
                )

                logger.info(
                    "growth_strategy_success",
                    attempt=attempt,
                    project_id=project_id
                )

                return result

            except ValueError as ve:
                # Don't retry validation errors
                logger.error("growth_strategy_validation_error", error=str(ve))
                raise

            except Exception as e:
                last_error = e
                logger.warning(
                    "growth_strategy_attempt_failed",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    error=str(e),
                    error_type=type(e).__name__
                )

                if attempt == self.max_retries:
                    logger.error(
                        "growth_strategy_all_retries_failed",
                        project_id=project_id,
                        error=str(e)
                    )
                    raise

                # Exponential backoff: 2s, 4s, 8s
                wait_time = self.retry_delay * (2 ** (attempt - 1))
                logger.info(
                    "growth_strategy_retrying",
                    wait_time=wait_time,
                    next_attempt=attempt + 1
                )
                time.sleep(wait_time)

        # Should never reach here, but just in case
        raise last_error if last_error else Exception("Unknown error in retry logic")

    def _develop_growth_strategy(
        self,
        product_details: str,
        target_audience: str,
        value_proposition: str,
        pricing_model: str,
        budget_range: str,
        growth_stage: str,
        competitors: list,
        unique_features: list,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Develop comprehensive growth marketing strategy using Claude Sonnet 4.5

        This is the core method that calls OpenRouter API
        """
        logger.info("developing_growth_strategy", growth_stage=growth_stage, budget=budget_range)

        # Build comprehensive prompt
        competitors_str = ", ".join(competitors) if competitors else "No specific competitors provided"
        features_str = ", ".join(unique_features) if unique_features else "Standard SaaS features"

        system_prompt = self._build_system_prompt()

        user_prompt = f"""
# Growth Marketing Mission

Develop a comprehensive go-to-market and growth marketing strategy for this SaaS product.

## Product Information

**Product Details:**
{product_details}

**Target Audience:** {target_audience}

**Value Proposition:** {value_proposition if value_proposition else "To be developed in strategy"}

**Pricing Model:** {pricing_model}

**Growth Stage:** {growth_stage}

**Marketing Budget:** {budget_range}

**Competitors:** {competitors_str}

**Unique Features:** {features_str}

## Deliverables Required

Please provide the following in your response:

1. **GTM Strategy Document** (comprehensive go-to-market plan)
2. **Landing Page Copy** (headlines, CTAs, sections with actual copy)
3. **SEO Strategy** (keywords, meta tags, content plan)
4. **Acquisition Channels** (prioritized list with specific tactics)
5. **Content Strategy** (blog topics, tutorials, case studies)
6. **Email Sequences** (onboarding, nurture, retention with actual email copy)
7. **Social Media Strategy** (platform-specific tactics for LinkedIn, Twitter/X, Product Hunt)
8. **Growth Experiments** (A/B tests, funnel optimizations to try)
9. **Pricing Page Copy** (tier descriptions, comparison tables)
10. **Metrics Dashboard** (KPIs to track: CAC, LTV, conversion rates, etc.)

## Output Format

Return your response as a JSON object with these keys:
- growth_strategy (comprehensive GTM document)
- landing_page_copy (actual copy with headlines, CTAs, sections)
- seo_strategy (keywords, meta tags, content calendar)
- acquisition_channels (array of channel objects with priority and tactics)
- content_strategy (blog topics, tutorials, case studies with titles and outlines)
- email_sequences (actual email copy for each sequence)
- social_media_strategy (platform-specific tactics)
- growth_experiments (array of experiment objects with hypothesis and setup)
- pricing_page_copy (actual copy for pricing tiers)
- metrics_dashboard (KPIs with formulas and targets)

Focus on actionable, specific tactics that can be implemented immediately.
Be creative with copy but professional and conversion-focused.
"""

        # Update progress
        execution.current_task = "Calling Claude Sonnet 4.5 for growth strategy"
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
                temperature=0.7,  # Higher for creative marketing copy
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
                cost_usd=cost_usd
            )

        except Exception as api_error:
            logger.error("openrouter_api_error", error=str(api_error))
            raise

        # Update progress
        execution.current_task = "Parsing growth marketing deliverables"
        execution.progress = 70
        try:
            db.commit()
        except Exception:
            db.rollback()

        # Parse response (try JSON first, fall back to structured text)
        result = self._parse_growth_strategy_response(content)

        # Update progress
        execution.current_task = "Finalizing growth marketing package"
        execution.progress = 90
        try:
            db.commit()
        except Exception:
            db.rollback()

        return {
            **result,
            "tokens_used": tokens_used,
            "cost_usd": round(cost_usd, 4)
        }

    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt for Growth Marketer agent"""
        return """You are a **Senior Growth Marketer** specializing in SaaS go-to-market strategy and growth marketing.

# Your Expertise

## Core Competencies
- Go-to-market (GTM) strategy for SaaS products
- Landing page optimization and conversion copywriting
- SEO strategy (technical SEO, content SEO, keyword research)
- Growth experiment design (A/B tests, funnel optimization)
- Customer acquisition strategy (paid, organic, viral, referral)
- Content marketing (blogging, tutorials, case studies, video)
- Email marketing (onboarding, nurture, retention, win-back)
- Social media marketing (LinkedIn, Twitter/X, Product Hunt, Reddit)
- Pricing strategy and pricing page optimization
- Product-led growth (PLG) tactics
- Analytics and metrics (CAC, LTV, conversion rates, retention)

## Marketing Channels You Master
1. **Organic Channels**
   - SEO (content, technical, backlinks)
   - Content marketing (blog, YouTube, podcasts)
   - Social media (LinkedIn, Twitter/X, Product Hunt)
   - Community building (Reddit, Discord, Slack)
   - Product-led growth (free tier, viral loops)

2. **Paid Channels**
   - Google Ads (Search, Display, YouTube)
   - LinkedIn Ads (B2B focus)
   - Facebook/Instagram Ads
   - Twitter/X Ads
   - Reddit Ads
   - Retargeting campaigns

3. **Referral & Viral**
   - Referral programs (give $X, get $Y)
   - Viral loops (invite friends to unlock features)
   - Affiliate programs
   - Integration partnerships

## Your Workflow

1. **Market Analysis**
   - Identify target audience segments
   - Analyze competitors' positioning and tactics
   - Find market gaps and opportunities
   - Develop unique value proposition

2. **GTM Strategy**
   - Define launch phases (pre-launch, launch, post-launch)
   - Choose primary and secondary acquisition channels
   - Set growth targets and KPIs
   - Allocate budget across channels

3. **Copywriting**
   - Write compelling headlines (benefit-driven, clear, urgent)
   - Craft strong CTAs (action-oriented, specific, friction-free)
   - Create social proof sections (testimonials, logos, stats)
   - Develop feature/benefit descriptions

4. **SEO Optimization**
   - Keyword research (high-intent, low-competition keywords)
   - Meta tags optimization (titles, descriptions, Open Graph)
   - Content strategy (pillar pages, clusters, FAQs)
   - Technical SEO (speed, mobile, schema markup)

5. **Growth Experiments**
   - Funnel analysis (identify drop-off points)
   - A/B test hypotheses (headlines, CTAs, pricing, copy)
   - Conversion rate optimization (forms, checkout, onboarding)
   - Retention experiments (emails, features, engagement)

6. **Content Strategy**
   - Blog topics (SEO-driven, educational, problem-solving)
   - Tutorial content (how-tos, guides, walkthroughs)
   - Case studies (success stories, ROI, before/after)
   - Video content (demos, explainers, testimonials)

7. **Email Marketing**
   - Onboarding sequence (welcome, setup, first win)
   - Nurture sequence (education, use cases, tips)
   - Retention sequence (engagement, feature discovery)
   - Win-back sequence (re-engagement for inactive users)

8. **Metrics & Analytics**
   - CAC (Customer Acquisition Cost) by channel
   - LTV (Lifetime Value) by cohort
   - Conversion rates (visitor → signup → paid)
   - Retention rates (Day 1, Week 1, Month 1)
   - Viral coefficient (if applicable)
   - Payback period

## Output Requirements

**IMPORTANT:** Return your strategy as a well-structured JSON object with these exact keys:

```json
{
  "growth_strategy": "Comprehensive GTM document (markdown formatted)",
  "landing_page_copy": "Complete landing page copy with headlines, CTAs, sections",
  "seo_strategy": "SEO plan with keywords, meta tags, content calendar",
  "acquisition_channels": [
    {
      "channel": "SEO",
      "priority": "Primary",
      "tactics": ["Specific tactic 1", "Specific tactic 2"],
      "budget": "$X-Y/month",
      "expected_cac": "$Z",
      "expected_ltv": "$W"
    }
  ],
  "content_strategy": "Blog topics, tutorials, case studies with titles and outlines",
  "email_sequences": "Actual email copy for onboarding, nurture, retention sequences",
  "social_media_strategy": "Platform-specific tactics for LinkedIn, Twitter, Product Hunt",
  "growth_experiments": [
    {
      "experiment": "Test headline variations",
      "hypothesis": "Benefit-driven headline will increase signups by 20%",
      "setup": "A/B test 3 headlines, split traffic 33/33/33, run for 2 weeks"
    }
  ],
  "pricing_page_copy": "Pricing tier descriptions, feature comparisons, CTAs",
  "metrics_dashboard": "KPIs to track with formulas and targets"
}
```

## Best Practices

### Landing Page Copy
- Headlines: Benefit-driven, clear, specific (e.g., "Ship Your SaaS 10x Faster")
- Subheadings: Expand on benefit, add urgency
- CTAs: Action verbs, specific outcomes (e.g., "Start Building Free" not "Sign Up")
- Social proof: Testimonials, logos, metrics (e.g., "Trusted by 500+ founders")
- Feature benefits: Focus on outcomes, not features (e.g., "Save 40 hours/week" not "Automated workflows")

### SEO Strategy
- Focus on long-tail keywords (e.g., "best project management tool for remote teams")
- Target high-intent keywords (e.g., "buy", "best", "vs", "alternative")
- Create pillar pages + cluster content
- Optimize for featured snippets (lists, tables, definitions)

### Growth Experiments
- Start with highest-impact, lowest-effort experiments
- Run experiments for statistical significance (1-2 weeks minimum)
- Document learnings (what worked, what didn't, why)
- Compound wins (implement winners, iterate on losers)

### Email Sequences
- Keep emails short (< 150 words)
- One clear CTA per email
- Personalize with user data (name, use case, behavior)
- A/B test subject lines for open rates

### Metrics Targets (B2B SaaS)
- Visitor → Signup: 5-15%
- Signup → Paid: 10-25%
- Monthly churn: < 5%
- CAC payback: < 12 months
- LTV:CAC ratio: > 3:1

Be specific, actionable, and data-driven in all recommendations.
"""

    def _parse_growth_strategy_response(self, content: str) -> Dict[str, Any]:
        """
        Parse Claude's response into structured growth strategy

        Tries JSON parsing first, falls back to text extraction
        """
        import json
        import re

        try:
            # Try parsing as JSON
            if "```json" in content:
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(1))
                    logger.info("parsed_json_from_code_block")
                    return parsed

            # Try parsing entire content as JSON
            if content.strip().startswith('{'):
                parsed = json.loads(content)
                logger.info("parsed_json_directly")
                return parsed

        except json.JSONDecodeError as e:
            logger.warning("json_parse_failed", error=str(e), fallback="text_extraction")

        # Fallback: Extract sections from markdown/text
        logger.info("using_text_extraction_fallback")

        result = {
            "growth_strategy": self._extract_section(content, ["growth_strategy", "gtm strategy", "go-to-market"]),
            "landing_page_copy": self._extract_section(content, ["landing_page_copy", "landing page", "homepage copy"]),
            "seo_strategy": self._extract_section(content, ["seo_strategy", "seo", "search optimization"]),
            "acquisition_channels": self._extract_channels(content),
            "content_strategy": self._extract_section(content, ["content_strategy", "content marketing", "blog strategy"]),
            "email_sequences": self._extract_section(content, ["email_sequences", "email marketing", "email copy"]),
            "social_media_strategy": self._extract_section(content, ["social_media_strategy", "social media", "social marketing"]),
            "growth_experiments": self._extract_experiments(content),
            "pricing_page_copy": self._extract_section(content, ["pricing_page_copy", "pricing page", "pricing tiers"]),
            "metrics_dashboard": self._extract_section(content, ["metrics_dashboard", "kpis", "analytics"])
        }

        return result

    def _extract_section(self, content: str, section_keywords: list) -> str:
        """Extract a section from markdown content based on keywords"""
        import re

        for keyword in section_keywords:
            # Try finding markdown heading
            pattern = rf'#{{1,3}}\s*{re.escape(keyword)}.*?\n(.*?)(?=\n#{{1,3}}\s|\Z)'
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

            # Try finding JSON key
            pattern = rf'"{re.escape(keyword)}"\s*:\s*"(.*?)"'
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        # Fallback
        return f"Section not found. Full content:\n\n{content[:500]}..."

    def _extract_channels(self, content: str) -> list:
        """Extract acquisition channels as structured list"""
        import re

        channels = []

        # Try to find channel sections
        channel_patterns = [
            r'(?:Primary|Secondary|Tertiary)\s+(?:Channel|Acquisition):\s*([^\n]+)',
            r'Channel:\s*([^\n]+)',
            r'(?:SEO|Content|Paid|Social|Referral|Email|Community)\s+Marketing'
        ]

        for pattern in channel_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                channel_name = match.group(0) if match.groups() == () else match.group(1)
                channels.append({
                    "channel": channel_name.strip(),
                    "priority": "To be determined",
                    "tactics": ["See full strategy document"],
                    "budget": "See full strategy document",
                    "expected_cac": "TBD",
                    "expected_ltv": "TBD"
                })

        if not channels:
            # Default channels
            channels = [
                {"channel": "SEO", "priority": "Primary", "tactics": ["See full strategy document"], "budget": "TBD", "expected_cac": "TBD", "expected_ltv": "TBD"},
                {"channel": "Content Marketing", "priority": "Primary", "tactics": ["See full strategy document"], "budget": "TBD", "expected_cac": "TBD", "expected_ltv": "TBD"}
            ]

        return channels

    def _extract_experiments(self, content: str) -> list:
        """Extract growth experiments as structured list"""
        import re

        experiments = []

        # Try to find experiment sections
        exp_pattern = r'(?:Experiment|Test|A/B Test):\s*([^\n]+)'
        matches = re.finditer(exp_pattern, content, re.IGNORECASE)

        for match in matches:
            experiments.append({
                "experiment": match.group(1).strip(),
                "hypothesis": "See full strategy document",
                "setup": "See full strategy document"
            })

        if not experiments:
            # Default experiments
            experiments = [
                {"experiment": "Headline A/B test", "hypothesis": "See full strategy document", "setup": "See full strategy document"},
                {"experiment": "CTA button optimization", "hypothesis": "See full strategy document", "setup": "See full strategy document"}
            ]

        return experiments

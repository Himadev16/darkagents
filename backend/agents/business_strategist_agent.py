"""
Agent 09: Business Strategist
Business model development and financial strategy for SaaS products
"""
import time
from typing import Dict, Any
import structlog
from sqlalchemy.orm import Session

from backend.database.models import AgentExecution
from backend.agents.base_agent import BaseAgent
from backend.services.claude_service import claude_service

logger = structlog.get_logger()


class BusinessStrategistAgent(BaseAgent):
    """
    Business Strategist Agent

    Senior business strategist specializing in SaaS business models and financial strategy.

    Capabilities:
    - Business model canvas development (9 building blocks)
    - Revenue modeling (projections, scenarios, unit economics)
    - Pricing strategy (tiers, value-based pricing, psychological pricing)
    - Competitive analysis (SWOT, Porter's Five Forces, positioning)
    - Financial modeling (P&L, cash flow, burn rate, runway)
    - Market sizing (TAM, SAM, SOM)
    - Unit economics (CAC, LTV, payback period, gross margin)
    - Go-to-market strategy validation
    - Funding strategy (bootstrap, angel, VC, revenue-based financing)
    - Exit strategy planning

    Input: Product details, market info, financial assumptions from previous agents
    Output: Comprehensive business strategy package with financial models

    Production Features:
    - Retry logic with exponential backoff (3 retries)
    - Input validation with detailed error messages
    - Database transaction management with rollback
    - Graceful error handling
    - Detailed structured logging
    """

    def __init__(self):
        """Initialize Business Strategist Agent"""
        self.agent_name = "business_strategist"
        self.agent_display_name = "Business Strategist"
        self.max_retries = 3
        self.retry_delay = 2  # Base delay in seconds for exponential backoff

    def execute(self, project_id: int, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Execute Business Strategist Agent

        Args:
            project_id: Project ID
            input_data: {
                "product_details": str (PRD or product description),
                "target_market": str (optional, e.g., "B2B SaaS for SMBs"),
                "pricing_model": str (optional, e.g., "freemium", "subscription", "usage-based"),
                "revenue_target": str (optional, e.g., "$1M ARR in 12 months"),
                "funding_stage": str (optional, e.g., "bootstrapped", "pre-seed", "seed"),
                "team_size": int (optional, current team size),
                "burn_rate": float (optional, monthly burn rate in USD),
                "runway_months": int (optional, current runway in months),
                "competitors": list (optional, e.g., ["Notion", "Airtable"]),
                "unique_value_proposition": str (optional)
            }
            db: Database session

        Returns:
            {
                "success": bool,
                "business_model_canvas": str (9 building blocks),
                "revenue_model": str (Revenue streams, pricing tiers, projections),
                "pricing_strategy": str (Pricing analysis, recommendations, psychology),
                "competitive_analysis": str (SWOT, Porter's Five Forces, positioning map),
                "financial_model": str (P&L, cash flow, burn rate, runway calculations),
                "market_sizing": str (TAM, SAM, SOM with calculations),
                "unit_economics": str (CAC, LTV, payback, margins with formulas),
                "funding_strategy": str (Funding options, timeline, milestones),
                "growth_roadmap": str (12-month roadmap with milestones and metrics),
                "risk_analysis": str (Top risks and mitigation strategies),
                "execution_id": int,
                "tokens_used": int,
                "cost_usd": float,
                "error": str (if success=False)
            }
        """
        execution = None
        try:
            logger.info(
                "business_strategist_agent_started",
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
            target_market = input_data.get("target_market", "B2B SaaS for startups and SMBs")
            pricing_model = input_data.get("pricing_model", "subscription")
            revenue_target = input_data.get("revenue_target", "$1M ARR in 24 months")
            funding_stage = input_data.get("funding_stage", "bootstrapped")
            team_size = input_data.get("team_size", 2)
            burn_rate = input_data.get("burn_rate", 10000.0)
            runway_months = input_data.get("runway_months", 12)
            competitors = input_data.get("competitors", [])
            unique_value_proposition = input_data.get("unique_value_proposition", "")

            # Validate optional fields
            if not isinstance(team_size, int) or team_size < 0:
                team_size = 2
            if not isinstance(burn_rate, (int, float)) or burn_rate < 0:
                burn_rate = 10000.0
            if not isinstance(runway_months, int) or runway_months < 0:
                runway_months = 12
            if not isinstance(competitors, list):
                competitors = []

            # Create database record
            try:
                execution = AgentExecution(
                    project_id=project_id,
                    agent_name=self.agent_name,
                    agent_display_name=self.agent_display_name,
                    status="working",
                    progress=0,
                    current_task="Analyzing business model and market opportunity",
                    tokens_used=0,
                    cost_usd=0.0
                )
                db.add(execution)
                db.commit()
                db.refresh(execution)

                logger.info(
                    "business_strategist_execution_created",
                    execution_id=execution.id,
                    project_id=project_id
                )
            except Exception as db_error:
                logger.error("database_error_creating_execution", error=str(db_error))
                db.rollback()
                raise

            # Update progress
            execution.current_task = "Developing business model canvas"
            execution.progress = 10
            try:
                db.commit()
            except Exception:
                db.rollback()

            # Develop business strategy with retry logic
            result = self._develop_business_strategy_with_retry(
                product_details=product_details,
                target_market=target_market,
                pricing_model=pricing_model,
                revenue_target=revenue_target,
                funding_stage=funding_stage,
                team_size=team_size,
                burn_rate=burn_rate,
                runway_months=runway_months,
                competitors=competitors,
                unique_value_proposition=unique_value_proposition,
                project_id=project_id,
                execution=execution,
                db=db
            )

            # Update execution record with results
            try:
                execution.status = "completed"
                execution.progress = 100
                execution.current_task = "Business strategy package complete"
                execution.tokens_used = result.get("tokens_used", 0)
                execution.cost_usd = result.get("cost_usd", 0.0)
                db.commit()

                logger.info(
                    "business_strategist_agent_completed",
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
                "business_strategist_validation_error",
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
                "business_strategist_agent_failed",
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

    def _develop_business_strategy_with_retry(
        self,
        product_details: str,
        target_market: str,
        pricing_model: str,
        revenue_target: str,
        funding_stage: str,
        team_size: int,
        burn_rate: float,
        runway_months: int,
        competitors: list,
        unique_value_proposition: str,
        project_id: int,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Develop business strategy with retry logic (exponential backoff)

        Retries up to max_retries times with exponential backoff on transient errors
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "business_strategy_attempt",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    project_id=project_id
                )

                result = self._develop_business_strategy(
                    product_details=product_details,
                    target_market=target_market,
                    pricing_model=pricing_model,
                    revenue_target=revenue_target,
                    funding_stage=funding_stage,
                    team_size=team_size,
                    burn_rate=burn_rate,
                    runway_months=runway_months,
                    competitors=competitors,
                    unique_value_proposition=unique_value_proposition,
                    execution=execution,
                    db=db
                )

                logger.info(
                    "business_strategy_success",
                    attempt=attempt,
                    project_id=project_id
                )

                return result

            except ValueError as ve:
                # Don't retry validation errors
                logger.error("business_strategy_validation_error", error=str(ve))
                raise

            except Exception as e:
                last_error = e
                logger.warning(
                    "business_strategy_attempt_failed",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    error=str(e),
                    error_type=type(e).__name__
                )

                if attempt == self.max_retries:
                    logger.error(
                        "business_strategy_all_retries_failed",
                        project_id=project_id,
                        error=str(e)
                    )
                    raise

                # Exponential backoff: 2s, 4s, 8s
                wait_time = self.retry_delay * (2 ** (attempt - 1))
                logger.info(
                    "business_strategy_retrying",
                    wait_time=wait_time,
                    next_attempt=attempt + 1
                )
                time.sleep(wait_time)

        # Should never reach here, but just in case
        raise last_error if last_error else Exception("Unknown error in retry logic")

    def _develop_business_strategy(
        self,
        product_details: str,
        target_market: str,
        pricing_model: str,
        revenue_target: str,
        funding_stage: str,
        team_size: int,
        burn_rate: float,
        runway_months: int,
        competitors: list,
        unique_value_proposition: str,
        execution: AgentExecution,
        db: Session
    ) -> Dict[str, Any]:
        """
        Develop comprehensive business strategy using Claude Sonnet 4.5

        This is the core method that calls OpenRouter API
        """
        logger.info("developing_business_strategy", funding_stage=funding_stage, revenue_target=revenue_target)

        # Build comprehensive prompt
        competitors_str = ", ".join(competitors) if competitors else "No specific competitors provided"

        system_prompt = self._build_system_prompt()

        user_prompt = f"""
# Business Strategy Mission

Develop a comprehensive business strategy and financial model for this SaaS product.

## Product Information

**Product Details:**
{product_details}

**Target Market:** {target_market}

**Pricing Model:** {pricing_model}

**Revenue Target:** {revenue_target}

**Funding Stage:** {funding_stage}

**Current Team Size:** {team_size} people

**Monthly Burn Rate:** ${burn_rate:,.2f}

**Current Runway:** {runway_months} months

**Competitors:** {competitors_str}

**Unique Value Proposition:** {unique_value_proposition if unique_value_proposition else "To be developed in strategy"}

## Deliverables Required

Please provide the following in your response:

1. **Business Model Canvas** (9 building blocks: Customer Segments, Value Propositions, Channels, Customer Relationships, Revenue Streams, Key Resources, Key Activities, Key Partnerships, Cost Structure)

2. **Revenue Model** (Revenue streams, pricing tiers with actual numbers, 24-month revenue projections with assumptions)

3. **Pricing Strategy** (Pricing analysis, tier recommendations, psychological pricing tactics, competitive pricing comparison)

4. **Competitive Analysis** (SWOT analysis, Porter's Five Forces, competitive positioning map, differentiation strategy)

5. **Financial Model** (24-month P&L projection, cash flow analysis, burn rate optimization, runway extension plan)

6. **Market Sizing** (TAM, SAM, SOM calculations with methodology and sources)

7. **Unit Economics** (CAC calculation, LTV calculation, CAC payback period, LTV:CAC ratio, gross margin, contribution margin)

8. **Funding Strategy** (Funding options analysis, recommended path, funding timeline, key milestones for next raise)

9. **Growth Roadmap** (12-month roadmap with quarterly milestones, metrics targets, hiring plan, product roadmap)

10. **Risk Analysis** (Top 5-7 business risks with likelihood, impact, and mitigation strategies)

## Output Format

Return your response as a JSON object with these keys:
- business_model_canvas (9 blocks with detailed descriptions)
- revenue_model (revenue streams, tiers, 24-month projections)
- pricing_strategy (pricing analysis, recommendations, psychology)
- competitive_analysis (SWOT, Porter's Five Forces, positioning)
- financial_model (P&L, cash flow, burn rate analysis)
- market_sizing (TAM/SAM/SOM with calculations)
- unit_economics (CAC, LTV, payback, margins with formulas)
- funding_strategy (options, recommendations, timeline)
- growth_roadmap (12-month plan with milestones)
- risk_analysis (top risks with mitigation plans)

Be specific with numbers, formulas, and actionable recommendations.
"""

        # Update progress
        execution.current_task = "Calling Claude Sonnet 4.5 for business strategy"
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
                temperature=0.4,  # Balanced for strategic + analytical thinking
                max_tokens=14000
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
        execution.current_task = "Parsing business strategy deliverables"
        execution.progress = 70
        try:
            db.commit()
        except Exception:
            db.rollback()

        # Parse response (try JSON first, fall back to structured text)
        result = self._parse_business_strategy_response(content)

        # Update progress
        execution.current_task = "Finalizing business strategy package"
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
        """Build comprehensive system prompt for Business Strategist agent"""
        return """You are a **Senior Business Strategist** specializing in SaaS business models and financial strategy.

# Your Expertise

## Core Competencies
- Business model development (Business Model Canvas, Lean Canvas)
- Financial modeling (P&L, cash flow, burn rate, runway)
- Revenue strategy (pricing, monetization, unit economics)
- Market analysis (TAM/SAM/SOM, competitive landscape)
- Strategic planning (vision, mission, roadmap, OKRs)
- Fundraising strategy (bootstrapping, angels, VCs, RBF)
- Unit economics optimization (CAC, LTV, payback, margins)
- Competitive strategy (differentiation, positioning, moats)
- Risk management (identification, assessment, mitigation)
- Exit strategy planning (M&A, IPO, strategic partnerships)

## Frameworks You Master

### Business Model Canvas (9 Building Blocks)
1. **Customer Segments** - Who are we serving?
2. **Value Propositions** - What problem do we solve?
3. **Channels** - How do we reach customers?
4. **Customer Relationships** - How do we acquire, retain, grow?
5. **Revenue Streams** - How do we make money?
6. **Key Resources** - What assets do we need?
7. **Key Activities** - What must we do?
8. **Key Partnerships** - Who can help us?
9. **Cost Structure** - What are our major costs?

### Financial Metrics (SaaS)
- **ARR/MRR** - Annual/Monthly Recurring Revenue
- **CAC** - Customer Acquisition Cost = (Sales + Marketing) / New Customers
- **LTV** - Lifetime Value = ARPU × Gross Margin % / Churn Rate
- **CAC Payback** - Months to recover CAC = CAC / (ARPU × Gross Margin %)
- **LTV:CAC Ratio** - Target: > 3:1 (sustainable), > 5:1 (excellent)
- **Gross Margin** - Target: > 70% for SaaS
- **Burn Rate** - Monthly cash consumption
- **Runway** - Months of cash remaining = Cash / Burn Rate
- **Rule of 40** - Growth % + Profit Margin % > 40%

### Competitive Analysis
- **SWOT** - Strengths, Weaknesses, Opportunities, Threats
- **Porter's Five Forces** - Competition, Suppliers, Buyers, Substitutes, New Entrants
- **Positioning Map** - 2D map showing competitive positioning
- **Differentiation** - What makes us unique and defensible?

### Market Sizing
- **TAM** (Total Addressable Market) - Total market demand
- **SAM** (Serviceable Addressable Market) - Segment we can serve
- **SOM** (Serviceable Obtainable Market) - Market we can capture (realistic)

### Pricing Strategy
- **Value-based pricing** - Price based on value delivered
- **Cost-plus pricing** - Price = Cost + Markup
- **Competitive pricing** - Match or undercut competitors
- **Penetration pricing** - Low price to gain market share
- **Freemium** - Free tier + paid upgrades
- **Usage-based** - Pay per use/consumption
- **Tiered pricing** - Good/Better/Best

## Your Workflow

1. **Understand the Business**
   - Analyze product, target market, value proposition
   - Review competitive landscape and differentiation
   - Assess team capabilities and resources

2. **Develop Business Model**
   - Complete Business Model Canvas (9 blocks)
   - Define revenue streams and pricing
   - Map customer journey and channels
   - Identify key partnerships and resources

3. **Build Financial Model**
   - Project revenue (3 scenarios: conservative, base, optimistic)
   - Estimate costs (COGS, R&D, S&M, G&A)
   - Calculate unit economics (CAC, LTV, payback, margins)
   - Model cash flow and runway

4. **Analyze Market & Competition**
   - Size the market (TAM, SAM, SOM)
   - Perform SWOT analysis
   - Apply Porter's Five Forces
   - Create competitive positioning map

5. **Design Pricing Strategy**
   - Analyze value delivered to customers
   - Research competitive pricing
   - Design pricing tiers (features, limits, pricing)
   - Apply psychological pricing tactics

6. **Plan Growth & Fundraising**
   - Set revenue and growth targets
   - Build 12-month roadmap with milestones
   - Determine funding needs and timeline
   - Recommend funding strategy (bootstrap vs raise)

7. **Assess Risks**
   - Identify top business risks
   - Assess likelihood and impact
   - Develop mitigation strategies
   - Create contingency plans

## Output Requirements

**IMPORTANT:** Return your strategy as a well-structured JSON object with these exact keys:

```json
{
  "business_model_canvas": {
    "customer_segments": "...",
    "value_propositions": "...",
    "channels": "...",
    "customer_relationships": "...",
    "revenue_streams": "...",
    "key_resources": "...",
    "key_activities": "...",
    "key_partnerships": "...",
    "cost_structure": "..."
  },
  "revenue_model": "Revenue streams, pricing tiers with numbers, 24-month projections",
  "pricing_strategy": "Pricing analysis, tier recommendations, psychological tactics",
  "competitive_analysis": "SWOT, Porter's Five Forces, positioning map",
  "financial_model": "24-month P&L, cash flow, burn rate analysis",
  "market_sizing": "TAM/SAM/SOM with calculations and methodology",
  "unit_economics": "CAC, LTV, payback, margins with formulas and targets",
  "funding_strategy": "Funding options, recommended path, timeline, milestones",
  "growth_roadmap": "12-month roadmap with quarterly milestones and metrics",
  "risk_analysis": "Top 5-7 risks with likelihood, impact, mitigation strategies"
}
```

## Best Practices

### Revenue Projections
- Use 3 scenarios: Conservative (70% of base), Base (realistic), Optimistic (130% of base)
- Show monthly revenue for first 12 months, quarterly for months 13-24
- Include assumptions (conversion rates, ARPU, churn)
- Be realistic - avoid hockey stick projections without justification

### Unit Economics
- Calculate CAC by channel (organic, paid, referral)
- Factor in all costs (S&M, discounts, free trials)
- Calculate LTV with realistic churn assumptions
- Target LTV:CAC > 3:1, CAC payback < 12 months

### Pricing Tiers
- Offer 3-4 tiers (Good, Better, Best, Enterprise)
- Anchor pricing on middle tier (most popular)
- Use psychological pricing ($29 vs $30, $99 vs $100)
- Include usage limits that encourage upgrades

### Market Sizing
- Start with top-down (total market size)
- Validate with bottom-up (customers × ARPU)
- Be conservative with SOM (1-5% of TAM is realistic for startups)
- Cite sources for market data

### Funding Strategy
- Bootstrap if possible (maintain control, avoid dilution)
- Angel/Pre-seed: $100K-$500K for MVP + early traction
- Seed: $500K-$2M for product-market fit
- Series A: $2M-$10M for scaling proven model
- Consider alternatives: RBF, venture debt, grants

Be specific, data-driven, and actionable in all recommendations.
"""

    def _parse_business_strategy_response(self, content: str) -> Dict[str, Any]:
        """
        Parse Claude's response into structured business strategy

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
            "business_model_canvas": self._extract_business_model_canvas(content),
            "revenue_model": self._extract_section(content, ["revenue_model", "revenue model", "revenue streams"]),
            "pricing_strategy": self._extract_section(content, ["pricing_strategy", "pricing strategy", "pricing"]),
            "competitive_analysis": self._extract_section(content, ["competitive_analysis", "competitive analysis", "swot", "competition"]),
            "financial_model": self._extract_section(content, ["financial_model", "financial model", "p&l", "projections"]),
            "market_sizing": self._extract_section(content, ["market_sizing", "market sizing", "tam sam som"]),
            "unit_economics": self._extract_section(content, ["unit_economics", "unit economics", "cac ltv"]),
            "funding_strategy": self._extract_section(content, ["funding_strategy", "funding strategy", "fundraising"]),
            "growth_roadmap": self._extract_section(content, ["growth_roadmap", "growth roadmap", "roadmap"]),
            "risk_analysis": self._extract_section(content, ["risk_analysis", "risk analysis", "risks"])
        }

        return result

    def _extract_business_model_canvas(self, content: str) -> str:
        """Extract Business Model Canvas from content"""
        import re

        # Try to find BMC section
        pattern = r'#{{1,3}}\s*business model canvas.*?\n(.*?)(?=\n#{{1,3}}\s|\Z)'
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()

        # Fallback: Return full content snippet
        return f"Business Model Canvas not found. See full content for details.\n\n{content[:500]}..."

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

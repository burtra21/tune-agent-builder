"""
Prospect Intelligence Engine
Web research, intent detection, and advanced scoring
(Works with Clay-enriched data as input)
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import anthropic
import httpx


class WebResearchEngine:
    """Conducts intelligent web research on prospects"""

    def __init__(self, claude_api_key: str):
        self.client = anthropic.Anthropic(api_key=claude_api_key)
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; TuneResearchBot/1.0)'}
        )

    async def research_company(self, company_name: str, domain: str,
                              intent_signals_to_find: List[str]) -> Dict[str, Any]:
        """Conduct comprehensive web research on company"""

        print(f"🔍 Researching {company_name}...")

        # Parallel research tasks
        research_tasks = [
            self._search_sustainability_page(domain),
            self._search_esg_reports(domain),
            self._analyze_about_page(domain),
            self._check_careers_page(domain),  # Job postings for intent
            self._search_news_google(company_name),
        ]

        results = await asyncio.gather(*research_tasks, return_exceptions=True)

        # Compile research
        research_data = {
            "sustainability_page": results[0] if not isinstance(results[0], Exception) else None,
            "esg_reports": results[1] if not isinstance(results[1], Exception) else None,
            "about_page": results[2] if not isinstance(results[2], Exception) else None,
            "careers_insights": results[3] if not isinstance(results[3], Exception) else None,
            "news_mentions": results[4] if not isinstance(results[4], Exception) else [],
        }

        # Synthesize with Claude
        synthesis = await self._synthesize_research(company_name, research_data, intent_signals_to_find)

        return synthesis

    async def _search_sustainability_page(self, domain: str) -> Optional[Dict]:
        """Search for sustainability/ESG page"""

        paths = [
            '/sustainability', '/esg', '/corporate-responsibility',
            '/environmental', '/about/sustainability', '/csr'
        ]

        for path in paths:
            try:
                url = f"https://{domain}{path}"
                response = await self.http_client.get(url, timeout=10.0)
                if response.status_code == 200:
                    page_text = response.text[:10000]  # First 10k chars
                    analysis = await self._analyze_sustainability_content(page_text)

                    return {
                        "url": url,
                        "found": True,
                        "analysis": analysis
                    }
            except:
                continue

        return {"found": False}

    async def _analyze_sustainability_content(self, content: str) -> Dict:
        """Analyze sustainability page content"""

        prompt = f"""Analyze this sustainability/ESG page and extract buying intent signals for energy efficiency solutions:

{content[:5000]}

Extract and return as JSON:
{{
  "carbon_targets": ["specific target with date"],
  "certifications": ["LEED", "Energy Star", etc],
  "esg_reporting": true/false,
  "energy_initiatives": ["specific initiatives mentioned"],
  "sustainability_commitments": ["specific commitments"],
  "intent_strength": 0-100 (how serious are they about sustainability?)
}}

Be specific with quotes where possible."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text

        try:
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
                return json.loads(json_str)
            else:
                return {"raw_analysis": response_text}
        except:
            return {"raw_analysis": response_text}

    async def _search_esg_reports(self, domain: str) -> Optional[Dict]:
        """Search for ESG/sustainability reports"""

        paths = [
            '/investors/esg', '/sustainability-report', '/esg-report',
            '/corporate-responsibility-report', '/impact-report'
        ]

        for path in paths:
            try:
                url = f"https://{domain}{path}"
                response = await self.http_client.get(url, timeout=10.0)
                if response.status_code == 200:
                    return {
                        "found": True,
                        "url": url,
                        "signal": "Company publishes ESG reports - HIGH sustainability commitment",
                        "confidence": 90
                    }
            except:
                continue

        return {"found": False, "confidence": 0}

    async def _analyze_about_page(self, domain: str) -> Optional[Dict]:
        """Analyze company about page for growth/values signals"""

        try:
            url = f"https://{domain}/about"
            response = await self.http_client.get(url, timeout=10.0)

            if response.status_code == 200:
                content = response.text[:8000]

                prompt = f"""Analyze this company About page for buying signals:

{content[:4000]}

Extract as JSON:
{{
  "growth_signals": ["expansion mentions", "new locations", etc],
  "values": ["sustainability", "innovation", etc if mentioned],
  "company_stage": "startup/growth/mature",
  "employee_growth": "any mentions of headcount growth"
}}"""

                message = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}]
                )

                return {"analysis": message.content[0].text}
        except:
            pass

        return None

    async def _check_careers_page(self, domain: str) -> Optional[Dict]:
        """Check careers page for hiring signals (intent indicator)"""

        try:
            url = f"https://{domain}/careers"
            response = await self.http_client.get(url, timeout=10.0)

            if response.status_code == 200:
                content = response.text.lower()

                # Look for sustainability/energy-related roles
                intent_roles = [
                    'sustainability', 'esg', 'energy manager', 'facilities',
                    'environmental', 'carbon', 'chief sustainability'
                ]

                found_roles = [role for role in intent_roles if role in content]

                if found_roles:
                    return {
                        "hiring_intent_roles": found_roles,
                        "signal": f"Hiring for: {', '.join(found_roles)}",
                        "confidence": 85
                    }

                # Check for general growth (expansion = need for efficiency)
                if content.count('position') > 10 or content.count('hiring') > 5:
                    return {
                        "signal": "High hiring activity - company growth phase",
                        "confidence": 60
                    }
        except:
            pass

        return None

    async def _search_news_google(self, company_name: str) -> List[Dict]:
        """Search for recent news (simulate - in production use News API)"""

        # In production, use Google News API or similar
        # For now, use Claude's reasoning about likely recent events

        prompt = f"""Based on general industry knowledge, what recent developments would {company_name} LIKELY have that indicate energy efficiency buying intent?

Consider:
- Facility expansions
- Sustainability announcements
- New executive hires (ESG/Sustainability)
- Rising energy costs concerns
- Green certifications

Return 2-3 plausible recent events as JSON array:
[{{"event": "...", "relevance_to_energy": "...", "estimated_date": "2024-XX"}}]

Only include if you're reasonably confident these types of events are common for this type of company."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            content = message.content[0].text
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0].strip()
                return json.loads(json_str)
        except:
            pass

        return []

    async def _synthesize_research(self, company_name: str, research_data: Dict,
                                   intent_signals: List[str]) -> Dict:
        """Synthesize all research into actionable intelligence"""

        prompt = f"""Synthesize web research on {company_name} and identify buying intent for energy efficiency solutions.

RESEARCH DATA:
{json.dumps(research_data, indent=2, default=str)}

INTENT SIGNALS TO LOOK FOR:
{json.dumps(intent_signals, indent=2)}

Provide as JSON:
{{
  "intent_signals_found": {{
    "sustainability_commitments": [{{"signal": "...", "evidence": "...", "confidence": 0-100}}],
    "expansion_signals": [...],
    "hiring_signals": [...],
    "esg_reporting": [...]
  }},
  "sustainability_maturity": 1-5,
  "urgency_score": 0-100,
  "key_personalization_points": ["specific detail 1", "specific detail 2", ...],
  "recommended_messaging": "what angle to lead with"
}}

Be specific with evidence. Score confidence based on strength of evidence."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )

        content = message.content[0].text

        try:
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0].strip()
                return json.loads(json_str)
            else:
                return {"raw_synthesis": content}
        except:
            return {"raw_synthesis": content}


class ProspectIntelligence:
    """Main prospect intelligence orchestrator (works with Clay-enriched data)"""

    def __init__(self, industry_agent, claude_api_key: str):
        self.agent = industry_agent
        self.web_research = WebResearchEngine(claude_api_key)
        self.claude_client = anthropic.Anthropic(api_key=claude_api_key)

    async def analyze_prospect(self, clay_enriched_data: Dict) -> Dict[str, Any]:
        """
        Complete prospect analysis

        Expects clay_enriched_data with:
        - company_name (required)
        - domain (required)
        - employee_count (from Clay enrichment)
        - industry (from Clay enrichment)
        - headquarters (from Clay enrichment)
        - revenue (from Clay enrichment)
        - etc.
        """

        company_name = clay_enriched_data["company_name"]
        domain = clay_enriched_data.get("domain") or self._guess_domain(company_name)

        print(f"\n{'='*60}")
        print(f"🎯 ANALYZING: {company_name}")
        print(f"{'='*60}\n")

        # Build company profile from Clay data
        company_profile = self._build_profile_from_clay(clay_enriched_data)

        # Web research for intent signals
        print("🔍 Conducting web research...")
        intent_signals = self.agent.intent_signals
        research = await self.web_research.research_company(
            company_name, domain,
            self._flatten_intent_signals(intent_signals)
        )

        # Calculate savings projection
        print("💰 Calculating savings projection...")
        savings = self._calculate_savings(company_profile)

        # Score prospect
        print("📈 Scoring prospect...")
        scores = await self._score_prospect(company_profile, research, savings)

        # Map personas
        print("👥 Mapping decision-maker personas...")
        persona_mapping = self._map_personas(company_profile)

        # Generate personalization intel
        print("✨ Generating personalization points...")
        personalization = await self._generate_personalization_intel(
            company_profile, research, scores
        )

        # Compile complete analysis
        analysis = {
            "company_profile": company_profile,
            "intent_signals": research.get("intent_signals_found", {}),
            "sustainability_maturity": research.get("sustainability_maturity", 2),
            "savings_projection": savings,
            "scores": scores,
            "composite_score": scores["composite"],
            "priority_tier": self._determine_priority_tier(scores["composite"]),
            "persona_mapping": persona_mapping,
            "personalization_intel": personalization,
            "recommended_messaging": research.get("recommended_messaging", "Lead with cost savings"),
            "analyzed_at": datetime.now().isoformat()
        }

        print(f"\n✅ Analysis Complete - Score: {scores['composite']}/100 (Tier {analysis['priority_tier']})\n")

        return analysis

    def _build_profile_from_clay(self, clay_data: Dict) -> Dict:
        """Build company profile from Clay-enriched data"""

        employee_count = clay_data.get("employee_count") or clay_data.get("employees") or 250
        estimated_sqft = employee_count * 200  # 200 sqft per employee estimate

        # Energy spend estimation (industry-specific if available)
        energy_cost_per_sqft = 15  # Default $/sqft/year
        estimated_energy_spend = estimated_sqft * energy_cost_per_sqft

        return {
            "company_name": clay_data["company_name"],
            "domain": clay_data.get("domain") or self._guess_domain(clay_data["company_name"]),
            "industry": clay_data.get("industry") or "Unknown",
            "employee_count": employee_count,
            "estimated_revenue": clay_data.get("revenue") or clay_data.get("estimated_revenue"),
            "locations_count": clay_data.get("locations_count") or 1,
            "headquarters": clay_data.get("headquarters") or clay_data.get("hq_location"),
            "founded_year": clay_data.get("founded_year") or clay_data.get("founded"),
            "linkedin_url": clay_data.get("linkedin_url"),
            "technologies_used": clay_data.get("technologies") or [],
            "estimated_sqft": estimated_sqft,
            "estimated_energy_spend": estimated_energy_spend
        }

    def _flatten_intent_signals(self, intent_signals: Dict) -> List[str]:
        """Flatten intent signals dict to list"""
        all_signals = []
        for category, signals in intent_signals.items():
            if isinstance(signals, list):
                all_signals.extend(signals)
        return all_signals

    def _calculate_savings(self, profile: Dict) -> Dict[str, Any]:
        """Calculate projected Tune savings"""

        savings_pct = self.agent.savings_benchmarks.get("typical_percentage", 11) / 100
        current_spend = profile["estimated_energy_spend"]
        annual_savings = current_spend * savings_pct

        # Tune cost estimation
        tune_cost_per_sqft = 3.50
        install_cost = profile["estimated_sqft"] * tune_cost_per_sqft
        payback_months = (install_cost / annual_savings) * 12 if annual_savings > 0 else 999

        return {
            "current_annual_spend": round(current_spend, 2),
            "savings_percentage": round(savings_pct * 100, 2),
            "annual_savings_dollars": round(annual_savings, 2),
            "monthly_savings_dollars": round(annual_savings / 12, 2),
            "payback_period_months": round(payback_months, 1),
            "five_year_savings": round(annual_savings * 5, 2),
            "estimated_install_cost": round(install_cost, 2),
            "roi_percentage": round((annual_savings * 5 - install_cost) / install_cost * 100, 1) if install_cost > 0 else 0,
            "carbon_reduction_tons": round(annual_savings * 0.0007, 1)  # Rough CO2 calc
        }

    async def _score_prospect(self, profile: Dict, research: Dict,
                            savings: Dict) -> Dict[str, float]:
        """Multi-dimensional prospect scoring"""

        weights = self.agent.scoring_weights

        # Intent Score (0-100)
        intent_score = self._calculate_intent_score(research)

        # Technical Fit Score (0-100)
        tech_fit_score = self._calculate_technical_fit(profile, savings)

        # Urgency Score (0-100)
        urgency_score = research.get("urgency_score", 50)

        # Persona Quality Score (0-100)
        persona_score = 70  # Default - could enhance with actual persona data from Clay

        # Account Value Score (0-100)
        value_score = min((savings["annual_savings_dollars"] / 50000) * 100, 100)

        # Composite score
        composite = (
            intent_score * weights["intent"] +
            tech_fit_score * weights["technical_fit"] +
            urgency_score * weights["urgency"] +
            persona_score * weights["persona_quality"] +
            value_score * weights["account_value"]
        )

        return {
            "intent": round(intent_score, 1),
            "technical_fit": round(tech_fit_score, 1),
            "urgency": round(urgency_score, 1),
            "persona_quality": round(persona_score, 1),
            "account_value": round(value_score, 1),
            "composite": round(composite, 1)
        }

    def _calculate_intent_score(self, research: Dict) -> float:
        """Calculate intent signal score"""

        intent_signals = research.get("intent_signals_found", {})

        if not intent_signals or not isinstance(intent_signals, dict):
            return 20  # Base score

        # Count signals and weight by confidence
        total_score = 0
        signal_count = 0

        for category, signals in intent_signals.items():
            if isinstance(signals, list):
                for signal in signals:
                    signal_count += 1
                    if isinstance(signal, dict):
                        confidence = signal.get("confidence", 50)
                        total_score += confidence
                    else:
                        total_score += 50

        if signal_count == 0:
            return 20

        # Average confidence + bonus for quantity
        avg_confidence = total_score / signal_count
        quantity_bonus = min(signal_count * 5, 25)

        return min(avg_confidence * 0.7 + quantity_bonus, 100)

    def _calculate_technical_fit(self, profile: Dict, savings: Dict) -> float:
        """Calculate technical fit score"""

        score = 40  # Base score

        # Company size
        employees = profile["employee_count"]
        if employees > 500:
            score += 30
        elif employees > 200:
            score += 20
        elif employees > 100:
            score += 10

        # Savings opportunity
        if savings["annual_savings_dollars"] > 100000:
            score += 20
        elif savings["annual_savings_dollars"] > 50000:
            score += 10

        # Payback period
        if savings["payback_period_months"] < 15:
            score += 10

        return min(score, 100)

    def _determine_priority_tier(self, composite_score: float) -> str:
        """Determine priority tier"""
        if composite_score >= 75:
            return "A"
        elif composite_score >= 60:
            return "B"
        else:
            return "C"

    def _map_personas(self, profile: Dict) -> Dict:
        """Map decision-maker personas"""

        ideal_personas = self.agent.ideal_personas

        decision_makers = []
        for i, persona in enumerate(ideal_personas[:3]):
            decision_makers.append({
                "persona_type": persona.persona_type.value,
                "typical_titles": persona.typical_titles[:3],
                "decision_authority": persona.decision_authority,
                "priority_order": i + 1
            })

        return {
            "decision_makers": decision_makers,
            "buying_committee_size": len(decision_makers),
            "primary_persona": decision_makers[0]["persona_type"] if decision_makers else None
        }

    async def _generate_personalization_intel(self, profile: Dict,
                                             research: Dict, scores: Dict) -> Dict:
        """Generate personalization intelligence for outreach"""

        key_points = research.get("key_personalization_points", [])

        # If we didn't get enough from research, generate some
        if len(key_points) < 3:
            prompt = f"""Generate 5-7 specific personalization points for outreach to {profile['company_name']}.

COMPANY:
- Industry: {profile['industry']}
- Size: {profile['employee_count']} employees
- Location: {profile.get('headquarters', 'Unknown')}

RESEARCH INSIGHTS:
{json.dumps(research, indent=2, default=str)[:1500]}

Generate specific, credible personalization points like:
- "Noticed your sustainability page mentions X target..."
- "Your recent expansion to Y location..."
- "With {employee_count} employees, you're likely spending $X on energy..."

Return as JSON array of strings."""

            try:
                message = self.claude_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}]
                )

                content = message.content[0].text
                if '```json' in content:
                    json_str = content.split('```json')[1].split('```')[0].strip()
                    key_points = json.loads(json_str)
            except:
                key_points = [f"Research conducted on {profile['company_name']}"]

        return {
            "personalization_points": key_points[:7],
            "personalization_depth": len(key_points),
            "recommended_approach": "High personalization" if scores["composite"] > 70 else "Standard personalization"
        }

    def _guess_domain(self, company_name: str) -> str:
        """Guess domain from company name"""
        clean = company_name.lower().replace(' ', '').replace(',', '').replace('.', '').replace('inc', '').replace('llc', '')
        return f"{clean}.com"


class BatchProspectProcessor:
    """Batch process multiple Clay-enriched prospects"""

    def __init__(self, industry_agent, claude_api_key: str):
        self.intelligence = ProspectIntelligence(industry_agent, claude_api_key)
        self.results = []

    async def process_batch(self, clay_enriched_prospects: List[Dict],
                           concurrency: int = 3) -> List[Dict]:
        """Process batch of prospects"""

        print(f"\n{'='*70}")
        print(f"🚀 BATCH PROCESSING {len(clay_enriched_prospects)} PROSPECTS")
        print(f"{'='*70}\n")

        semaphore = asyncio.Semaphore(concurrency)

        async def process_with_semaphore(prospect):
            async with semaphore:
                try:
                    return await self.intelligence.analyze_prospect(prospect)
                except Exception as e:
                    print(f"❌ Error processing {prospect.get('company_name')}: {e}")
                    return None

        tasks = [process_with_semaphore(p) for p in clay_enriched_prospects]
        results = await asyncio.gather(*tasks)

        self.results = [r for r in results if r is not None]

        self._print_summary()

        return self.results

    def _print_summary(self):
        """Print batch summary"""

        if not self.results:
            print("No results to summarize")
            return

        tier_a = len([r for r in self.results if r["priority_tier"] == "A"])
        tier_b = len([r for r in self.results if r["priority_tier"] == "B"])
        tier_c = len([r for r in self.results if r["priority_tier"] == "C"])

        avg_score = sum(r["composite_score"] for r in self.results) / len(self.results)
        total_savings = sum(r["savings_projection"]["annual_savings_dollars"] for r in self.results)

        print(f"\n{'='*70}")
        print("📊 BATCH ANALYSIS SUMMARY")
        print(f"{'='*70}")
        print(f"Total Analyzed: {len(self.results)}")
        print(f"Average Score: {avg_score:.1f}/100")
        print(f"Total Annual Savings Potential: ${total_savings:,.0f}")
        print(f"\nPriority Breakdown:")
        print(f"  🔥 A-Tier (75+): {tier_a} prospects")
        print(f"  ⭐ B-Tier (60-74): {tier_b} prospects")
        print(f"  💤 C-Tier (<60): {tier_c} prospects")
        print(f"{'='*70}\n")

    def export_results(self, filepath: str):
        """Export results to JSON"""
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"✅ Results exported to {filepath}")


# Example usage
async def example_usage():
    """Example with Clay-enriched data"""

    from agent_builder_system import MasterAgentBuilder, IndustryType

    # Build agent
    CLAUDE_API_KEY = "your-api-key"
    builder = MasterAgentBuilder(CLAUDE_API_KEY)
    agent = await builder.build_agent(IndustryType.CASINO)

    # Simulate Clay-enriched prospect data
    clay_enriched_prospect = {
        "company_name": "MGM Grand Las Vegas",
        "domain": "mgmgrand.com",
        "employee_count": 5000,
        "industry": "casino",
        "headquarters": "Las Vegas, NV",
        "revenue": 2500000000,
        "linkedin_url": "https://linkedin.com/company/mgm-grand"
    }

    # Analyze
    intelligence = ProspectIntelligence(agent, CLAUDE_API_KEY)
    analysis = await intelligence.analyze_prospect(clay_enriched_prospect)

    print(f"\n📋 Analysis Results:")
    print(f"Composite Score: {analysis['composite_score']}/100")
    print(f"Priority: {analysis['priority_tier']}")
    print(f"Annual Savings: ${analysis['savings_projection']['annual_savings_dollars']:,.0f}")
    print(f"Payback: {analysis['savings_projection']['payback_period_months']} months")


if __name__ == "__main__":
    asyncio.run(example_usage())

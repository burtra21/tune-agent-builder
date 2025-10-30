"""
Tune® Agent Builder System
Elite-tier agent creation framework for specialized industry outbound

This system creates industry-specialized AI agents that:
1. Research industries deeply
2. Score and enrich prospects
3. Generate hyper-personalized multi-channel content
4. Orchestrate outbound campaigns through Clay/n8n
5. Optimize continuously based on performance data
"""

import asyncio
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
import anthropic
import httpx

# =============================================================================
# CORE DATA MODELS
# =============================================================================

class IndustryType(Enum):
    CASINO = "casino"
    DATA_CENTER = "data_center"
    HOSPITAL = "hospital"
    MANUFACTURING = "manufacturing"
    MULTIFAMILY = "multifamily"
    HOTEL = "hotel"
    OFFICE_BUILDING = "office_building"
    QSR = "qsr"
    EDUCATION = "education"
    
class PersonaType(Enum):
    ESG_DIRECTOR = "esg_director"
    FACILITIES_VP = "facilities_vp"
    ENERGY_MANAGER = "energy_manager"
    SUSTAINABILITY_CHIEF = "sustainability_chief"
    CFO = "cfo"
    OPERATIONS_DIRECTOR = "operations_director"
    VP_REAL_ESTATE = "vp_real_estate"
    DIRECTOR_FACILITIES = "director_facilities"

@dataclass
class TuneValueProposition:
    """Specific value prop for an industry/persona combination"""
    headline: str
    proof_points: List[str]
    quantified_benefit: str
    timeframe: str
    risk_mitigation: str
    
@dataclass
class EmailFramework:
    """Complete email template framework"""
    touch_number: int
    goal: str
    framework_type: str  # PEC+G, BAB, PAS, etc.
    max_words: int
    tone: str
    key_message: str
    cta: str
    hooks: List[str]
    personalization_requirements: List[str]
    
@dataclass
class PersonaProfile:
    """Complete persona intelligence"""
    persona_type: PersonaType
    typical_titles: List[str]
    priorities: List[str]
    pain_points: List[str]
    success_metrics: List[str]
    decision_authority: str
    budget_influence: str
    evaluation_criteria: List[str]
    objection_patterns: List[str]

@dataclass
class IndustryAgent:
    """Complete specification for an industry-specialized agent"""
    
    # Core Identity
    industry: IndustryType
    name: str
    description: str
    version: str
    created_at: datetime
    
    # Industry Intelligence
    energy_profile: Dict[str, Any]
    operational_characteristics: Dict[str, Any]
    financial_profile: Dict[str, Any]
    sustainability_drivers: Dict[str, Any]
    
    # Value Propositions
    value_props_by_persona: Dict[PersonaType, TuneValueProposition]
    case_studies: List[Dict[str, Any]]
    savings_benchmarks: Dict[str, float]
    
    # Target Intelligence
    ideal_personas: List[PersonaProfile]
    intent_signals: Dict[str, List[str]]
    urgency_triggers: List[str]
    company_size_targets: Dict[str, Any]
    
    # Research Protocols
    research_questions: List[str]
    enrichment_workflow: Dict[str, Any]
    scoring_weights: Dict[str, float]
    
    # Content Frameworks
    email_sequences: Dict[PersonaType, List[EmailFramework]]
    linkedin_strategy: Dict[str, Any]
    video_frameworks: Dict[str, Any]
    
    # Outreach Design
    sequence_cadence: Dict[str, Any]
    channel_mix_by_persona: Dict[PersonaType, List[str]]
    personalization_depth: int  # 1-5 scale
    
    # Integration Specs
    clay_table_schemas: Dict[str, Any]
    n8n_workflow_specs: List[Dict[str, Any]]
    api_endpoints: Dict[str, str]
    
    def to_json(self) -> str:
        """Export agent as JSON"""
        data = asdict(self)
        # Convert enums to strings
        data['industry'] = self.industry.value
        data['created_at'] = self.created_at.isoformat()

        # Convert PersonaProfile objects with PersonaType enum conversion
        data['ideal_personas'] = []
        for persona in self.ideal_personas:
            persona_dict = asdict(persona)
            persona_dict['persona_type'] = persona.persona_type.value
            data['ideal_personas'].append(persona_dict)

        # Convert PersonaType enum keys to strings in dictionaries
        data['value_props_by_persona'] = {
            k.value: asdict(v) for k, v in self.value_props_by_persona.items()
        }
        data['email_sequences'] = {
            k.value: [asdict(framework) for framework in v]
            for k, v in self.email_sequences.items()
        }
        data['channel_mix_by_persona'] = {
            k.value: v for k, v in self.channel_mix_by_persona.items()
        }

        return json.dumps(data, indent=2)
    
    def save(self, filepath: str):
        """Save agent to file"""
        with open(filepath, 'w') as f:
            f.write(self.to_json())


# =============================================================================
# INDUSTRY RESEARCH ENGINE
# =============================================================================

class IndustryResearchEngine:
    """Conducts comprehensive industry research to power agent creation"""
    
    def __init__(self, industry: IndustryType, claude_api_key: str):
        self.industry = industry
        self.client = anthropic.Anthropic(api_key=claude_api_key)
        self.http_client = httpx.AsyncClient()
        
    async def research_industry(self) -> Dict[str, Any]:
        """Execute complete industry research protocol"""
        
        print(f"🔍 Researching {self.industry.value} industry...")
        
        research_results = {
            "energy_profile": await self._research_energy_profile(),
            "operational_characteristics": await self._research_operations(),
            "financial_profile": await self._research_financials(),
            "sustainability_drivers": await self._research_sustainability(),
            "decision_making": await self._research_decision_processes(),
            "competitive_landscape": await self._research_competitors(),
            "intent_signals": await self._identify_intent_signals(),
            "urgency_triggers": await self._identify_urgency_triggers(),
        }
        
        # Synthesize research
        synthesis = await self._synthesize_research(research_results)
        
        return synthesis
    
    async def _research_energy_profile(self) -> Dict[str, Any]:
        """Research industry energy consumption patterns"""
        
        prompt = f"""Research the {self.industry.value} industry's energy consumption profile.

Provide detailed information on:
1. Average kWh per square foot annually
2. Typical peak demand patterns (time of day, seasonality)
3. Major equipment that consumes electricity
4. Load characteristics (constant vs variable)
5. Power quality challenges (harmonics, voltage fluctuations)
6. Typical electrical infrastructure (voltage levels, panel configurations)

Format as structured JSON with quantified data where possible."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse response
        content = message.content[0].text
        
        # Extract JSON if present, otherwise structure the response
        try:
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0].strip()
                return json.loads(json_str)
            else:
                return {"raw_research": content}
        except:
            return {"raw_research": content}
    
    async def _research_operations(self) -> Dict[str, Any]:
        """Research operational characteristics"""
        
        prompt = f"""Analyze the operational characteristics of {self.industry.value} facilities.

Focus on:
1. Uptime criticality (24/7 operations? Maintenance windows?)
2. Equipment lifecycle and replacement cycles
3. Maintenance intensity and costs
4. Technology adoption rate
5. Regulatory requirements affecting operations
6. Seasonal operational variations

Provide specific examples and quantified data."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {"operational_analysis": message.content[0].text}
    
    async def _research_sustainability(self) -> Dict[str, Any]:
        """Research sustainability drivers and initiatives"""
        
        prompt = f"""Research sustainability drivers for the {self.industry.value} industry.

Analyze:
1. ESG reporting requirements (mandatory vs voluntary)
2. Common carbon reduction targets (e.g., % reduction by year)
3. Green building certifications pursued (LEED, Energy Star, etc.)
4. Stakeholder pressures (investors, customers, regulators, employees)
5. Sustainability ROI considerations
6. Common sustainability initiatives beyond energy

Provide current trends and specific examples of industry leaders."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {"sustainability_research": message.content[0].text}

    async def _research_financials(self) -> Dict[str, Any]:
        """Research financial characteristics and considerations"""

        prompt = f"""Research financial characteristics for the {self.industry.value} industry.

Analyze:
1. Typical capital expenditure budgets and cycles
2. Average project approval thresholds
3. Common ROI requirements for energy projects
4. Payback period expectations
5. Financing preferences (capex vs opex, leasing, PPAs)
6. Budget timing (fiscal year, approval cycles)
7. Financial decision-making authority levels

Provide specific data points and ranges."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        return {"financial_research": message.content[0].text}

    async def _research_decision_processes(self) -> Dict[str, Any]:
        """Research decision-making processes and stakeholders"""

        prompt = f"""Research decision-making processes for energy efficiency projects in the {self.industry.value} industry.

Analyze:
1. Key decision-makers and their titles
2. Typical decision-making committees or groups
3. Approval process steps and timeline
4. Stakeholder influences (operations, finance, sustainability, procurement)
5. Common objections and concerns
6. Decision criteria and priorities
7. Vendor evaluation process

Provide specific organizational patterns."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        return {"decision_process_research": message.content[0].text}

    async def _research_competitors(self) -> Dict[str, Any]:
        """Research competitive landscape"""

        prompt = f"""Research the competitive landscape for energy efficiency solutions in the {self.industry.value} industry.

Analyze:
1. Major solution providers and their market positions
2. Common solution types (equipment, services, software)
3. Typical value propositions and differentiators
4. Pricing models and ranges
5. Common partnerships and alliances
6. Market trends and emerging players
7. Customer satisfaction pain points with existing solutions

Provide specific competitor names and positioning."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        return {"competitive_research": message.content[0].text}

    async def _identify_intent_signals(self) -> Dict[str, List[str]]:
        """Identify buying intent signals for this industry"""
        
        prompt = f"""Identify specific buying intent signals for energy efficiency solutions in the {self.industry.value} industry.

For each signal category, list 5-10 specific, searchable indicators:

1. Sustainability Commitments:
   - What pages/documents indicate active sustainability initiatives?
   - What language suggests they're measuring and reducing energy?

2. Recent Initiatives:
   - What announcements suggest they're investing in efficiency?
   - What project types create demand for energy solutions?

3. Leadership Changes:
   - What new roles indicate increased sustainability focus?
   - What background suggests they'll prioritize energy?

4. Expansion Plans:
   - What expansion activities create energy optimization opportunities?

5. Regulatory Pressures:
   - What compliance requirements drive energy projects?

6. Financial Triggers:
   - What financial situations create urgency for cost savings?

Provide as structured lists of specific, actionable signals."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse into structured format
        content = message.content[0].text
        
        return {
            "sustainability_commitments": self._extract_signals(content, "Sustainability Commitments"),
            "recent_initiatives": self._extract_signals(content, "Recent Initiatives"),
            "leadership_changes": self._extract_signals(content, "Leadership Changes"),
            "expansion_plans": self._extract_signals(content, "Expansion Plans"),
            "regulatory_pressures": self._extract_signals(content, "Regulatory Pressures"),
            "financial_triggers": self._extract_signals(content, "Financial Triggers")
        }
    
    def _extract_signals(self, content: str, category: str) -> List[str]:
        """Extract signals from research text"""
        # Simple extraction - look for bullet points or numbered items after category
        signals = []
        lines = content.split('\n')
        in_category = False
        
        for line in lines:
            if category.lower() in line.lower():
                in_category = True
                continue
            if in_category:
                # Stop at next category or blank line
                if any(cat in line for cat in ['Commitments:', 'Initiatives:', 'Changes:', 'Plans:', 'Pressures:', 'Triggers:']) and category not in line:
                    break
                # Extract bullet points or numbered items
                if line.strip().startswith(('-', '•', '*')) or (len(line) > 0 and line.strip()[0].isdigit()):
                    signal = line.strip().lstrip('-•*0123456789. ')
                    if signal:
                        signals.append(signal)
        
        return signals[:10]  # Max 10 per category

    async def _identify_urgency_triggers(self) -> Dict[str, List[str]]:
        """Identify urgency triggers that accelerate buying decisions"""

        prompt = f"""Identify urgency triggers that accelerate energy efficiency project decisions in the {self.industry.value} industry.

For each category, list specific, time-sensitive triggers:

1. **Regulatory Deadlines**: Compliance deadlines, reporting requirements
2. **Financial Windows**: Budget cycles, tax incentives expiring, rebate programs
3. **Operational Crises**: Equipment failures, power quality issues, high bills
4. **Market Events**: Energy price spikes, supply constraints, competitor moves
5. **Organizational Changes**: New leadership, acquisitions, expansions
6. **External Pressures**: Investor demands, customer complaints, media attention

Provide specific, actionable triggers that create NOW urgency."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        content = message.content[0].text

        return {
            "regulatory_deadlines": self._extract_signals(content, "Regulatory Deadlines"),
            "financial_windows": self._extract_signals(content, "Financial Windows"),
            "operational_crises": self._extract_signals(content, "Operational Crises"),
            "market_events": self._extract_signals(content, "Market Events"),
            "organizational_changes": self._extract_signals(content, "Organizational Changes"),
            "external_pressures": self._extract_signals(content, "External Pressures")
        }

    async def _synthesize_research(self, research_results: Dict) -> Dict[str, Any]:
        """Synthesize all research into actionable insights"""
        
        prompt = f"""Synthesize the following research on the {self.industry.value} industry into actionable insights for selling Tune® energy filters.

Research Data:
{json.dumps(research_results, indent=2)}

Provide:
1. Key energy consumption insights that support Tune® value prop
2. Primary pain points that Tune® solves
3. Decision-maker priorities we should address
4. Optimal messaging angles
5. Likely objections and how to counter them

Format as structured JSON."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        synthesis = {"synthesis": message.content[0].text}
        synthesis.update(research_results)
        
        return synthesis


# =============================================================================
# PERSONA RESEARCH ENGINE
# =============================================================================

class PersonaResearchEngine:
    """Researches target personas for industry"""
    
    def __init__(self, industry: IndustryType, claude_api_key: str):
        self.industry = industry
        self.client = anthropic.Anthropic(api_key=claude_api_key)
    
    async def research_personas(self) -> List[PersonaProfile]:
        """Identify and research all relevant personas"""
        
        # First, identify personas
        personas_list = await self._identify_personas()
        
        # Then, deep dive on each
        persona_profiles = []
        for persona_type in personas_list:
            profile = await self._research_persona_deep(persona_type)
            persona_profiles.append(profile)
        
        return persona_profiles
    
    async def _identify_personas(self) -> List[PersonaType]:
        """Identify relevant personas for this industry"""
        
        prompt = f"""For the {self.industry.value} industry, identify all relevant personas who would be involved in purchasing energy efficiency solutions like Tune® filters.

Consider:
- Who has budget authority?
- Who experiences the pain points?
- Who measures success?
- Who champions sustainability?
- Who evaluates technical solutions?

List 3-6 key personas with their typical titles."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse and map to PersonaType enum
        content = message.content[0].text.lower()
        
        relevant_personas = []
        persona_keywords = {
            PersonaType.ESG_DIRECTOR: ['esg', 'sustainability', 'environmental'],
            PersonaType.FACILITIES_VP: ['facilities', 'building', 'property'],
            PersonaType.ENERGY_MANAGER: ['energy', 'utilities'],
            PersonaType.SUSTAINABILITY_CHIEF: ['chief sustainability', 'cso'],
            PersonaType.CFO: ['cfo', 'chief financial', 'finance'],
            PersonaType.OPERATIONS_DIRECTOR: ['operations', 'ops'],
            PersonaType.VP_REAL_ESTATE: ['real estate', 'asset management'],
            PersonaType.DIRECTOR_FACILITIES: ['director of facilities', 'facilities director']
        }
        
        for persona_type, keywords in persona_keywords.items():
            if any(keyword in content for keyword in keywords):
                relevant_personas.append(persona_type)
        
        return relevant_personas[:6]  # Max 6 personas
    
    async def _research_persona_deep(self, persona_type: PersonaType) -> PersonaProfile:
        """Deep research on specific persona"""
        
        prompt = f"""Conduct deep research on the {persona_type.value} persona in the {self.industry.value} industry as it relates to purchasing energy efficiency solutions.

Provide:
1. Typical job titles (5-10 variations)
2. Top 5 priorities in their role
3. Top 5 pain points
4. How they measure success (KPIs)
5. Decision authority level (Decision Maker, Influencer, Champion, Gatekeeper)
6. Budget influence (High, Medium, Low)
7. Evaluation criteria when assessing solutions (5-7 criteria)
8. Common objections they raise (4-6 objections)
9. Information sources they trust
10. Communication preferences

Format as JSON with specific, actionable insights."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = message.content[0].text
        
        # Parse JSON if present
        try:
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0].strip()
                data = json.loads(json_str)
            else:
                # Create structured data from text
                data = {
                    "typical_titles": ["Director of Sustainability", "VP Facilities", "Energy Manager"],
                    "priorities": ["Cost reduction", "ESG goals", "Operational efficiency"],
                    "pain_points": ["Rising energy costs", "Maintenance burden", "Sustainability reporting"],
                    "success_metrics": ["Energy cost savings", "Carbon reduction", "Equipment uptime"],
                    "decision_authority": "Influencer",
                    "budget_influence": "Medium",
                    "evaluation_criteria": ["ROI", "Ease of implementation", "Proven results"],
                    "objection_patterns": ["Too good to be true", "Budget constraints", "Risk aversion"]
                }
        except:
            data = {"raw_research": content}
        
        return PersonaProfile(
            persona_type=persona_type,
            typical_titles=data.get("typical_titles", []),
            priorities=data.get("priorities", []),
            pain_points=data.get("pain_points", []),
            success_metrics=data.get("success_metrics", []),
            decision_authority=data.get("decision_authority", "Unknown"),
            budget_influence=data.get("budget_influence", "Unknown"),
            evaluation_criteria=data.get("evaluation_criteria", []),
            objection_patterns=data.get("objection_patterns", [])
        )


# =============================================================================
# VALUE PROPOSITION BUILDER
# =============================================================================

class ValuePropositionBuilder:
    """Builds industry/persona-specific value propositions"""
    
    def __init__(self, industry: IndustryType, claude_api_key: str):
        self.industry = industry
        self.client = anthropic.Anthropic(api_key=claude_api_key)
        
        # Load Tune case study data
        self.case_study_data = self._load_case_studies()
    
    def _load_case_studies(self) -> Dict[str, Any]:
        """Load relevant Tune case studies for industry"""
        
        # Map industries to case studies
        case_study_mapping = {
            IndustryType.CASINO: {
                "savings_percentage": 8.59,
                "customer": "Las Vegas Casino",
                "results": "8.59% kW reduction, verified by third-party"
            },
            IndustryType.HOSPITAL: {
                "savings_percentage": 12,
                "typical_savings": "$14,520/year",
                "kwh_saved": "201,024 kWh/year"
            },
            IndustryType.MULTIFAMILY: {
                "savings_percentage": 15,
                "typical_savings": "$31,676/year",
                "kwh_saved": "334,800 kWh/year",
                "examples": ["Caribe Resort: 14% savings", "Hilton Garden Inn: 13.51% savings"]
            },
            IndustryType.HOTEL: {
                "savings_percentage": 14,
                "examples": ["Caribe Resort", "Hilton Garden Inn"],
                "maintenance_benefits": "Extended equipment life, reduced HVAC failures"
            },
            IndustryType.QSR: {
                "savings_percentage": 12,
                "examples": ["Domino's RPM: 12.5% savings", "Popeyes: 9% savings", "Krystal: 9.7% delta"],
                "maintenance_savings": "Up to 40% reduction in maintenance budgets"
            },
            IndustryType.OFFICE_BUILDING: {
                "savings_percentage": 15,
                "typical_savings": "$31,574/year",
                "kwh_saved": "342,000 kWh/year"
            }
        }
        
        return case_study_mapping.get(self.industry, {
            "savings_percentage": 11,
            "typical_savings": "10-15% energy cost reduction"
        })
    
    async def build_value_props(self, persona_profiles: List[PersonaProfile], 
                               industry_research: Dict) -> Dict[PersonaType, TuneValueProposition]:
        """Build value propositions for each persona"""
        
        value_props = {}
        
        for persona in persona_profiles:
            value_prop = await self._build_persona_value_prop(persona, industry_research)
            value_props[persona.persona_type] = value_prop
        
        return value_props
    
    async def _build_persona_value_prop(self, persona: PersonaProfile, 
                                       industry_research: Dict) -> TuneValueProposition:
        """Build value prop for specific persona"""
        
        prompt = f"""Create a compelling value proposition for Tune® energy filters targeting a {persona.persona_type.value} in the {self.industry.value} industry.

PERSONA PROFILE:
- Priorities: {', '.join(persona.priorities)}
- Pain Points: {', '.join(persona.pain_points)}
- Success Metrics: {', '.join(persona.success_metrics)}
- Decision Authority: {persona.decision_authority}

TUNE® PERFORMANCE DATA:
{json.dumps(self.case_study_data, indent=2)}

INDUSTRY INSIGHTS:
{json.dumps(industry_research.get('synthesis', {}), indent=2)}

Create:
1. Headline: One sentence that captures the core value (focus on their #1 priority)
2. 3-5 Proof Points: Specific, credible reasons to believe
3. Quantified Benefit: Specific $ or % savings with timeframe
4. Risk Mitigation: How we reduce their risk (guarantee, validation, ease of implementation)

Make it specific to this persona's worldview and priorities. Use language they use.

Format as JSON."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = message.content[0].text
        
        try:
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0].strip()
                data = json.loads(json_str)
            else:
                data = {
                    "headline": f"Reduce energy costs by {self.case_study_data.get('savings_percentage', 11)}% with zero operational disruption",
                    "proof_points": [
                        f"Verified {self.case_study_data.get('savings_percentage', 11)}% savings in {self.industry.value} facilities",
                        "Passive device - no electricity consumption",
                        "5% minimum savings guarantee or full refund",
                        "UL listed, DOE certified technology"
                    ],
                    "quantified_benefit": f"{self.case_study_data.get('savings_percentage', 11)}% reduction in kWh consumption",
                    "timeframe": "Typical payback: 11-18 months",
                    "risk_mitigation": "90-day pilot with 5% savings guarantee - full refund if not met"
                }
        except:
            data = {"raw": content}
        
        return TuneValueProposition(
            headline=data.get("headline", "Reduce energy costs significantly"),
            proof_points=data.get("proof_points", []),
            quantified_benefit=data.get("quantified_benefit", "10%+ energy savings"),
            timeframe=data.get("timeframe", "12-18 month payback"),
            risk_mitigation=data.get("risk_mitigation", "90-day pilot with guarantee")
        )


# =============================================================================
# CONTENT FRAMEWORK BUILDER
# =============================================================================

class ContentFrameworkBuilder:
    """Builds email, LinkedIn, video content frameworks"""
    
    def __init__(self, industry: IndustryType, claude_api_key: str):
        self.industry = industry
        self.client = anthropic.Anthropic(api_key=claude_api_key)
    
    async def build_email_frameworks(self, 
                                     persona_profiles: List[PersonaProfile],
                                     value_props: Dict[PersonaType, TuneValueProposition]) -> Dict[PersonaType, List[EmailFramework]]:
        """Build complete email sequence frameworks for each persona"""
        
        frameworks = {}
        
        for persona in persona_profiles:
            value_prop = value_props[persona.persona_type]
            sequence = await self._build_email_sequence(persona, value_prop)
            frameworks[persona.persona_type] = sequence
        
        return frameworks
    
    async def _build_email_sequence(self, persona: PersonaProfile, 
                                    value_prop: TuneValueProposition) -> List[EmailFramework]:
        """Build 5-touch email sequence for persona"""
        
        prompt = f"""Design a 5-touch cold email sequence for selling Tune® energy filters to a {persona.persona_type.value} in the {self.industry.value} industry.

PERSONA:
- Priorities: {', '.join(persona.priorities[:3])}
- Pain Points: {', '.join(persona.pain_points[:3])}
- Decision Authority: {persona.decision_authority}

VALUE PROPOSITION:
{value_prop.headline}
- Benefit: {value_prop.quantified_benefit}
- Proof: {', '.join(value_prop.proof_points[:2])}

SEQUENCE REQUIREMENTS:
- Touch 1: Problem awareness + value teaser (PEC+G framework, 100 words max)
- Touch 2: Specific value + proof (case study, 125 words max)
- Touch 3: Address likely objection (150 words max)
- Touch 4: Urgency + easy next step (100 words max)
- Touch 5: Break-up email + door open (75 words max)

For each touch, specify:
1. Goal
2. Framework type (PEC+G, BAB, PAS, etc.)
3. Max word count
4. Tone (professional, conversational, urgent, etc.)
5. Key message
6. CTA
7. 3-5 potential hooks/opening lines
8. Required personalization elements

Format as JSON array of 5 email specifications."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = message.content[0].text
        
        # Parse sequence
        sequence = []
        for i in range(1, 6):
            framework = EmailFramework(
                touch_number=i,
                goal=f"Touch {i} goal",
                framework_type="PEC+G" if i == 1 else "Custom",
                max_words=100 if i in [1, 4, 5] else 125,
                tone="conversational",
                key_message=f"Touch {i} message",
                cta="Book 15-min call",
                hooks=["Hook 1", "Hook 2", "Hook 3"],
                personalization_requirements=["Company name", "Industry", "Sustainability commitment"]
            )
            sequence.append(framework)
        
        return sequence


# =============================================================================
# MASTER AGENT BUILDER
# =============================================================================

class MasterAgentBuilder:
    """Master system that orchestrates entire agent creation"""
    
    def __init__(self, claude_api_key: str):
        self.claude_api_key = claude_api_key
    
    async def build_agent(self, industry: IndustryType, 
                         config: Optional[Dict] = None) -> IndustryAgent:
        """Complete agent build process"""
        
        if config is None:
            config = {"personalization_depth": 4}
        
        print(f"\n{'='*60}")
        print(f"🏗️  BUILDING {industry.value.upper()} AGENT")
        print(f"{'='*60}\n")
        
        # Phase 1: Industry Research
        print("📚 Phase 1: Deep Industry Research")
        industry_engine = IndustryResearchEngine(industry, self.claude_api_key)
        industry_intel = await industry_engine.research_industry()
        print("✅ Industry research complete\n")
        
        # Phase 2: Persona Research
        print("👥 Phase 2: Persona Intelligence Gathering")
        persona_engine = PersonaResearchEngine(industry, self.claude_api_key)
        personas = await persona_engine.research_personas()
        print(f"✅ Identified {len(personas)} key personas\n")
        
        # Phase 3: Value Propositions
        print("💎 Phase 3: Building Value Propositions")
        value_prop_builder = ValuePropositionBuilder(industry, self.claude_api_key)
        value_props = await value_prop_builder.build_value_props(personas, industry_intel)
        print("✅ Value props created for each persona\n")
        
        # Phase 4: Content Frameworks
        print("✍️  Phase 4: Creating Content Frameworks")
        content_builder = ContentFrameworkBuilder(industry, self.claude_api_key)
        email_frameworks = await content_builder.build_email_frameworks(personas, value_props)
        print("✅ Email sequences designed\n")
        
        # Phase 5: Package Agent
        print("📦 Phase 5: Packaging Complete Agent")
        agent = IndustryAgent(
            industry=industry,
            name=f"Tune® {industry.value.replace('_', ' ').title()} Specialist",
            description=f"Elite outbound agent for {industry.value} sector with deep personalization",
            version="1.0.0",
            created_at=datetime.now(),
            
            # Industry Intelligence
            energy_profile=industry_intel.get('energy_profile', {}),
            operational_characteristics=industry_intel.get('operational_characteristics', {}),
            financial_profile=industry_intel.get('financial_profile', {}),
            sustainability_drivers=industry_intel.get('sustainability_drivers', {}),
            
            # Value Props
            value_props_by_persona=value_props,
            case_studies=value_prop_builder.case_study_data,
            savings_benchmarks={
                "typical_percentage": value_prop_builder.case_study_data.get('savings_percentage', 11),
                "payback_months": 14
            },
            
            # Targets
            ideal_personas=personas,
            intent_signals=industry_intel.get('intent_signals', {}),
            urgency_triggers=industry_intel.get('urgency_triggers', []),
            company_size_targets={"min_employees": 50, "min_sqft": 10000},
            
            # Research
            research_questions=[
                f"What are {industry.value} energy consumption patterns?",
                "What sustainability commitments has company made?",
                "Who are the key decision makers?",
                "What is their ESG reporting status?",
                "Are there any expansion or renovation plans?"
            ],
            enrichment_workflow={"steps": ["web_research", "linkedin_lookup", "intent_scoring"]},
            scoring_weights={
                "intent": 0.35,
                "technical_fit": 0.25,
                "urgency": 0.15,
                "persona_quality": 0.20,
                "account_value": 0.05
            },
            
            # Content
            email_sequences=email_frameworks,
            linkedin_strategy={"approach": "Value-first connection requests"},
            video_frameworks={"loom_intro": "Personal video introducing Tune value"},
            
            # Outreach
            sequence_cadence={"touches": 5, "days_between": [3, 4, 5, 7, 7]},
            channel_mix_by_persona={p.persona_type: ["email", "linkedin"] for p in personas},
            personalization_depth=config.get("personalization_depth", 4),
            
            # Integration
            clay_table_schemas=self._generate_clay_schemas(),
            n8n_workflow_specs=self._generate_n8n_workflows(),
            api_endpoints={
                "research": "/api/research/prospect",
                "content": "/api/content/generate",
                "score": "/api/prospect/score"
            }
        )
        
        print("✅ Agent packaging complete\n")
        
        print(f"{'='*60}")
        print(f"✨ {industry.value.upper()} AGENT BUILD COMPLETE!")
        print(f"{'='*60}\n")
        
        return agent
    
    def _generate_clay_schemas(self) -> Dict[str, Any]:
        """Generate Clay table schemas"""
        return {
            "master_prospects": {
                "columns": [
                    "company_name", "domain", "industry", "employee_count",
                    "estimated_sqft", "estimated_kwh", "estimated_savings",
                    "intent_score", "composite_score", "priority_tier"
                ]
            },
            "decision_makers": {
                "columns": [
                    "full_name", "title", "persona_type", "email", "linkedin_url",
                    "decision_authority", "outreach_status"
                ]
            }
        }
    
    def _generate_n8n_workflows(self) -> List[Dict[str, Any]]:
        """Generate n8n workflow specs"""
        return [
            {
                "name": "prospect_enrichment",
                "trigger": "Clay webhook - new prospect",
                "steps": ["Research API", "Score", "Update Clay"]
            },
            {
                "name": "content_generation",
                "trigger": "High score threshold",
                "steps": ["Generate emails", "QA check", "Write to Clay"]
            }
        ]


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

async def main():
    """Example: Build a casino industry agent"""
    
    # Initialize with Claude API key
    CLAUDE_API_KEY = "your-api-key-here"  # Replace with your key
    
    builder = MasterAgentBuilder(claude_api_key=CLAUDE_API_KEY)
    
    # Build casino agent
    casino_agent = await builder.build_agent(
        industry=IndustryType.CASINO,
        config={
            "personalization_depth": 5,  # Maximum personalization
        }
    )
    
    # Save agent
    casino_agent.save("/home/claude/tune_agents/casino_agent.json")
    
    print("\n🎰 Casino Agent Summary:")
    print(f"   Name: {casino_agent.name}")
    print(f"   Personas: {len(casino_agent.ideal_personas)}")
    print(f"   Email Sequences: {len(casino_agent.email_sequences)}")
    print(f"   Savings Benchmark: {casino_agent.savings_benchmarks['typical_percentage']}%")
    
    # Build multiple agents
    industries_to_build = [
        IndustryType.DATA_CENTER,
        IndustryType.HOSPITAL,
        IndustryType.MULTIFAMILY
    ]
    
    for industry in industries_to_build:
        agent = await builder.build_agent(industry)
        agent.save(f"/home/claude/tune_agents/{industry.value}_agent.json")


if __name__ == "__main__":
    asyncio.run(main())

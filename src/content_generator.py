"""
Content Generation Engine
Hyper-personalized multi-channel content creation with Claude
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import anthropic


class ContentGenerator:
    """Generates highly personalized emails, LinkedIn messages, and video scripts"""
    
    def __init__(self, industry_agent, claude_api_key: str):
        self.agent = industry_agent
        self.client = anthropic.Anthropic(api_key=claude_api_key)
    
    async def generate_full_sequence(self, prospect_analysis: Dict, 
                                     persona_type: str) -> List[Dict]:
        """Generate complete email sequence for prospect"""
        
        # Get email frameworks for this persona
        from agent_builder_system import PersonaType
        persona_enum = PersonaType[persona_type.upper()]
        frameworks = self.agent.email_sequences.get(persona_enum, [])
        
        if not frameworks:
            print(f"⚠️  No frameworks found for {persona_type}")
            return []
        
        # Get value prop
        value_prop = self.agent.value_props_by_persona.get(persona_enum)
        
        # Generate each email in sequence
        sequence = []
        for i, framework in enumerate(frameworks, 1):
            email = await self._generate_email(
                touch_number=i,
                framework=framework,
                prospect_analysis=prospect_analysis,
                value_prop=value_prop,
                previous_emails=sequence
            )
            sequence.append(email)
            print(f"✅ Generated Email {i}/{len(frameworks)}")
        
        return sequence
    
    async def _generate_email(self, touch_number: int, framework, 
                              prospect_analysis: Dict, value_prop, 
                              previous_emails: List[Dict]) -> Dict:
        """Generate single email"""
        
        # Build comprehensive prompt
        prompt = self._build_email_prompt(
            touch_number, framework, prospect_analysis, 
            value_prop, previous_emails
        )
        
        # Generate with Claude
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.8,  # Creative but controlled
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = message.content[0].text
        
        # Parse email
        email = self._parse_email_response(content)
        
        # Add metadata
        email["touch_number"] = touch_number
        email["framework_used"] = framework.framework_type
        email["generated_at"] = datetime.now().isoformat()
        email["prospect_company"] = prospect_analysis["company_profile"]["company_name"]
        
        # Quality score
        email["quality_score"] = await self._score_email_quality(email, prospect_analysis)
        
        return email
    
    def _build_email_prompt(self, touch_number: int, framework, 
                           prospect_analysis: Dict, value_prop, 
                           previous_emails: List) -> str:
        """Build comprehensive email generation prompt"""
        
        company = prospect_analysis["company_profile"]
        savings = prospect_analysis["savings_projection"]
        intent = prospect_analysis["intent_signals"]
        personalization = prospect_analysis["personalization_intel"]
        
        # Get relevant case study
        case_study = self._select_case_study(company["industry"])
        
        prompt = f"""Generate a highly effective cold outreach email for Tune® energy filters.

CRITICAL REQUIREMENTS:
- This must feel like a 1-to-1 email from a human, NOT a mass campaign
- Use conversational, authentic language
- Reference specific details about their company/industry
- NO generic energy pitches
- Subject line must create curiosity without being salesy
- Keep to {framework.max_words} words maximum
- Use {framework.framework_type} framework

PROSPECT CONTEXT:
Company: {company["company_name"]}
Industry: {company["industry"]}
Size: {company["employee_count"]} employees, ~{company["estimated_sqft"]:,} sq ft
Current Energy Spend: ${company["estimated_energy_spend"]:,.0f}/year

SAVINGS OPPORTUNITY:
- Projected Annual Savings: ${savings["annual_savings_dollars"]:,.0f} ({savings["savings_percentage"]}%)
- Payback Period: {savings["payback_period_months"]} months
- 5-Year Value: ${savings["five_year_savings"]:,.0f}
- Carbon Reduction: {savings["carbon_reduction_tons"]} metric tons CO2/year

INTENT SIGNALS FOUND:
{json.dumps(intent["categories"], indent=2)}

PERSONALIZATION INTELLIGENCE:
{personalization["personalization_points"]}

VALUE PROPOSITION:
{value_prop.headline}
Proof Points:
{chr(10).join(f"- {p}" for p in value_prop.proof_points)}

RELEVANT CASE STUDY:
{case_study}

EMAIL SPECIFICATIONS:
- Touch #{touch_number} - Goal: {framework.goal}
- Tone: {framework.tone}
- Framework: {framework.framework_type}
- Max Length: {framework.max_words} words
- CTA: {framework.cta}

PREVIOUS EMAILS IN SEQUENCE:
{self._format_previous_emails(previous_emails)}

{self._get_framework_instructions(framework.framework_type)}

Generate the email as JSON:
{{
    "subject": "specific, curiosity-driven subject line",
    "body": "full email body",
    "personalization_used": ["specific element 1", "specific element 2"],
    "key_points": ["main point 1", "main point 2"],
    "expected_response": "what response/action you expect"
}}

CRITICAL: 
- NO quotes around any prices/numbers - use them naturally in sentences
- NO corporate jargon
- Make it feel like I actually researched them specifically
- Use their company name naturally (not "your company")
"""
        
        return prompt
    
    def _get_framework_instructions(self, framework_type: str) -> str:
        """Get specific framework instructions"""
        
        frameworks = {
            "PEC+G": """
PEC+G Framework:
- PROOF: Lead with specific, credible proof (case study result)
- EXPLAIN: Briefly explain how it works
- CONNECT: Connect to their specific situation
- GUARANTEE: Mention risk reversal (90-day pilot, 5% guarantee)
""",
            "BAB": """
BAB Framework:
- BEFORE: Paint the current pain state
- AFTER: Show the improved state
- BRIDGE: Position Tune as the bridge
""",
            "PAS": """
PAS Framework:
- PROBLEM: Identify specific problem they face
- AGITATE: Make problem feel urgent/costly
- SOLVE: Present Tune as solution
"""
        }
        
        return frameworks.get(framework_type, "")
    
    def _select_case_study(self, industry: str) -> str:
        """Select most relevant case study"""
        
        case_studies = {
            "casino": "Las Vegas casino: 8.59% kW reduction verified by third-party metering",
            "hospital": "Medical facilities average 12% savings ($14,520/year typical)",
            "multifamily": "Caribe Resort: 14% kWh savings, Hilton Garden Inn: 13.51% savings",
            "hotel": "Caribe Resort: 14% savings with 26% peak month savings",
            "qsr": "RPM Pizza (170 Domino's): 12.5% savings, 1.7 year payback",
            "office_building": "Office buildings average 15% reduction ($31,574/year)",
            "data_center": "High harmonic environments see 10-15% typical savings"
        }
        
        return case_studies.get(industry, "Typical installations save 10-15% on energy costs")
    
    def _format_previous_emails(self, previous_emails: List[Dict]) -> str:
        """Format previous emails for context"""
        
        if not previous_emails:
            return "No previous emails - this is the first touch"
        
        formatted = []
        for email in previous_emails:
            formatted.append(f"Email {email['touch_number']}: {email['subject']}")
        
        return "\n".join(formatted)
    
    def _parse_email_response(self, content: str) -> Dict:
        """Parse Claude's email response"""
        
        try:
            # Try to extract JSON
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0].strip()
                return json.loads(json_str)
            elif '{' in content:
                # Find JSON object
                start = content.find('{')
                end = content.rfind('}') + 1
                return json.loads(content[start:end])
        except:
            pass
        
        # Fallback parsing
        return {
            "subject": "Follow-up on energy savings opportunity",
            "body": content,
            "personalization_used": ["company_name"],
            "key_points": ["energy savings", "quick payback"],
            "expected_response": "meeting request"
        }
    
    async def _score_email_quality(self, email: Dict, prospect_analysis: Dict) -> float:
        """Score email quality (0-10)"""
        
        score = 5.0  # Start at middle
        
        # Check personalization depth
        personalization_count = len(email.get("personalization_used", []))
        score += min(personalization_count * 0.5, 2.0)
        
        # Check length (not too short, not too long)
        body_words = len(email["body"].split())
        if 80 <= body_words <= 150:
            score += 1.0
        elif 60 <= body_words <= 180:
            score += 0.5
        
        # Check for generic phrases (penalize)
        generic_phrases = [
            "i hope this email finds you well",
            "i wanted to reach out",
            "just checking in",
            "circling back",
            "touching base"
        ]
        body_lower = email["body"].lower()
        if any(phrase in body_lower for phrase in generic_phrases):
            score -= 1.0
        
        # Check for specific value mention
        if "$" in email["body"] or "%" in email["body"]:
            score += 0.5
        
        # Check for company name
        company_name = prospect_analysis["company_profile"]["company_name"]
        if company_name.lower() in email["body"].lower():
            score += 0.5
        
        return round(min(score, 10.0), 1)
    
    async def generate_linkedin_message(self, prospect_analysis: Dict, 
                                       persona_type: str) -> Dict:
        """Generate LinkedIn connection request + follow-up"""
        
        company = prospect_analysis["company_profile"]
        savings = prospect_analysis["savings_projection"]
        
        prompt = f"""Generate a LinkedIn connection request message for selling Tune® energy filters.

Prospect: {persona_type} at {company["company_name"]}
Industry: {company["industry"]}
Savings Potential: ${savings["annual_savings_dollars"]:,.0f}/year

REQUIREMENTS:
- Maximum 300 characters (LinkedIn limit)
- Mention specific value/result relevant to their industry
- Natural, not salesy
- Give reason to connect

Generate as JSON:
{{
    "connection_message": "...",
    "follow_up_message": "message to send after connection accepted"
}}
"""
        
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return self._parse_email_response(message.content[0].text)
    
    async def generate_video_script(self, prospect_analysis: Dict, 
                                    persona_type: str, duration_seconds: int = 60) -> Dict:
        """Generate Loom video script"""
        
        company = prospect_analysis["company_profile"]
        savings = prospect_analysis["savings_projection"]
        
        prompt = f"""Create a {duration_seconds}-second Loom video script for selling Tune® energy filters.

Target: {persona_type} at {company["company_name"]}
Savings: ${savings["annual_savings_dollars"]:,.0f}/year ({savings["savings_percentage"]}%)

REQUIREMENTS:
- Conversational, authentic tone
- Show their company website/LinkedIn profile at start
- Reference specific detail about their company
- Visual: Show Tune case study or savings calculator
- Strong CTA at end
- {duration_seconds} seconds maximum

Structure:
- 0-10s: Hook + personalization
- 10-40s: Value explanation
- 40-60s: CTA

Format as JSON with timestamps."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {"script": message.content[0].text, "duration": duration_seconds}


class BatchContentGenerator:
    """Generate content for multiple prospects efficiently"""
    
    def __init__(self, industry_agent, claude_api_key: str):
        self.generator = ContentGenerator(industry_agent, claude_api_key)
        self.results = []
    
    async def generate_sequences_batch(self, prospects_analyzed: List[Dict],
                                      concurrency: int = 3) -> List[Dict]:
        """Generate email sequences for batch of prospects"""
        
        print(f"\n✍️  Generating content for {len(prospects_analyzed)} prospects...")
        
        semaphore = asyncio.Semaphore(concurrency)
        
        async def generate_with_semaphore(prospect):
            async with semaphore:
                # Determine persona to target
                persona_type = self._select_primary_persona(prospect)
                
                # Generate sequence
                sequence = await self.generator.generate_full_sequence(
                    prospect, persona_type
                )
                
                return {
                    "company": prospect["company_profile"]["company_name"],
                    "persona_type": persona_type,
                    "sequence": sequence,
                    "priority_tier": prospect["priority_tier"]
                }
        
        tasks = [generate_with_semaphore(p) for p in prospects_analyzed]
        results = await asyncio.gather(*tasks)
        
        self.results = results
        
        # Print summary
        self._print_summary()
        
        return results
    
    def _select_primary_persona(self, prospect_analysis: Dict) -> str:
        """Select primary persona to target first"""
        
        # Get personas sorted by priority
        personas = prospect_analysis["persona_mapping"]["decision_makers"]
        
        if not personas:
            return "facilities_vp"
        
        # Sort by priority_order
        sorted_personas = sorted(personas, key=lambda x: x.get("priority_order", 5))
        
        return sorted_personas[0]["persona_type"]
    
    def _print_summary(self):
        """Print generation summary"""
        
        total_emails = sum(len(r["sequence"]) for r in self.results)
        avg_quality = sum(
            sum(e["quality_score"] for e in r["sequence"]) / len(r["sequence"])
            for r in self.results
        ) / len(self.results) if self.results else 0
        
        print(f"\n{'='*60}")
        print("📧 CONTENT GENERATION SUMMARY")
        print(f"{'='*60}")
        print(f"Prospects Processed: {len(self.results)}")
        print(f"Total Emails Generated: {total_emails}")
        print(f"Average Quality Score: {avg_quality:.1f}/10")
        print(f"{'='*60}\n")
    
    def export_to_json(self, filepath: str):
        """Export generated content"""
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"✅ Content exported to {filepath}")
    
    def export_to_clay_format(self, filepath: str):
        """Export in Clay-importable format"""
        
        clay_rows = []
        
        for result in self.results:
            for email in result["sequence"]:
                row = {
                    "company": result["company"],
                    "persona_type": result["persona_type"],
                    "touch_number": email["touch_number"],
                    "subject": email["subject"],
                    "body": email["body"],
                    "personalization_elements": ", ".join(email.get("personalization_used", [])),
                    "quality_score": email["quality_score"],
                    "priority_tier": result["priority_tier"],
                    "status": "ready_to_review"
                }
                clay_rows.append(row)
        
        with open(filepath, 'w') as f:
            json.dump(clay_rows, f, indent=2)
        
        print(f"✅ Clay-formatted content exported to {filepath}")


# Example usage
async def example_content_generation():
    """Example of generating content"""
    
    from agent_builder_system import MasterAgentBuilder, IndustryType
    from prospect_intelligence import BatchProspectProcessor
    
    # Build agent
    builder = MasterAgentBuilder("your-api-key")
    agent = await builder.build_agent(IndustryType.CASINO)
    
    # Analyze prospects first
    processor = BatchProspectProcessor(agent, "your-api-key")
    prospects = [
        {"company_name": "MGM Grand", "domain": "mgmgrand.com", "employee_count": 5000}
    ]
    analyzed = await processor.process_batch(prospects)
    
    # Generate content
    content_gen = BatchContentGenerator(agent, "your-api-key")
    sequences = await content_gen.generate_sequences_batch(analyzed)
    
    # Export for Clay
    content_gen.export_to_clay_format("/home/claude/generated_content_clay.json")
    
    return sequences


if __name__ == "__main__":
    asyncio.run(example_content_generation())

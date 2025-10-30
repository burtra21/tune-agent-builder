"""
Clay Integration
Read enriched prospect data from Clay, write analysis and content back
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import httpx


class ClayAPI:
    """Clay API client"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.clay.com/v1"
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

    async def get_table(self, table_id: str) -> Dict:
        """Get table metadata"""
        response = await self.client.get(f"{self.base_url}/tables/{table_id}")
        response.raise_for_status()
        return response.json()

    async def list_rows(self, table_id: str, limit: int = 100, offset: int = 0) -> List[Dict]:
        """List rows from table"""
        response = await self.client.get(
            f"{self.base_url}/tables/{table_id}/rows",
            params={"limit": limit, "offset": offset}
        )
        response.raise_for_status()
        return response.json().get("rows", [])

    async def get_row(self, table_id: str, row_id: str) -> Dict:
        """Get single row"""
        response = await self.client.get(
            f"{self.base_url}/tables/{table_id}/rows/{row_id}"
        )
        response.raise_for_status()
        return response.json()

    async def create_row(self, table_id: str, data: Dict) -> Dict:
        """Create new row"""
        response = await self.client.post(
            f"{self.base_url}/tables/{table_id}/rows",
            json=data
        )
        response.raise_for_status()
        return response.json()

    async def update_row(self, table_id: str, row_id: str, data: Dict) -> Dict:
        """Update existing row"""
        response = await self.client.patch(
            f"{self.base_url}/tables/{table_id}/rows/{row_id}",
            json=data
        )
        response.raise_for_status()
        return response.json()

    async def create_table(self, name: str, columns: List[Dict]) -> Dict:
        """Create new table"""
        response = await self.client.post(
            f"{self.base_url}/tables",
            json={"name": name, "columns": columns}
        )
        response.raise_for_status()
        return response.json()


class ClayIntegration:
    """High-level Clay integration for Tune workflows"""

    def __init__(self, clay_api_key: str, industry_agent):
        self.api = ClayAPI(clay_api_key)
        self.agent = industry_agent
        self.table_ids = {}  # Cache table IDs

    async def setup_tables(self) -> Dict[str, str]:
        """
        Setup Clay tables for Tune workflow

        Creates 3 tables:
        1. Master Prospects - Enriched companies with analysis
        2. Decision Makers - Individual contacts
        3. Generated Content - Email sequences ready to send
        """

        print("🏗️  Setting up Clay tables...")

        # Table 1: Master Prospects
        prospects_table = await self._create_prospects_table()
        self.table_ids['prospects'] = prospects_table['id']

        # Table 2: Decision Makers
        contacts_table = await self._create_contacts_table()
        self.table_ids['contacts'] = contacts_table['id']

        # Table 3: Generated Content
        content_table = await self._create_content_table()
        self.table_ids['content'] = content_table['id']

        print(f"✅ Tables created:")
        print(f"   Prospects: {self.table_ids['prospects']}")
        print(f"   Contacts: {self.table_ids['contacts']}")
        print(f"   Content: {self.table_ids['content']}")

        return self.table_ids

    async def _create_prospects_table(self) -> Dict:
        """Create Master Prospects table"""

        columns = [
            # Basic Info (from Clay enrichment)
            {"name": "company_name", "type": "text"},
            {"name": "domain", "type": "text"},
            {"name": "industry", "type": "text"},
            {"name": "employee_count", "type": "number"},
            {"name": "revenue", "type": "number"},
            {"name": "headquarters", "type": "text"},
            {"name": "linkedin_url", "type": "url"},

            # Our Analysis
            {"name": "composite_score", "type": "number"},
            {"name": "priority_tier", "type": "text"},  # A, B, C
            {"name": "intent_score", "type": "number"},
            {"name": "technical_fit_score", "type": "number"},
            {"name": "urgency_score", "type": "number"},

            # Savings Projection
            {"name": "annual_savings_dollars", "type": "number"},
            {"name": "savings_percentage", "type": "number"},
            {"name": "payback_months", "type": "number"},
            {"name": "five_year_value", "type": "number"},

            # Intent Signals
            {"name": "sustainability_maturity", "type": "number"},  # 1-5
            {"name": "intent_signals_found", "type": "text"},  # JSON
            {"name": "personalization_points", "type": "text"},  # JSON array

            # Status
            {"name": "analysis_status", "type": "text"},  # pending, analyzed, content_generated
            {"name": "analyzed_at", "type": "date"},
            {"name": "outreach_status", "type": "text"},  # not_started, in_sequence, replied, closed
        ]

        return await self.api.create_table(
            name=f"Tune - {self.agent.industry.value.title()} Prospects",
            columns=columns
        )

    async def _create_contacts_table(self) -> Dict:
        """Create Decision Makers / Contacts table"""

        columns = [
            # Contact Info (from Clay enrichment)
            {"name": "full_name", "type": "text"},
            {"name": "email", "type": "email"},
            {"name": "title", "type": "text"},
            {"name": "linkedin_url", "type": "url"},
            {"name": "company_name", "type": "text"},

            # Our Mapping
            {"name": "persona_type", "type": "text"},  # facilities_vp, esg_director, etc
            {"name": "decision_authority", "type": "text"},  # Decision Maker, Influencer, etc
            {"name": "priority_order", "type": "number"},  # 1 = primary contact

            # Outreach
            {"name": "outreach_status", "type": "text"},
            {"name": "current_touch", "type": "number"},
            {"name": "last_contacted", "type": "date"},
            {"name": "replied", "type": "boolean"},
            {"name": "meeting_booked", "type": "boolean"},
        ]

        return await self.api.create_table(
            name=f"Tune - {self.agent.industry.value.title()} Contacts",
            columns=columns
        )

    async def _create_content_table(self) -> Dict:
        """Create Generated Content table"""

        columns = [
            # Reference
            {"name": "company_name", "type": "text"},
            {"name": "contact_email", "type": "email"},
            {"name": "persona_type", "type": "text"},

            # Email Content
            {"name": "touch_number", "type": "number"},
            {"name": "subject_line", "type": "text"},
            {"name": "email_body", "type": "text"},
            {"name": "framework_used", "type": "text"},  # PEC+G, BAB, etc

            # Quality
            {"name": "quality_score", "type": "number"},  # 0-10
            {"name": "personalization_depth", "type": "number"},

            # Status
            {"name": "status", "type": "text"},  # draft, approved, sent, opened, clicked, replied
            {"name": "generated_at", "type": "date"},
            {"name": "sent_at", "type": "date"},
            {"name": "opened_at", "type": "date"},
            {"name": "replied_at", "type": "date"},

            # Metadata
            {"name": "priority_tier", "type": "text"},
        ]

        return await self.api.create_table(
            name=f"Tune - {self.agent.industry.value.title()} Content",
            columns=columns
        )

    async def read_enriched_prospects(self, prospects_table_id: str,
                                     limit: int = 100) -> List[Dict]:
        """
        Read Clay-enriched prospects ready for analysis

        Expects Clay table with enrichment columns already filled
        """

        print(f"📖 Reading {limit} prospects from Clay...")

        rows = await self.api.list_rows(prospects_table_id, limit=limit)

        prospects = []
        for row in rows:
            # Extract Clay enrichment data
            fields = row.get("fields", {})

            prospect = {
                "row_id": row.get("id"),  # Save for updating later
                "company_name": fields.get("company_name") or fields.get("name"),
                "domain": fields.get("domain") or fields.get("website"),
                "employee_count": fields.get("employee_count") or fields.get("employees"),
                "industry": fields.get("industry"),
                "revenue": fields.get("revenue") or fields.get("estimated_revenue"),
                "headquarters": fields.get("headquarters") or fields.get("hq_location"),
                "founded_year": fields.get("founded_year") or fields.get("founded"),
                "linkedin_url": fields.get("linkedin_url") or fields.get("linkedin_company_url"),
                "technologies": fields.get("technologies") or [],
                "locations_count": fields.get("locations_count") or 1,
            }

            prospects.append(prospect)

        print(f"✅ Read {len(prospects)} enriched prospects")

        return prospects

    async def write_prospect_analysis(self, prospects_table_id: str,
                                     row_id: str, analysis: Dict):
        """Write analysis results back to Clay prospect row"""

        update_data = {
            "composite_score": analysis["composite_score"],
            "priority_tier": analysis["priority_tier"],
            "intent_score": analysis["scores"]["intent"],
            "technical_fit_score": analysis["scores"]["technical_fit"],
            "urgency_score": analysis["scores"]["urgency"],
            "annual_savings_dollars": analysis["savings_projection"]["annual_savings_dollars"],
            "savings_percentage": analysis["savings_projection"]["savings_percentage"],
            "payback_months": analysis["savings_projection"]["payback_period_months"],
            "five_year_value": analysis["savings_projection"]["five_year_savings"],
            "sustainability_maturity": analysis.get("sustainability_maturity", 2),
            "intent_signals_found": json.dumps(analysis["intent_signals"]),
            "personalization_points": json.dumps(analysis["personalization_intel"]["personalization_points"]),
            "analysis_status": "analyzed",
            "analyzed_at": datetime.now().isoformat(),
        }

        await self.api.update_row(prospects_table_id, row_id, update_data)

        print(f"✅ Wrote analysis for {analysis['company_profile']['company_name']}")

    async def write_generated_content(self, content_table_id: str,
                                     content_results: List[Dict]):
        """Write generated email sequences to Clay content table"""

        print(f"✍️  Writing {len(content_results)} sequences to Clay...")

        for result in content_results:
            for email in result["sequence"]:
                row_data = {
                    "company_name": result["company"],
                    "persona_type": result["persona_type"],
                    "touch_number": email["touch_number"],
                    "subject_line": email["subject"],
                    "email_body": email["body"],
                    "framework_used": email.get("framework_used", "Unknown"),
                    "quality_score": email["quality_score"],
                    "personalization_depth": len(email.get("personalization_used", [])),
                    "status": "ready_to_review" if email["quality_score"] >= 7 else "draft",
                    "generated_at": datetime.now().isoformat(),
                    "priority_tier": result["priority_tier"],
                }

                await self.api.create_row(content_table_id, row_data)

        print(f"✅ Wrote content to Clay")

    async def get_prospects_needing_analysis(self, prospects_table_id: str) -> List[Dict]:
        """Get prospects that are enriched but not yet analyzed"""

        all_rows = await self.api.list_rows(prospects_table_id, limit=1000)

        prospects_to_analyze = []
        for row in all_rows:
            fields = row.get("fields", {})

            # Check if enriched but not analyzed
            has_enrichment = fields.get("employee_count") or fields.get("domain")
            not_analyzed = not fields.get("analysis_status") or fields.get("analysis_status") == "pending"

            if has_enrichment and not_analyzed:
                prospect = {
                    "row_id": row.get("id"),
                    "company_name": fields.get("company_name"),
                    "domain": fields.get("domain"),
                    "employee_count": fields.get("employee_count"),
                    "industry": fields.get("industry"),
                    "revenue": fields.get("revenue"),
                    "headquarters": fields.get("headquarters"),
                    "linkedin_url": fields.get("linkedin_url"),
                }
                prospects_to_analyze.append(prospect)

        print(f"📋 Found {len(prospects_to_analyze)} prospects needing analysis")

        return prospects_to_analyze


class ClayWebhookHandler:
    """Handle webhooks from Clay for automation"""

    def __init__(self, industry_agent, claude_api_key: str, clay_api_key: str):
        self.agent = industry_agent
        self.claude_api_key = claude_api_key
        self.clay = ClayIntegration(clay_api_key, industry_agent)

    async def handle_new_prospect(self, webhook_data: Dict) -> Dict:
        """
        Handle new prospect added to Clay

        Workflow:
        1. Prospect added to Clay table
        2. Clay enriches (Apollo, Clearbit, etc.)
        3. Clay webhook triggers this function
        4. We analyze and write back
        """

        from prospect_intelligence import ProspectIntelligence

        table_id = webhook_data.get("table_id")
        row_id = webhook_data.get("row_id")
        prospect_data = webhook_data.get("data", {})

        print(f"🔔 New prospect webhook: {prospect_data.get('company_name')}")

        # Analyze
        intelligence = ProspectIntelligence(self.agent, self.claude_api_key)
        analysis = await intelligence.analyze_prospect(prospect_data)

        # Write back to Clay
        await self.clay.write_prospect_analysis(table_id, row_id, analysis)

        return {
            "status": "success",
            "company": prospect_data.get("company_name"),
            "score": analysis["composite_score"],
            "tier": analysis["priority_tier"]
        }

    async def handle_trigger_content_generation(self, webhook_data: Dict) -> Dict:
        """
        Handle content generation trigger

        Workflow:
        1. Prospect analyzed with high score
        2. Clay webhook triggers content generation
        3. We generate email sequence
        4. Write to Clay content table
        """

        from content_generator import ContentGenerator

        prospect_analysis = webhook_data.get("prospect_analysis")
        persona_type = webhook_data.get("persona_type")

        print(f"🔔 Content generation webhook: {prospect_analysis['company_profile']['company_name']}")

        # Generate
        generator = ContentGenerator(self.agent, self.claude_api_key)
        sequence = await generator.generate_full_sequence(prospect_analysis, persona_type)

        # Write to Clay
        content_table_id = webhook_data.get("content_table_id")
        if content_table_id:
            content_result = {
                "company": prospect_analysis["company_profile"]["company_name"],
                "persona_type": persona_type,
                "sequence": sequence,
                "priority_tier": prospect_analysis["priority_tier"]
            }
            await self.clay.write_generated_content(content_table_id, [content_result])

        return {
            "status": "success",
            "emails_generated": len(sequence),
            "avg_quality": sum(e["quality_score"] for e in sequence) / len(sequence)
        }


# Example usage
async def example_clay_workflow():
    """Example end-to-end Clay workflow"""

    from agent_builder_system import MasterAgentBuilder, IndustryType
    from prospect_intelligence import BatchProspectProcessor
    from content_generator import BatchContentGenerator

    CLAUDE_API_KEY = "your-claude-api-key"
    CLAY_API_KEY = "your-clay-api-key"

    # 1. Build agent
    print("🏗️  Building agent...")
    builder = MasterAgentBuilder(CLAUDE_API_KEY)
    agent = await builder.build_agent(IndustryType.CASINO)

    # 2. Setup Clay tables
    print("\n📊 Setting up Clay tables...")
    clay = ClayIntegration(CLAY_API_KEY, agent)
    table_ids = await clay.setup_tables()

    # 3. Read enriched prospects from Clay
    # (Assuming you've already added prospects and Clay enriched them)
    prospects_table_id = table_ids['prospects']
    enriched_prospects = await clay.read_enriched_prospects(prospects_table_id, limit=10)

    # 4. Analyze prospects
    print("\n🔍 Analyzing prospects...")
    processor = BatchProspectProcessor(agent, CLAUDE_API_KEY)
    analyses = await processor.process_batch(enriched_prospects)

    # 5. Write analyses back to Clay
    print("\n📝 Writing analyses to Clay...")
    for analysis, prospect in zip(analyses, enriched_prospects):
        await clay.write_prospect_analysis(
            prospects_table_id,
            prospect["row_id"],
            analysis
        )

    # 6. Generate content for high-scorers (A-tier)
    high_scorers = [a for a in analyses if a["priority_tier"] == "A"]
    if high_scorers:
        print(f"\n✍️  Generating content for {len(high_scorers)} A-tier prospects...")
        content_gen = BatchContentGenerator(agent, CLAUDE_API_KEY)
        content_results = await content_gen.generate_sequences_batch(high_scorers)

        # 7. Write content to Clay
        content_table_id = table_ids['content']
        await clay.write_generated_content(content_table_id, content_results)

    print("\n✅ Complete Clay workflow finished!")


if __name__ == "__main__":
    asyncio.run(example_clay_workflow())

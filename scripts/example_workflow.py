"""
Example End-to-End Workflow
Complete Tune campaign from agent building to content delivery
"""

import asyncio
import json
from agent_builder_system import MasterAgentBuilder, IndustryType
from prospect_intelligence import BatchProspectProcessor
from content_generator import BatchContentGenerator
from clay_integration import ClayIntegration
from database import TuneDatabase
from analytics import AnalyticsEngine


async def run_complete_campaign():
    """
    Complete end-to-end campaign workflow

    Steps:
    1. Build industry agent
    2. Create campaign in database
    3. Read Clay-enriched prospects
    4. Analyze prospects (web research + scoring)
    5. Write analysis back to Clay
    6. Generate content for high-scorers
    7. Write content to Clay
    8. Track performance
    9. Get analytics
    """

    # ============================================================================
    # CONFIGURATION
    # ============================================================================

    with open("config.json", "r") as f:
        config = json.load(f)

    CLAUDE_API_KEY = config["claude_api_key"]
    CLAY_API_KEY = config["clay_api_key"]
    INDUSTRY = IndustryType.CASINO  # Change to your industry

    print("\n" + "="*80)
    print("🚀 TUNE CAMPAIGN BUILDER - COMPLETE WORKFLOW")
    print("="*80 + "\n")

    # ============================================================================
    # STEP 1: BUILD INDUSTRY AGENT
    # ============================================================================

    print("STEP 1: Building Industry Agent")
    print("-" * 80)

    builder = MasterAgentBuilder(CLAUDE_API_KEY)
    agent = await builder.build_agent(
        industry=INDUSTRY,
        config={"personalization_depth": 5}  # Maximum personalization
    )

    # Save agent for reuse
    agent.save(f"agents/{INDUSTRY.value}_agent.json")

    print(f"✅ Agent built: {agent.name}")
    print(f"   Personas: {len(agent.ideal_personas)}")
    print(f"   Savings Benchmark: {agent.savings_benchmarks['typical_percentage']}%\n")

    # ============================================================================
    # STEP 2: CREATE CAMPAIGN
    # ============================================================================

    print("STEP 2: Creating Campaign in Database")
    print("-" * 80)

    db = TuneDatabase("tune_campaigns.db")
    campaign_id = db.create_campaign(
        name=f"{INDUSTRY.value.title()} - Q1 2025",
        industry=INDUSTRY.value
    )

    print(f"✅ Campaign created: ID {campaign_id}\n")

    # ============================================================================
    # STEP 3: SETUP CLAY INTEGRATION
    # ============================================================================

    print("STEP 3: Setting up Clay Tables")
    print("-" * 80)

    clay = ClayIntegration(CLAY_API_KEY, agent)
    table_ids = await clay.setup_tables()

    print(f"✅ Clay tables created:")
    for table_name, table_id in table_ids.items():
        print(f"   {table_name}: {table_id}")
    print()

    # ============================================================================
    # STEP 4: READ CLAY-ENRICHED PROSPECTS
    # ============================================================================

    print("STEP 4: Reading Clay-Enriched Prospects")
    print("-" * 80)

    # In production, you would have already:
    # 1. Imported prospects to Clay
    # 2. Run Clay enrichment waterfalls (Apollo, Clearbit, etc.)
    # 3. Now read the enriched data

    # For this example, we'll simulate Clay-enriched data
    prospects_table_id = table_ids.get("prospects") or "your_prospects_table_id"

    # Option A: Read from Clay (uncomment in production)
    # enriched_prospects = await clay.read_enriched_prospects(prospects_table_id, limit=50)

    # Option B: Simulate enriched data for example
    enriched_prospects = [
        {
            "row_id": "row_1",
            "company_name": "MGM Grand Las Vegas",
            "domain": "mgmgrand.com",
            "employee_count": 5000,
            "industry": "casino",
            "revenue": 2500000000,
            "headquarters": "Las Vegas, NV",
            "linkedin_url": "https://linkedin.com/company/mgm-grand"
        },
        {
            "row_id": "row_2",
            "company_name": "Caesars Palace",
            "domain": "caesarspalace.com",
            "employee_count": 4200,
            "industry": "casino",
            "revenue": 1800000000,
            "headquarters": "Las Vegas, NV",
            "linkedin_url": "https://linkedin.com/company/caesars-palace"
        },
        {
            "row_id": "row_3",
            "company_name": "Bellagio",
            "domain": "bellagio.com",
            "employee_count": 3500,
            "industry": "casino",
            "revenue": 1500000000,
            "headquarters": "Las Vegas, NV",
            "linkedin_url": "https://linkedin.com/company/bellagio"
        }
    ]

    print(f"✅ Read {len(enriched_prospects)} Clay-enriched prospects\n")

    # ============================================================================
    # STEP 5: ANALYZE PROSPECTS
    # ============================================================================

    print("STEP 5: Analyzing Prospects (Web Research + Scoring)")
    print("-" * 80)

    processor = BatchProspectProcessor(agent, CLAUDE_API_KEY)
    analyses = await processor.process_batch(enriched_prospects, concurrency=3)

    print(f"\n✅ Analyzed {len(analyses)} prospects")
    print(f"   Average Score: {sum(a['composite_score'] for a in analyses) / len(analyses):.1f}/100\n")

    # ============================================================================
    # STEP 6: SAVE TO DATABASE
    # ============================================================================

    print("STEP 6: Saving Analyses to Database")
    print("-" * 80)

    for analysis, prospect in zip(analyses, enriched_prospects):
        prospect_id = db.insert_prospect(campaign_id, prospect, analysis)
        print(f"   Saved: {prospect['company_name']} (Score: {analysis['composite_score']}/100)")

    print(f"\n✅ Saved {len(analyses)} prospect analyses to database\n")

    # ============================================================================
    # STEP 7: WRITE ANALYSIS BACK TO CLAY
    # ============================================================================

    print("STEP 7: Writing Analysis Back to Clay")
    print("-" * 80)

    for analysis, prospect in zip(analyses, enriched_prospects):
        await clay.write_prospect_analysis(
            prospects_table_id,
            prospect["row_id"],
            analysis
        )
        print(f"   Updated Clay: {prospect['company_name']}")

    print(f"\n✅ Updated {len(analyses)} Clay rows with analysis\n")

    # ============================================================================
    # STEP 8: GENERATE CONTENT FOR HIGH-SCORERS
    # ============================================================================

    print("STEP 8: Generating Content for High-Score Prospects")
    print("-" * 80)

    # Filter A and B tier prospects
    high_scorers = [a for a in analyses if a["priority_tier"] in ["A", "B"]]

    print(f"High-score prospects ({len(high_scorers)}):")
    for prospect in high_scorers:
        print(f"   • {prospect['company_profile']['company_name']} - Tier {prospect['priority_tier']} ({prospect['composite_score']}/100)")

    print()

    content_gen = BatchContentGenerator(agent, CLAUDE_API_KEY)
    content_results = await content_gen.generate_sequences_batch(high_scorers, concurrency=2)

    total_emails = sum(len(r["sequence"]) for r in content_results)
    avg_quality = sum(
        sum(e["quality_score"] for e in r["sequence"]) / len(r["sequence"])
        for r in content_results
    ) / len(content_results) if content_results else 0

    print(f"\n✅ Generated {total_emails} emails for {len(high_scorers)} prospects")
    print(f"   Average Quality Score: {avg_quality:.1f}/10\n")

    # ============================================================================
    # STEP 9: WRITE CONTENT TO CLAY
    # ============================================================================

    print("STEP 9: Writing Generated Content to Clay")
    print("-" * 80)

    content_table_id = table_ids.get("content") or "your_content_table_id"
    await clay.write_generated_content(content_table_id, content_results)

    print(f"✅ Wrote {total_emails} emails to Clay content table\n")

    # ============================================================================
    # STEP 10: SAVE CONTENT TO DATABASE
    # ============================================================================

    print("STEP 10: Saving Content to Database")
    print("-" * 80)

    for result in content_results:
        prospect_id = 1  # Would lookup from database in production
        for email in result["sequence"]:
            content_id = db.insert_generated_content(
                prospect_id=prospect_id,
                campaign_id=campaign_id,
                contact_id=None,
                email_data=email
            )

    print(f"✅ Saved {total_emails} emails to database\n")

    # ============================================================================
    # STEP 11: GET ANALYTICS
    # ============================================================================

    print("STEP 11: Campaign Analytics")
    print("-" * 80)

    analytics = AnalyticsEngine(db)

    # Print report
    analytics.print_campaign_report(campaign_id, days=7)

    # ============================================================================
    # SUMMARY
    # ============================================================================

    print("\n" + "="*80)
    print("✨ CAMPAIGN SETUP COMPLETE!")
    print("="*80)
    print(f"\nCampaign ID: {campaign_id}")
    print(f"Prospects Analyzed: {len(analyses)}")
    print(f"High-Score Prospects: {len(high_scorers)}")
    print(f"Emails Generated: {total_emails}")
    print(f"Average Quality: {avg_quality:.1f}/10")
    print(f"\nNext Steps:")
    print("1. Review generated content in Clay")
    print("2. Approve high-quality emails (score ≥ 7)")
    print("3. Setup n8n workflow for delivery")
    print("4. Monitor performance in analytics dashboard")
    print("5. Iterate based on performance data")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(run_complete_campaign())

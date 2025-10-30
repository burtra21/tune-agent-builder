"""
Quick Start Script
Gets you up and running with Tune Agent Builder in 5 minutes
"""

import asyncio
import json
import os
from pathlib import Path


async def setup():
    """Quick setup wizard"""

    print("\n" + "="*70)
    print("🚀 TUNE AGENT BUILDER - QUICK START")
    print("="*70 + "\n")

    # Check if config exists
    if os.path.exists("config.json"):
        print("✅ config.json found")
        with open("config.json", "r") as f:
            config = json.load(f)
    else:
        print("⚠️  config.json not found. Creating from template...")

        # Get API keys
        print("\nPlease enter your API keys:")
        claude_key = input("Claude API key (sk-ant-...): ").strip()
        clay_key = input("Clay API key (or press Enter to skip): ").strip() or "optional"

        config = {
            "claude_api_key": claude_key,
            "clay_api_key": clay_key,
            "database_path": "tune_campaigns.db",
            "features": {
                "enable_web_research": True,
                "enable_intent_detection": True,
                "min_quality_score": 7.0,
                "max_concurrency": 3
            }
        }

        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)

        print("✅ config.json created")

    # Create agents directory
    Path("agents").mkdir(exist_ok=True)
    print("✅ agents/ directory ready")

    # Initialize database
    print("\n📊 Initializing database...")
    from database import TuneDatabase
    db = TuneDatabase(config.get("database_path", "tune_campaigns.db"))
    print("✅ Database initialized")

    # Build a sample agent
    print("\n🏗️  Building sample casino agent...")
    from agent_builder_system import MasterAgentBuilder, IndustryType

    builder = MasterAgentBuilder(config["claude_api_key"])
    agent = await builder.build_agent(IndustryType.CASINO)
    agent.save("agents/casino_agent.json")

    print("✅ Casino agent built and saved")

    # Create sample campaign
    print("\n📋 Creating sample campaign...")
    campaign_id = db.create_campaign("Sample Casino Campaign", "casino")
    print(f"✅ Campaign created (ID: {campaign_id})")

    # Sample prospect analysis
    print("\n🔍 Analyzing sample prospect...")
    from prospect_intelligence import ProspectIntelligence

    intelligence = ProspectIntelligence(agent, config["claude_api_key"])

    sample_prospect = {
        "company_name": "MGM Grand Las Vegas",
        "domain": "mgmgrand.com",
        "employee_count": 5000,
        "industry": "casino",
        "revenue": 2500000000,
        "headquarters": "Las Vegas, NV"
    }

    analysis = await intelligence.analyze_prospect(sample_prospect)

    print(f"\n📊 SAMPLE ANALYSIS RESULTS:")
    print(f"   Company: {analysis['company_profile']['company_name']}")
    print(f"   Composite Score: {analysis['composite_score']}/100")
    print(f"   Priority Tier: {analysis['priority_tier']}")
    print(f"   Annual Savings: ${analysis['savings_projection']['annual_savings_dollars']:,.0f}")
    print(f"   Payback Period: {analysis['savings_projection']['payback_period_months']} months")

    # Save to database
    prospect_id = db.insert_prospect(campaign_id, sample_prospect, analysis)
    print(f"\n✅ Prospect saved to database (ID: {prospect_id})")

    # Generate sample content
    print("\n✍️  Generating sample email sequence...")
    from content_generator import ContentGenerator

    generator = ContentGenerator(agent, config["claude_api_key"])
    sequence = await generator.generate_full_sequence(
        prospect_analysis=analysis,
        persona_type="facilities_vp"
    )

    print(f"\n📧 SAMPLE EMAIL (Touch 1):")
    print(f"   Subject: {sequence[0]['subject']}")
    print(f"   Quality Score: {sequence[0]['quality_score']}/10")
    print(f"   Body Preview: {sequence[0]['body'][:200]}...")

    # Save content to database
    for email in sequence:
        db.insert_generated_content(
            prospect_id=prospect_id,
            campaign_id=campaign_id,
            contact_id=None,
            email_data=email
        )

    print(f"\n✅ Generated {len(sequence)} emails and saved to database")

    # Final instructions
    print("\n" + "="*70)
    print("🎉 SETUP COMPLETE!")
    print("="*70)
    print("\nYou now have:")
    print("  ✅ Configuration set up")
    print("  ✅ Database initialized")
    print("  ✅ Sample casino agent built")
    print("  ✅ Sample campaign created")
    print("  ✅ Sample prospect analyzed")
    print("  ✅ Sample content generated")

    print("\n📚 NEXT STEPS:")
    print("\n1. Start the API server:")
    print("   uvicorn api_server:app --reload --port 8000")
    print("\n2. View API docs:")
    print("   http://localhost:8000/docs")
    print("\n3. Run complete workflow:")
    print("   python example_workflow.py")
    print("\n4. Read the docs:")
    print("   README_V2.md - Complete documentation")
    print("   UPGRADE_SUMMARY.md - What's new")

    print("\n5. Setup Clay integration:")
    print("   - Get Clay API key")
    print("   - Run: python -c 'from clay_integration import *; ...'")

    print("\n💡 PRO TIP: Check out example_workflow.py for a complete end-to-end example")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(setup())

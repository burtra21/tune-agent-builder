"""
Example: Using the Casino Agent to analyze prospects and generate content
"""

import asyncio
import json
from prospect_intelligence import ProspectIntelligenceEngine
from content_generator import ContentGenerator

async def analyze_casino_prospects():
    """Analyze real casino prospects using the built agent"""

    # Load the casino agent
    with open('agents/casino_agent.json', 'r') as f:
        agent_data = json.load(f)

    print("🎰 Casino Agent Loaded!")
    print(f"Agent: {agent_data['name']}")
    print(f"Personas: {len(agent_data['ideal_personas'])}")
    print(f"Average Savings: {agent_data['savings_benchmarks']['typical_percentage']}%\n")

    # Example casino prospects to analyze
    prospects = [
        {
            "company_name": "MGM Grand",
            "domain": "mgmgrand.com",
            "employee_count": 5000,
            "location": "Las Vegas, NV"
        },
        {
            "company_name": "Caesars Palace",
            "domain": "caesars.com",
            "employee_count": 4500,
            "location": "Las Vegas, NV"
        },
        {
            "company_name": "The Venetian",
            "domain": "venetian.com",
            "employee_count": 6000,
            "location": "Las Vegas, NV"
        }
    ]

    print("=" * 60)
    print("PROSPECT ANALYSIS")
    print("=" * 60)

    # Initialize intelligence engine with your Claude API key
    # Uncomment to use:
    # from dotenv import load_dotenv
    # import os
    # load_dotenv()
    # claude_api_key = os.getenv("CLAUDE_API_KEY")
    #
    # intel_engine = ProspectIntelligenceEngine(agent_data, claude_api_key)
    #
    # for prospect in prospects:
    #     analysis = await intel_engine.analyze_prospect(prospect)
    #     print(f"\n{prospect['company_name']}:")
    #     print(f"  Intent Score: {analysis['intent_score']}/100")
    #     print(f"  Composite Score: {analysis['composite_score']}/100")
    #     print(f"  Priority Tier: {analysis['priority_tier']}")
    #     print(f"  Estimated Annual Savings: ${analysis['estimated_savings']:,}")

    # For now, just show the agent capabilities
    print("\nAgent is ready to:")
    print("✓ Score prospects 0-100 based on intent, fit, urgency")
    print("✓ Identify 60+ buying signals across 6 categories")
    print("✓ Generate persona-specific value propositions")
    print("✓ Create 5-touch email sequences")
    print("✓ Estimate savings based on company size/location")

    print("\n" + "=" * 60)
    print("INTENT SIGNALS THE AGENT LOOKS FOR")
    print("=" * 60)

    for category, signals in agent_data['intent_signals'].items():
        print(f"\n{category.replace('_', ' ').title()}: ({len(signals)} signals)")
        for signal in signals[:3]:  # Show first 3
            print(f"  • {signal}")
        if len(signals) > 3:
            print(f"  ... and {len(signals) - 3} more")

if __name__ == "__main__":
    asyncio.run(analyze_casino_prospects())

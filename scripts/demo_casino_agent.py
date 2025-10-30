"""
Demo: View Casino Agent Capabilities
"""

import json

# Load the casino agent
with open('agents/casino_agent.json', 'r') as f:
    agent = json.load(f)

print("=" * 70)
print("🎰 CASINO AGENT LOADED")
print("=" * 70)
print(f"Name: {agent['name']}")
print(f"Version: {agent['version']}")
print(f"Average Savings: {agent['savings_benchmarks']['typical_percentage']}%")
print(f"Typical Payback: {agent['savings_benchmarks']['payback_months']} months")

print("\n" + "=" * 70)
print("KEY BUYER PERSONAS (5 Total)")
print("=" * 70)

for i, persona in enumerate(agent['ideal_personas'], 1):
    print(f"\n{i}. {persona['persona_type'].replace('_', ' ').title()}")
    print(f"   Decision Authority: {persona['decision_authority']}")
    print(f"   Budget Influence: {persona['budget_influence']}")
    print(f"   Top Priorities:")
    for priority in persona['priorities'][:3]:
        print(f"     • {priority}")

print("\n" + "=" * 70)
print("INTENT SIGNALS (60 Total Across 6 Categories)")
print("=" * 70)

for category, signals in agent['intent_signals'].items():
    print(f"\n{category.replace('_', ' ').title()} ({len(signals)} signals):")
    for signal in signals[:2]:  # Show first 2
        print(f"  • {signal}")
    if len(signals) > 2:
        print(f"  ... plus {len(signals) - 2} more signals")

print("\n" + "=" * 70)
print("VALUE PROPOSITIONS BY PERSONA")
print("=" * 70)

for persona_key, value_prop in agent['value_props_by_persona'].items():
    print(f"\n{persona_key.replace('_', ' ').title()}:")
    print(f"  Headline: {value_prop['headline']}")
    print(f"  Benefit: {value_prop['quantified_benefit']}")
    print(f"  Timeframe: {value_prop['timeframe']}")

print("\n" + "=" * 70)
print("EMAIL SEQUENCES")
print("=" * 70)

for persona_key, sequences in agent['email_sequences'].items():
    print(f"\n{persona_key.replace('_', ' ').title()}: {len(sequences)} touches")
    for seq in sequences[:2]:  # Show first 2 touches
        print(f"  Touch {seq['touch_number']}: {seq['goal']} ({seq['max_words']} words max)")

print("\n" + "=" * 70)
print("HOW TO USE THIS AGENT")
print("=" * 70)
print("""
1. Via API Server:
   uvicorn api_server:app --reload --port 8000

   Then POST to:
   - /api/prospects/analyze - Score a prospect
   - /api/content/generate-sequence - Generate emails
   - /api/workflows/complete-pipeline - Full automation

2. Via Python:
   from prospect_intelligence import ProspectIntelligence
   # Use the agent JSON to analyze prospects

3. Via Clay Integration:
   - Agent automatically creates 3 Clay tables
   - Webhook triggers prospect analysis
   - Generated content appears in Clay for review

Ready to power your casino outbound! 🚀
""")

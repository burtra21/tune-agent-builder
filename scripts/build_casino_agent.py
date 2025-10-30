"""
Build Casino Agent Script
Resumes the casino agent build process
"""

import asyncio
import os
from agent_builder_system import MasterAgentBuilder, IndustryType
from dotenv import load_dotenv

async def build_casino_agent():
    """Build and save the casino industry agent"""

    # Load environment variables
    load_dotenv()

    # Get Claude API key
    claude_api_key = os.getenv("CLAUDE_API_KEY")

    if not claude_api_key:
        print("❌ Error: CLAUDE_API_KEY not found in .env file")
        return

    print("🎰 Starting Casino Agent Build Process...\n")

    # Initialize builder
    builder = MasterAgentBuilder(claude_api_key=claude_api_key)

    # Build casino agent with maximum personalization
    casino_agent = await builder.build_agent(
        industry=IndustryType.CASINO,
        config={
            "personalization_depth": 5,  # Maximum personalization
        }
    )

    # Save agent to file
    output_path = "agents/casino_agent.json"
    casino_agent.save(output_path)

    print(f"\n✅ Casino Agent saved to: {output_path}\n")

    # Display summary
    print("=" * 60)
    print("🎰 CASINO AGENT SUMMARY")
    print("=" * 60)
    print(f"Name: {casino_agent.name}")
    print(f"Version: {casino_agent.version}")
    print(f"Ideal Personas: {len(casino_agent.ideal_personas)}")
    print(f"Email Sequences: {len(casino_agent.email_sequences)}")
    print(f"Savings Benchmark: {casino_agent.savings_benchmarks['typical_percentage']}%")
    print(f"Payback Period: {casino_agent.savings_benchmarks['payback_months']} months")
    print("\nKey Personas:")
    for persona in casino_agent.ideal_personas:
        print(f"  • {persona.persona_type.value.replace('_', ' ').title()}")
    print("\nIntent Signal Categories:")
    for category in casino_agent.intent_signals.keys():
        signal_count = len(casino_agent.intent_signals[category])
        print(f"  • {category.replace('_', ' ').title()}: {signal_count} signals")
    print("=" * 60)

    return casino_agent

if __name__ == "__main__":
    asyncio.run(build_casino_agent())

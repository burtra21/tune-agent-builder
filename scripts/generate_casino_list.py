"""
Auto-Generate Casino Prospect List
Uses AI to research and build a comprehensive casino database
"""

import asyncio
import json
import csv
from typing import List, Dict
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

async def generate_casino_list(regions: List[str], min_size: str = "medium") -> List[Dict]:
    """
    Use Claude to research and generate a comprehensive casino list

    Args:
        regions: List of regions (e.g., ["Nevada", "New Jersey", "Pennsylvania"])
        min_size: "small", "medium", or "large"
    """

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    print(f"\n{'='*70}")
    print("AUTO-GENERATING CASINO PROSPECT LIST")
    print(f"{'='*70}")
    print(f"Regions: {', '.join(regions)}")
    print(f"Minimum Size: {min_size}")
    print("\nResearching casinos...\n")

    prompt = f"""Generate a comprehensive list of {min_size}+ casinos in the following regions: {', '.join(regions)}.

For each casino, provide:
1. Company name (official name)
2. Website domain
3. Location (city, state)
4. Estimated employee count
5. Estimated square footage
6. Parent company (if applicable)
7. Property type (resort, standalone, tribal, etc.)

Focus on casinos that would be good prospects for energy efficiency solutions:
- Medium to large properties (50,000+ sqft)
- 24/7 operations
- High energy consumption

Format as a JSON array with these exact fields:
- company_name
- domain
- location
- employee_count (estimate)
- est_sqft (estimate)
- parent_company
- property_type
- notes

Provide at least 20-30 casinos per region if possible. Include major casino resorts, tribal casinos, and regional gaming facilities."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}]
    )

    content = message.content[0].text

    # Extract JSON
    try:
        if '```json' in content:
            json_str = content.split('```json')[1].split('```')[0].strip()
        else:
            json_str = content

        casinos = json.loads(json_str)
        print(f"✅ Found {len(casinos)} casinos")

        # Preview
        print(f"\nSample casinos:")
        for casino in casinos[:5]:
            print(f"  • {casino['company_name']} - {casino['location']}")

        return casinos

    except Exception as e:
        print(f"❌ Error parsing response: {e}")
        print(f"Response preview: {content[:500]}")
        return []

def export_casino_list(casinos: List[Dict], filename: str):
    """Export casino list to CSV"""

    if not casinos:
        print("No casinos to export")
        return

    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=casinos[0].keys())
        writer.writeheader()
        writer.writerows(casinos)

    print(f"\n✅ Exported {len(casinos)} casinos to {filename}")

async def main():
    """Main function"""

    print("🎰 CASINO LIST GENERATOR")
    print("\nThis will research and build a comprehensive casino prospect list.\n")

    # Define target regions
    regions = [
        "Nevada (Las Vegas Strip, Downtown, Locals)",
        "Atlantic City, New Jersey",
        "Pennsylvania",
        "Mississippi (Gulf Coast)",
        "Louisiana",
        "Oklahoma (Tribal casinos)",
        "California (Tribal casinos)",
        "Connecticut (Foxwoods, Mohegan Sun area)",
        "Michigan (Detroit area)",
        "Indiana",
    ]

    print("Target regions:")
    for i, region in enumerate(regions, 1):
        print(f"  {i}. {region}")

    print("\nGenerating comprehensive casino list...")
    print("This may take 2-3 minutes for deep research...\n")

    # Generate list
    casinos = await generate_casino_list(regions, min_size="medium")

    if casinos:
        # Export
        export_casino_list(casinos, "casino_prospect_list.csv")

        # Also save as JSON
        with open("casino_prospect_list.json", 'w') as f:
            json.dump(casinos, f, indent=2)

        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        print(f"Total Casinos Found: {len(casinos)}")

        # Group by state
        by_state = {}
        for casino in casinos:
            state = casino['location'].split(',')[-1].strip()
            by_state[state] = by_state.get(state, 0) + 1

        print("\nBy State:")
        for state, count in sorted(by_state.items(), key=lambda x: x[1], reverse=True):
            print(f"  {state}: {count} casinos")

        print(f"\n{'='*70}")
        print("NEXT STEP")
        print(f"{'='*70}")
        print("\nNow run the batch analysis:")
        print("  python3 batch_casino_analysis_standalone.py")
        print("\nOr edit batch_casino_analysis_standalone.py to load from casino_prospect_list.csv")
    else:
        print("\n❌ Failed to generate casino list")

if __name__ == "__main__":
    asyncio.run(main())

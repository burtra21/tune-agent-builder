"""
Quick Demo: Generate emails for top 10 A-tier casinos and send to Clay
"""

import asyncio
import json
import csv
import httpx
from datetime import datetime
from typing import List, Dict
import anthropic
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAY_WEBHOOK_URL = "https://api.clay.com/v3/sources/webhook/pull-in-data-from-a-webhook-66d60486-9c7c-4a7b-b615-9ddbe021fbab"

# Load casino agent
with open('agents/casino_agent.json', 'r') as f:
    CASINO_AGENT = json.load(f)

async def generate_email_sequence(
    client: anthropic.Anthropic,
    prospect_analysis: Dict,
    persona_type: str,
    num_emails: int
) -> List[Dict]:
    """Generate personalized email sequence"""

    email_frameworks = CASINO_AGENT.get('email_sequences', {}).get(persona_type, [])
    if not email_frameworks:
        email_frameworks = CASINO_AGENT['email_sequences']['facilities_vp']

    frameworks = email_frameworks[:num_emails]
    company = prospect_analysis['company_profile']

    prompt = f"""Generate a {num_emails}-email sequence for {company['company_name']}:

**Key Facts:**
- Location: {company['location']}
- Size: {company['estimated_sqft']:,} sqft
- Annual Savings: ${company['annual_savings_dollars']:,.0f}
- Monthly Savings: ${company['monthly_savings_dollars']:,.0f}
- Payback: {company['payback_months']} months
- 5-Year Value: ${company['five_year_savings']:,.0f}
- Tier: {prospect_analysis['priority_tier']} (Score: {prospect_analysis['composite_score']})

**Target Persona:** {persona_type}

Create {num_emails} compelling emails focused on casino energy waste (24/7 HVAC, gaming floor, kitchen).

Return JSON array:
[
  {{
    "email_number": 1,
    "subject": "Subject line",
    "body": "Email body (150-200 words)",
    "cta": "Call to action",
    "send_delay_days": 0
  }}
]"""

    message = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    content = message.content[0].text

    try:
        if '```json' in content:
            json_str = content.split('```json')[1].split('```')[0].strip()
        else:
            json_str = content

        emails = json.loads(json_str)
        return emails
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        return [{
            "email_number": i+1,
            "subject": f"${company['annual_savings_dollars']:,.0f} energy savings for {company['company_name']}",
            "body": f"Quick note about {company['company_name']}'s energy optimization opportunity. Our analysis shows potential savings of ${company['annual_savings_dollars']:,.0f} annually. Worth a conversation?",
            "cta": "Schedule 15-minute call",
            "send_delay_days": i * 3
        } for i in range(num_emails)]

async def process_prospect(client, prospect_analysis):
    """Generate emails for one prospect"""

    tier = prospect_analysis['priority_tier']
    num_emails = 5 if tier == 'A' else 3
    persona = prospect_analysis['persona_mapping']['primary_persona']

    print(f"  📧 {prospect_analysis['company_profile']['company_name']}: Generating {num_emails} emails...")

    emails = await generate_email_sequence(client, prospect_analysis, persona, num_emails)
    prospect_analysis['email_sequence'] = emails
    prospect_analysis['num_emails_generated'] = len(emails)

    return prospect_analysis

async def send_to_clay(prospect: Dict):
    """Send one prospect to Clay webhook"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(CLAY_WEBHOOK_URL, json=prospect)
            if response.status_code in [200, 201, 202]:
                print(f"    ✅ Sent to Clay")
                return True
            else:
                print(f"    ❌ Clay error: {response.status_code}")
                return False
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False

async def main():
    """Quick demo with top 10 casinos"""

    print(f"\n{'='*70}")
    print("QUICK DEMO: TOP 10 A-TIER CASINOS WITH EMAIL GENERATION")
    print(f"{'='*70}\n")

    # Load analysis
    df = pd.read_csv('casino_analysis_20251029_225746.csv')

    # Parse annual_savings as numeric for sorting
    df['annual_savings_numeric'] = df['annual_savings_dollars'].str.replace('$', '').str.replace(',', '').astype(float)

    # Get top 10 A-tier by savings
    a_tier = df[df['priority_tier'] == 'A'].nlargest(10, 'annual_savings_numeric')

    print(f"Selected top 10 A-tier casinos by savings potential:\n")

    # Convert to analysis format
    prospects = []
    for _, row in a_tier.iterrows():
        annual_savings = float(row['annual_savings_dollars'].replace('$', '').replace(',', ''))
        print(f"  • {row['company_name']}: ${annual_savings:,.0f}/year")

        prospects.append({
            'company_profile': {
                'company_name': row['company_name'],
                'domain': row['domain'],
                'location': row['location'],
                'employee_count': int(row['employee_count']),
                'estimated_sqft': int(row['estimated_sqft']),
                'estimated_energy_spend': float(row['estimated_annual_energy_spend'].replace('$', '').replace(',', '')),
                'annual_savings_dollars': annual_savings,
                'monthly_savings_dollars': float(row['monthly_savings_dollars'].replace('$', '').replace(',', '')),
                'five_year_savings': float(row['five_year_savings'].replace('$', '').replace(',', '')),
                'payback_months': int(row['payback_months']),
                'carbon_reduction_tons': float(row['carbon_reduction_tons']),
            },
            'composite_score': float(row['composite_score']),
            'priority_tier': row['priority_tier'],
            'persona_mapping': {
                'primary_persona': row['primary_persona'],
            }
        })

    print(f"\n{'='*70}")
    print("GENERATING 5-EMAIL SEQUENCES FOR EACH CASINO")
    print(f"{'='*70}\n")

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    # Generate emails (sequential for better progress visibility)
    results = []
    for i, prospect in enumerate(prospects, 1):
        print(f"[{i}/10] {prospect['company_profile']['company_name']}")
        result = await process_prospect(client, prospect)
        results.append(result)

        # Show first email as sample
        if result['email_sequence']:
            email1 = result['email_sequence'][0]
            print(f"    📨 Email 1: \"{email1['subject']}\"")

    # Export to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"top_10_casinos_with_emails_{timestamp}.csv"

    csv_data = []
    for r in results:
        row = {
            'company_name': r['company_profile']['company_name'],
            'domain': r['company_profile']['domain'],
            'location': r['company_profile']['location'],
            'composite_score': r['composite_score'],
            'annual_savings': f"${r['company_profile']['annual_savings_dollars']:,.0f}",
            'num_emails': r['num_emails_generated'],
        }

        # Add emails
        for i, email in enumerate(r['email_sequence'], 1):
            row[f'email_{i}_subject'] = email['subject']
            row[f'email_{i}_body'] = email['body']
            row[f'email_{i}_cta'] = email['cta']

        csv_data.append(row)

    with open(csv_filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
        writer.writeheader()
        writer.writerows(csv_data)

    print(f"\n✅ Exported to {csv_filename}")

    # Also save JSON
    json_filename = csv_filename.replace('.csv', '.json')
    with open(json_filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"✅ Exported to {json_filename}")

    # Send to Clay
    print(f"\n{'='*70}")
    print("SENDING TO CLAY WEBHOOK")
    print(f"{'='*70}\n")

    success_count = 0
    for i, prospect in enumerate(results, 1):
        print(f"[{i}/10] {prospect['company_profile']['company_name']}")
        if await send_to_clay(prospect):
            success_count += 1
        await asyncio.sleep(0.2)  # Rate limit

    # Summary
    print(f"\n{'='*70}")
    print("DEMO COMPLETE")
    print(f"{'='*70}")
    print(f"✅ Casinos analyzed: 10")
    print(f"✅ Emails generated: {sum(r['num_emails_generated'] for r in results)}")
    print(f"✅ Sent to Clay: {success_count}/10")
    print(f"✅ CSV: {csv_filename}")
    print(f"✅ JSON: {json_filename}")
    print(f"\n💡 Next: Run batch_with_email_generation.py for all 133 casinos")

if __name__ == "__main__":
    asyncio.run(main())

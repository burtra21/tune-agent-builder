"""
Complete Batch Processing with Email Generation + Clay Webhook
Generate personalized emails for each casino BEFORE sending to Clay
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

load_dotenv()

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAY_WEBHOOK_URL = "https://api.clay.com/v3/sources/webhook/pull-in-data-from-a-webhook-66d60486-9c7c-4a7b-b615-9ddbe021fbab"

# Load casino agent with email frameworks
with open('agents/casino_agent.json', 'r') as f:
    CASINO_AGENT = json.load(f)

async def generate_email_sequence(
    client: anthropic.Anthropic,
    prospect_analysis: Dict,
    persona_type: str,
    num_emails: int
) -> List[Dict]:
    """
    Generate personalized email sequence for a prospect

    Args:
        prospect_analysis: The full analyzed prospect data
        persona_type: Primary persona (facilities_vp, energy_manager, etc.)
        num_emails: Number of emails in sequence (3 for B-tier, 5 for A-tier)
    """

    # Get email frameworks from agent
    email_frameworks = CASINO_AGENT.get('email_sequences', {}).get(persona_type, [])

    if not email_frameworks:
        # Fallback to facilities_vp if persona not found
        email_frameworks = CASINO_AGENT['email_sequences']['facilities_vp']

    # Take only the number of emails needed
    frameworks = email_frameworks[:num_emails]

    # Extract data
    company = prospect_analysis['company_profile']

    # Build generation prompt
    prompt = f"""Generate a personalized email sequence for this casino prospect:

**Prospect Details:**
- Company: {company['company_name']}
- Location: {company['location']}
- Square Footage: {company['estimated_sqft']:,} sqft
- Annual Energy Spend: ${company['estimated_energy_spend']:,.0f}
- Potential Annual Savings: ${company['annual_savings_dollars']:,.0f}
- Monthly Savings: ${company['monthly_savings_dollars']:,.0f}
- Payback Period: {company['payback_months']} months
- 5-Year Value: ${company['five_year_savings']:,.0f}
- Priority Tier: {prospect_analysis['priority_tier']}
- Composite Score: {prospect_analysis['composite_score']}

**Target Persona:** {persona_type}

**Generate {num_emails} emails using these frameworks:**

{json.dumps(frameworks, indent=2)}

**Requirements:**
1. Each email should be 150-200 words
2. Use casino-specific energy pain points (24/7 HVAC, gaming floor lighting, kitchen operations)
3. Reference their specific savings numbers
4. Progressive sequence: Email 1 = awareness, Email 2 = value proof, Email 3+ = urgency/action
5. Include clear CTAs (schedule demo, review case study, etc.)
6. Professional but conversational tone
7. Subject lines should be punchy and benefit-focused

Return as JSON array with this format:
[
  {{
    "email_number": 1,
    "subject": "Subject line here",
    "body": "Email body here",
    "cta": "Primary call to action",
    "send_delay_days": 0
  }},
  ...
]

Focus on the massive energy waste in casinos and how Tune's 8.59% savings can transform their operations."""

    # Generate emails using Claude
    message = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    content = message.content[0].text

    # Extract JSON
    try:
        if '```json' in content:
            json_str = content.split('```json')[1].split('```')[0].strip()
        else:
            json_str = content

        emails = json.loads(json_str)
        return emails
    except Exception as e:
        print(f"  ⚠️  Email generation error for {company['company_name']}: {e}")
        # Return basic fallback emails
        return [{
            "email_number": i+1,
            "subject": f"Energy savings opportunity for {company['company_name']}",
            "body": f"Hi,\n\nI noticed {company['company_name']} could save ${company['annual_savings_dollars']:,.0f} annually with Tune's energy optimization. Would you be open to a brief call?\n\nBest regards",
            "cta": "Schedule a 15-minute call",
            "send_delay_days": i * 3
        } for i in range(num_emails)]

async def process_prospect_with_emails(
    client: anthropic.Anthropic,
    prospect_analysis: Dict,
    semaphore: asyncio.Semaphore
) -> Dict:
    """Generate emails for a single prospect"""

    async with semaphore:
        # Determine number of emails based on tier
        tier = prospect_analysis['priority_tier']
        num_emails = 5 if tier == 'A' else 3 if tier == 'B' else 1

        persona = prospect_analysis['persona_mapping']['primary_persona']

        print(f"  📧 Generating {num_emails} emails for {prospect_analysis['company_profile']['company_name']} ({tier}-tier, {persona})...")

        # Generate email sequence
        emails = await generate_email_sequence(
            client,
            prospect_analysis,
            persona,
            num_emails
        )

        # Add emails to prospect data
        prospect_analysis['email_sequence'] = emails
        prospect_analysis['num_emails_generated'] = len(emails)

        return prospect_analysis

async def batch_generate_emails(analysis_results: List[Dict]) -> List[Dict]:
    """Generate emails for all prospects concurrently"""

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    print(f"\n{'='*70}")
    print("EMAIL GENERATION FOR ALL PROSPECTS")
    print(f"{'='*70}")
    print(f"Total prospects: {len(analysis_results)}")

    # Count by tier
    a_tier = [r for r in analysis_results if r['priority_tier'] == 'A']
    b_tier = [r for r in analysis_results if r['priority_tier'] == 'B']
    c_tier = [r for r in analysis_results if r['priority_tier'] == 'C']

    print(f"  A-tier: {len(a_tier)} prospects → 5-email sequences")
    print(f"  B-tier: {len(b_tier)} prospects → 3-email sequences")
    print(f"  C-tier: {len(c_tier)} prospects → 1-email touchpoint")

    total_emails = len(a_tier) * 5 + len(b_tier) * 3 + len(c_tier) * 1
    print(f"  Total emails to generate: {total_emails}")
    print(f"\n⏱️  Estimated time: {len(analysis_results) * 3 // 60} minutes (3 concurrent generations)\n")

    # Limit concurrency to avoid rate limits
    semaphore = asyncio.Semaphore(3)

    # Generate emails for all prospects
    tasks = [
        process_prospect_with_emails(client, result, semaphore)
        for result in analysis_results
    ]

    results_with_emails = await asyncio.gather(*tasks)

    print(f"\n✅ Generated {total_emails} personalized emails for {len(results_with_emails)} prospects")

    return results_with_emails

async def send_to_clay_webhook(data: List[Dict]) -> bool:
    """Send complete prospect data (analysis + emails) to Clay webhook"""

    print(f"\n{'='*70}")
    print("SENDING TO CLAY WEBHOOK")
    print(f"{'='*70}")
    print(f"Webhook URL: {CLAY_WEBHOOK_URL}")
    print(f"Sending {len(data)} prospects with complete email sequences...\n")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Send each prospect as individual webhook call
            # (Clay typically expects one record per webhook call)
            success_count = 0

            for i, prospect in enumerate(data, 1):
                try:
                    response = await client.post(
                        CLAY_WEBHOOK_URL,
                        json=prospect,
                        headers={"Content-Type": "application/json"}
                    )

                    if response.status_code in [200, 201, 202]:
                        success_count += 1
                        print(f"  ✅ {i}/{len(data)}: {prospect['company_profile']['company_name']} sent successfully")
                    else:
                        print(f"  ❌ {i}/{len(data)}: {prospect['company_profile']['company_name']} failed (status {response.status_code})")

                    # Rate limit: wait 100ms between requests
                    await asyncio.sleep(0.1)

                except Exception as e:
                    print(f"  ❌ {i}/{len(data)}: {prospect['company_profile']['company_name']} error: {e}")

            print(f"\n✅ Successfully sent {success_count}/{len(data)} prospects to Clay")
            return success_count == len(data)

    except Exception as e:
        print(f"\n❌ Webhook error: {e}")
        return False

def export_with_emails(results: List[Dict], filename: str):
    """Export results with email content to CSV"""

    csv_data = []
    for r in results:
        base_row = {
            'company_name': r['company_profile']['company_name'],
            'domain': r['company_profile']['domain'],
            'location': r['company_profile']['location'],
            'employee_count': r['company_profile']['employee_count'],
            'composite_score': r['composite_score'],
            'priority_tier': r['priority_tier'],
            'estimated_sqft': r['company_profile']['estimated_sqft'],
            'annual_savings_dollars': f"${r['savings_projection']['annual_savings_dollars']:,.0f}",
            'monthly_savings_dollars': f"${r['savings_projection']['monthly_savings_dollars']:,.0f}",
            'five_year_savings': f"${r['savings_projection']['five_year_savings']:,.0f}",
            'primary_persona': r['persona_mapping']['primary_persona'],
            'num_emails': r['num_emails_generated'],
        }

        # Add email columns
        for i, email in enumerate(r['email_sequence'], 1):
            base_row[f'email_{i}_subject'] = email['subject']
            base_row[f'email_{i}_body'] = email['body']
            base_row[f'email_{i}_cta'] = email['cta']
            base_row[f'email_{i}_delay_days'] = email['send_delay_days']

        csv_data.append(base_row)

    # Write CSV
    with open(filename, 'w', newline='') as f:
        if csv_data:
            writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
            writer.writeheader()
            writer.writerows(csv_data)

    print(f"\n✅ Exported {len(csv_data)} prospects with emails to {filename}")

async def main():
    """Main workflow: Load analysis → Generate emails → Send to Clay"""

    print(f"\n{'='*70}")
    print("TUNE CASINO AGENT: COMPLETE BATCH PROCESSING WITH EMAILS")
    print(f"{'='*70}\n")

    # Load the most recent analysis results
    analysis_file = "casino_analysis_20251029_225746.csv"

    print(f"📂 Loading analysis from {analysis_file}...")

    # Read CSV and convert to analysis format
    import pandas as pd
    df = pd.read_csv(analysis_file)

    # Convert CSV rows back to analysis format
    analysis_results = []
    for _, row in df.iterrows():
        # Parse monetary values
        annual_savings = float(row['annual_savings_dollars'].replace('$', '').replace(',', ''))
        monthly_savings = float(row['monthly_savings_dollars'].replace('$', '').replace(',', ''))
        five_year_savings = float(row['five_year_savings'].replace('$', '').replace(',', ''))
        energy_spend = float(row['estimated_annual_energy_spend'].replace('$', '').replace(',', ''))

        analysis_results.append({
            'company_profile': {
                'company_name': row['company_name'],
                'domain': row['domain'],
                'location': row['location'],
                'employee_count': int(row['employee_count']),
                'estimated_sqft': int(row['estimated_sqft']),
                'estimated_energy_spend': energy_spend,
                'annual_savings_dollars': annual_savings,
                'monthly_savings_dollars': monthly_savings,
                'five_year_savings': five_year_savings,
                'payback_months': int(row['payback_months']),
                'carbon_reduction_tons': float(row['carbon_reduction_tons']),
            },
            'composite_score': float(row['composite_score']),
            'priority_tier': row['priority_tier'],
            'scores': {
                'intent': int(row['intent_score']),
                'technical_fit': int(row['technical_fit_score']),
                'urgency': int(row['urgency_score']),
                'account_value': int(row['account_value_score']),
            },
            'savings_projection': {
                'annual_savings_dollars': annual_savings,
                'monthly_savings_dollars': monthly_savings,
                'five_year_savings': five_year_savings,
                'payback_months': int(row['payback_months']),
                'carbon_reduction_tons': float(row['carbon_reduction_tons']),
            },
            'persona_mapping': {
                'primary_persona': row['primary_persona'],
            }
        })

    print(f"✅ Loaded {len(analysis_results)} analyzed casinos\n")

    # Generate emails for all prospects
    results_with_emails = await batch_generate_emails(analysis_results)

    # Export to CSV with emails
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"casino_analysis_with_emails_{timestamp}.csv"
    export_with_emails(results_with_emails, csv_filename)

    # Also save full JSON
    json_filename = f"casino_analysis_with_emails_{timestamp}.json"
    with open(json_filename, 'w') as f:
        json.dump(results_with_emails, f, indent=2)
    print(f"✅ Exported full JSON to {json_filename}")

    # Send to Clay webhook
    webhook_success = await send_to_clay_webhook(results_with_emails)

    # Final summary
    print(f"\n{'='*70}")
    print("FINAL SUMMARY")
    print(f"{'='*70}")
    print(f"✅ Analyzed: {len(analysis_results)} casinos")
    print(f"✅ Emails Generated: {sum(r['num_emails_generated'] for r in results_with_emails)} total")
    print(f"✅ Clay Webhook: {'SUCCESS' if webhook_success else 'PARTIAL/FAILED'}")
    print(f"✅ CSV Export: {csv_filename}")
    print(f"✅ JSON Export: {json_filename}")

    print(f"\n{'='*70}")
    print("NEXT STEPS")
    print(f"{'='*70}")
    print("1. Check Clay for incoming prospect data with email sequences")
    print("2. Review generated emails in the CSV/JSON exports")
    print("3. Set up Clay workflows to schedule email sends")
    print("4. Monitor responses and update scores in real-time")
    print(f"\n🎰 Ready to launch outbound to {len(analysis_results)} casinos!")

if __name__ == "__main__":
    asyncio.run(main())

"""
Quick test of 4-persona email generation for 1 casino
"""

import asyncio
import anthropic
import os
from dotenv import load_dotenv
import pandas as pd

# Import from worldclass_email_generator
from worldclass_email_generator import (
    generate_cfo_sequence,
    generate_operations_sequence,
    generate_facilities_sequence,
    generate_esg_sequence
)

load_dotenv()

async def test_single_casino():
    """Test 4-persona generation for Foxwoods"""

    print("\n" + "="*70)
    print("TESTING 4-PERSONA EMAIL GENERATION - FOXWOODS")
    print("="*70 + "\n")

    # Load data
    df = pd.read_csv('casino_analysis_20251029_225746.csv')
    df['annual_savings_numeric'] = df['annual_savings_dollars'].str.replace('$', '').str.replace(',', '').astype(float)

    # Get Foxwoods (first A-tier casino)
    a_tier = df[df['priority_tier'] == 'A'].nlargest(1, 'annual_savings_numeric')
    row = a_tier.iloc[0]

    # Build prospect
    annual_savings = float(row['annual_savings_dollars'].replace('$', '').replace(',', ''))
    prospect = {
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
    }

    print(f"Casino: {prospect['company_profile']['company_name']}")
    print(f"Location: {prospect['company_profile']['location']}")
    print(f"Est. Savings: ${annual_savings:,.0f}/year")
    print(f"Tier: {prospect['priority_tier']}\n")

    client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

    num_emails = 5  # A-tier gets 5 emails

    # Generate all 4 sequences
    print("Generating 4 persona sequences...")
    print("  → CFO sequence...")
    cfo_emails = await generate_cfo_sequence(client, prospect, num_emails)
    print(f"     ✓ Generated {len(cfo_emails)} emails")

    print("  → Operations sequence...")
    ops_emails = await generate_operations_sequence(client, prospect, num_emails)
    print(f"     ✓ Generated {len(ops_emails)} emails")

    print("  → Facilities sequence...")
    facilities_emails = await generate_facilities_sequence(client, prospect, num_emails)
    print(f"     ✓ Generated {len(facilities_emails)} emails")

    print("  → ESG sequence...")
    esg_emails = await generate_esg_sequence(client, prospect, num_emails)
    print(f"     ✓ Generated {len(esg_emails)} emails")

    print("\n" + "="*70)
    print("RESULTS")
    print("="*70 + "\n")

    # Show Email 1 from each persona
    print("CFO Email 1:")
    print(f"  Subject: {cfo_emails[0]['subject']}")
    print(f"  Body: {cfo_emails[0]['body'][:150]}...")
    print(f"  CTA: {cfo_emails[0].get('cta', 'N/A')}\n")

    print("Operations Email 1:")
    print(f"  Subject: {ops_emails[0]['subject']}")
    print(f"  Body: {ops_emails[0]['body'][:150]}...")
    print(f"  CTA: {ops_emails[0].get('cta', 'N/A')}\n")

    print("Facilities Email 1:")
    print(f"  Subject: {facilities_emails[0]['subject']}")
    print(f"  Body: {facilities_emails[0]['body'][:150]}...")
    print(f"  CTA: {facilities_emails[0].get('cta', 'N/A')}\n")

    print("ESG Email 1:")
    print(f"  Subject: {esg_emails[0]['subject']}")
    print(f"  Body: {esg_emails[0]['body'][:150]}...")
    print(f"  CTA: {esg_emails[0].get('cta', 'N/A')}\n")

    print("="*70)
    print("✅ TEST COMPLETE - All 4 personas generated successfully!")
    print(f"   Total: {len(cfo_emails) + len(ops_emails) + len(facilities_emails) + len(esg_emails)} emails")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_single_casino())

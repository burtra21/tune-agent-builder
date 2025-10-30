"""
Test PDF generation with a single casino
"""
import pandas as pd
from pdf_lead_magnets.pdf_generator import generate_cost_analysis_pdf

# Load casino data
df = pd.read_csv('casino_analysis_20251029_225746.csv')

# Get first A-tier casino (Foxwoods)
casino = df[df['priority_tier'] == 'A'].iloc[0]

# Build prospect data structure
prospect_data = {
    'company_profile': {
        'company_name': casino['company_name'],
        'domain': casino['domain'],
        'location': casino['location'],
        'employee_count': int(casino['employee_count']),
        'estimated_sqft': int(casino['estimated_sqft']),
        'estimated_energy_spend': float(casino['estimated_annual_energy_spend'].replace('$', '').replace(',', '')),
        'annual_savings_dollars': float(casino['annual_savings_dollars'].replace('$', '').replace(',', '')),
        'monthly_savings_dollars': float(casino['monthly_savings_dollars'].replace('$', '').replace(',', '')),
        'five_year_savings': float(casino['five_year_savings'].replace('$', '').replace(',', '')),
        'payback_months': int(casino['payback_months']),
        'carbon_reduction_tons': float(casino['carbon_reduction_tons']),
    }
}

print(f"Generating PDF for {prospect_data['company_profile']['company_name']}...")
print(f"  Location: {prospect_data['company_profile']['location']}")
print(f"  Annual savings: ${prospect_data['company_profile']['annual_savings_dollars']:,.0f}")

filename = generate_cost_analysis_pdf(prospect_data)

print(f"\n✅ PDF generated successfully!")
print(f"   File: pdf_lead_magnets/generated/{filename}")
print(f"\n   You can open it with:")
print(f"   open 'pdf_lead_magnets/generated/{filename}'")

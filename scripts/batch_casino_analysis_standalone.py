"""
Standalone Batch Casino Analysis
Analyze hundreds of casinos using the agent directly (no API server needed)
"""

import asyncio
import json
import csv
from datetime import datetime
from typing import List, Dict
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

# Load casino agent
with open('agents/casino_agent.json', 'r') as f:
    CASINO_AGENT = json.load(f)

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# Sample list of major US casinos - expand this for your full list
CASINO_PROSPECTS = [
    # Las Vegas Strip
    {"company_name": "MGM Grand Las Vegas", "domain": "mgmgrand.com", "employee_count": 5000, "location": "Las Vegas, NV", "est_sqft": 1200000},
    {"company_name": "Caesars Palace", "domain": "caesars.com", "employee_count": 4500, "location": "Las Vegas, NV", "est_sqft": 1100000},
    {"company_name": "The Venetian", "domain": "venetian.com", "employee_count": 6000, "location": "Las Vegas, NV", "est_sqft": 1500000},
    {"company_name": "Bellagio", "domain": "bellagio.com", "employee_count": 4000, "location": "Las Vegas, NV", "est_sqft": 950000},
    {"company_name": "Wynn Las Vegas", "domain": "wynnlasvegas.com", "employee_count": 5500, "location": "Las Vegas, NV", "est_sqft": 1300000},

    # Add your casino list here - you can load from CSV:
    # import pandas as pd
    # df = pd.read_csv('your_casino_list.csv')
    # CASINO_PROSPECTS = df.to_dict('records')
]

def estimate_energy_metrics(prospect: Dict) -> Dict:
    """Estimate energy consumption based on casino size"""
    sqft = prospect.get('est_sqft', 1000000)
    employees = prospect.get('employee_count', 3000)

    # Casino energy profile from agent
    kwh_per_sqft = 200  # Average for large casinos
    annual_kwh = sqft * kwh_per_sqft

    # Nevada average: $0.10/kWh
    annual_energy_spend = annual_kwh * 0.10

    savings_pct = CASINO_AGENT['savings_benchmarks']['typical_percentage'] / 100
    annual_savings = annual_energy_spend * savings_pct

    return {
        "estimated_sqft": sqft,
        "estimated_annual_kwh": annual_kwh,
        "estimated_energy_spend": annual_energy_spend,
        "savings_percentage": CASINO_AGENT['savings_benchmarks']['typical_percentage'],
        "annual_savings_dollars": annual_savings,
        "monthly_savings_dollars": annual_savings / 12,
        "payback_months": CASINO_AGENT['savings_benchmarks']['payback_months'],
        "five_year_savings": annual_savings * 5,
        "carbon_reduction_tons": annual_kwh * savings_pct * 0.0007,  # EPA factor
    }

def score_prospect(prospect: Dict, energy_metrics: Dict) -> Dict:
    """Quick scoring without full AI research (for batch processing)"""

    # Size-based scoring
    sqft = energy_metrics['estimated_sqft']
    if sqft > 1000000:
        size_score = 100
    elif sqft > 500000:
        size_score = 75
    else:
        size_score = 50

    # Location-based (Vegas strip = high value)
    location = prospect.get('location', '')
    if 'Las Vegas' in location:
        location_score = 90
    elif any(city in location for city in ['Atlantic City', 'Macau', 'Singapore']):
        location_score = 80
    else:
        location_score = 60

    # Default scores (you can enhance with real web research)
    intent_score = 70  # Baseline
    technical_fit = 85  # Casinos are always good fit
    urgency = 65  # Moderate

    # Composite score
    composite = (
        intent_score * 0.35 +
        technical_fit * 0.25 +
        urgency * 0.15 +
        size_score * 0.15 +
        location_score * 0.10
    )

    # Priority tier
    if composite >= 75:
        tier = "A"
    elif composite >= 60:
        tier = "B"
    else:
        tier = "C"

    return {
        "intent": intent_score,
        "technical_fit": technical_fit,
        "urgency": urgency,
        "account_value": size_score,
        "location_quality": location_score,
        "composite": round(composite, 1)
    }, tier

def analyze_casino_fast(prospect: Dict) -> Dict:
    """Fast analysis without API calls - for bulk processing"""

    energy_metrics = estimate_energy_metrics(prospect)
    scores, tier = score_prospect(prospect, energy_metrics)

    # Determine primary persona based on size
    if energy_metrics['estimated_sqft'] > 1000000:
        primary_persona = "facilities_vp"
    elif energy_metrics['annual_savings_dollars'] > 500000:
        primary_persona = "energy_manager"
    else:
        primary_persona = "operations_director"

    return {
        "company_profile": {
            "company_name": prospect['company_name'],
            "domain": prospect.get('domain', ''),
            "location": prospect.get('location', ''),
            "employee_count": prospect.get('employee_count', 0),
            **energy_metrics
        },
        "scores": scores,
        "composite_score": scores['composite'],
        "priority_tier": tier,
        "savings_projection": energy_metrics,
        "persona_mapping": {
            "primary_persona": primary_persona,
            "recommended_personas": ["esg_director", "facilities_vp", "energy_manager"]
        },
        "recommended_messaging": f"Focus on ${energy_metrics['annual_savings_dollars']:,.0f} annual savings opportunity. Emphasize {tier}-tier priority for quick ROI.",
        "analyzed_at": datetime.now().isoformat()
    }

def batch_analyze_fast(prospects: List[Dict]) -> List[Dict]:
    """Analyze all prospects quickly"""
    results = []

    print(f"\n{'='*70}")
    print(f"FAST BATCH CASINO ANALYSIS")
    print(f"{'='*70}")
    print(f"Analyzing {len(prospects)} casinos...")
    print(f"Using agent: {CASINO_AGENT['name']}")
    print(f"Savings benchmark: {CASINO_AGENT['savings_benchmarks']['typical_percentage']}%\n")

    for i, prospect in enumerate(prospects, 1):
        result = analyze_casino_fast(prospect)
        results.append(result)

        print(f"  {i}. {prospect['company_name']}: "
              f"Score {result['composite_score']} | "
              f"Tier {result['priority_tier']} | "
              f"${result['savings_projection']['annual_savings_dollars']:,.0f}/year")

    return results

def export_to_csv(results: List[Dict], filename: str):
    """Export to Clay-ready CSV"""

    csv_data = []
    for r in results:
        csv_data.append({
            'company_name': r['company_profile']['company_name'],
            'domain': r['company_profile']['domain'],
            'location': r['company_profile']['location'],
            'employee_count': r['company_profile']['employee_count'],
            'composite_score': r['composite_score'],
            'priority_tier': r['priority_tier'],
            'intent_score': r['scores']['intent'],
            'technical_fit_score': r['scores']['technical_fit'],
            'urgency_score': r['scores']['urgency'],
            'account_value_score': r['scores']['account_value'],
            'estimated_sqft': r['company_profile']['estimated_sqft'],
            'estimated_annual_energy_spend': f"${r['company_profile']['estimated_energy_spend']:,.0f}",
            'annual_savings_dollars': f"${r['savings_projection']['annual_savings_dollars']:,.0f}",
            'monthly_savings_dollars': f"${r['savings_projection']['monthly_savings_dollars']:,.0f}",
            'payback_months': r['savings_projection']['payback_months'],
            'five_year_savings': f"${r['savings_projection']['five_year_savings']:,.0f}",
            'carbon_reduction_tons': round(r['savings_projection']['carbon_reduction_tons'], 1),
            'primary_persona': r['persona_mapping']['primary_persona'],
            'recommended_messaging': r['recommended_messaging'],
            'analyzed_at': r['analyzed_at']
        })

    with open(filename, 'w', newline='') as f:
        if csv_data:
            writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
            writer.writeheader()
            writer.writerows(csv_data)

    print(f"\n✅ Exported {len(csv_data)} results to {filename}")

def print_summary(results: List[Dict]):
    """Print analysis summary"""

    a_tier = [r for r in results if r['priority_tier'] == 'A']
    b_tier = [r for r in results if r['priority_tier'] == 'B']
    c_tier = [r for r in results if r['priority_tier'] == 'C']

    total_savings = sum(r['savings_projection']['annual_savings_dollars'] for r in results)
    avg_score = sum(r['composite_score'] for r in results) / len(results)

    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total Analyzed: {len(results)}")
    print(f"\nPriority Distribution:")
    print(f"  A-Tier (75+): {len(a_tier)} casinos → Generate full 5-touch sequences")
    print(f"  B-Tier (60-74): {len(b_tier)} casinos → Standard 3-touch sequences")
    print(f"  C-Tier (<60): {len(c_tier)} casinos → Light touch or nurture")

    print(f"\nFinancial Opportunity:")
    print(f"  Total Annual Savings: ${total_savings:,.0f}")
    print(f"  Average per Casino: ${total_savings/len(results):,.0f}")
    print(f"  5-Year Pipeline Value: ${total_savings * 5:,.0f}")

    print(f"\nTop 5 Opportunities:")
    top_5 = sorted(results, key=lambda x: x['savings_projection']['annual_savings_dollars'], reverse=True)[:5]
    for i, r in enumerate(top_5, 1):
        print(f"  {i}. {r['company_profile']['company_name']}: ${r['savings_projection']['annual_savings_dollars']:,.0f}/year")

def main():
    """Main function"""

    # Load from the auto-generated casino list
    import pandas as pd
    prospects = pd.read_csv('casino_prospect_list.csv').to_dict('records')

    print(f"Loaded {len(prospects)} casinos from casino_prospect_list.csv")

    # Analyze
    results = batch_analyze_fast(prospects)

    # Export
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_to_csv(results, f"casino_analysis_{timestamp}.csv")

    with open(f"casino_analysis_{timestamp}.json", 'w') as f:
        json.dump(results, f, indent=2)

    # Summary
    print_summary(results)

    print(f"\n{'='*70}")
    print("NEXT STEPS FOR HUNDREDS OF CASINOS")
    print(f"{'='*70}")
    print("1. Add your casino list to CASINO_PROSPECTS (or load from CSV)")
    print("2. Run this script: python3 batch_casino_analysis_standalone.py")
    print("3. Import the CSV to Clay for enrichment")
    print("4. Generate personalized emails for A-tier prospects")
    print("5. Set up automated outreach via n8n")
    print("\nFor FULL AI research on each casino (slower but higher quality):")
    print("  - Use the API server version with concurrency limits")
    print("  - Expect ~30 seconds per casino with deep research")
    print("  - 100 casinos = ~50 minutes with concurrency=3")

if __name__ == "__main__":
    main()

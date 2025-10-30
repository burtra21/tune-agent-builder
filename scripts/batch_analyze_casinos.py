"""
Batch Casino Analysis
Analyze hundreds of casino prospects and export results
"""

import asyncio
import json
import csv
from datetime import datetime
import httpx
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://localhost:8000"
API_KEY = "tune_dev_key_12345"

# Sample casino list - you can expand this or load from CSV
CASINO_PROSPECTS = [
    {"company_name": "MGM Grand Las Vegas", "domain": "mgmgrand.com", "employee_count": 5000, "location": "Las Vegas, NV"},
    {"company_name": "Caesars Palace", "domain": "caesars.com", "employee_count": 4500, "location": "Las Vegas, NV"},
    {"company_name": "The Venetian Resort", "domain": "venetian.com", "employee_count": 6000, "location": "Las Vegas, NV"},
    {"company_name": "Bellagio", "domain": "bellagio.com", "employee_count": 4000, "location": "Las Vegas, NV"},
    {"company_name": "Wynn Las Vegas", "domain": "wynnlasvegas.com", "employee_count": 5500, "location": "Las Vegas, NV"},
    {"company_name": "Aria Resort", "domain": "aria.com", "employee_count": 4200, "location": "Las Vegas, NV"},
    {"company_name": "Cosmopolitan", "domain": "cosmopolitanlasvegas.com", "employee_count": 3800, "location": "Las Vegas, NV"},
    {"company_name": "Mandalay Bay", "domain": "mandalaybay.com", "employee_count": 4500, "location": "Las Vegas, NV"},
    {"company_name": "Luxor", "domain": "luxor.com", "employee_count": 3000, "location": "Las Vegas, NV"},
    {"company_name": "Paris Las Vegas", "domain": "caesars.com/paris-las-vegas", "employee_count": 3200, "location": "Las Vegas, NV"},
]

async def analyze_casino(client: httpx.AsyncClient, prospect: Dict) -> Dict:
    """Analyze a single casino prospect"""
    try:
        response = await client.post(
            f"{API_URL}/api/prospects/analyze",
            params={"industry": "casino"},
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json=prospect,
            timeout=120.0
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ {prospect['company_name']}: Score {result['composite_score']:.1f} | Tier {result['priority_tier']} | ${result['savings_projection']['annual_savings_dollars']:,.0f}/year")
            return result
        else:
            print(f"❌ {prospect['company_name']}: Error {response.status_code}")
            return {"error": response.text, "prospect": prospect}

    except Exception as e:
        print(f"❌ {prospect['company_name']}: {str(e)}")
        return {"error": str(e), "prospect": prospect}

async def batch_analyze(prospects: List[Dict], concurrency: int = 3):
    """Analyze multiple casinos with rate limiting"""

    print(f"\n{'='*70}")
    print(f"BATCH CASINO ANALYSIS")
    print(f"{'='*70}")
    print(f"Total Prospects: {len(prospects)}")
    print(f"Concurrency: {concurrency} simultaneous requests")
    print(f"Estimated Time: {len(prospects) / concurrency * 30} seconds\n")

    results = []

    async with httpx.AsyncClient() as client:
        # Process in batches to avoid overwhelming the API
        for i in range(0, len(prospects), concurrency):
            batch = prospects[i:i+concurrency]
            print(f"\nProcessing batch {i//concurrency + 1} ({len(batch)} prospects)...")

            # Analyze batch concurrently
            batch_results = await asyncio.gather(
                *[analyze_casino(client, prospect) for prospect in batch],
                return_exceptions=True
            )

            results.extend(batch_results)

            # Small delay between batches
            if i + concurrency < len(prospects):
                await asyncio.sleep(2)

    return results

def export_to_csv(results: List[Dict], filename: str):
    """Export results to CSV for Clay import"""

    csv_data = []
    for result in results:
        if 'error' not in result:
            csv_data.append({
                'company_name': result['company_profile']['company_name'],
                'domain': result['company_profile']['domain'],
                'composite_score': result['composite_score'],
                'priority_tier': result['priority_tier'],
                'intent_score': result['scores']['intent'],
                'technical_fit_score': result['scores']['technical_fit'],
                'urgency_score': result['scores']['urgency'],
                'annual_savings_dollars': result['savings_projection']['annual_savings_dollars'],
                'monthly_savings_dollars': result['savings_projection']['monthly_savings_dollars'],
                'payback_months': result['savings_projection']['payback_period_months'],
                'roi_percentage': result['savings_projection']['roi_percentage'],
                'carbon_reduction_tons': result['savings_projection']['carbon_reduction_tons'],
                'primary_persona': result['persona_mapping']['primary_persona'],
                'buying_committee_size': result['persona_mapping']['buying_committee_size'],
                'intent_signals_found': len(result['intent_signals'].get('sustainability_commitments', [])) +
                                       len(result['intent_signals'].get('expansion_signals', [])) +
                                       len(result['intent_signals'].get('hiring_signals', [])),
                'recommended_messaging': result['recommended_messaging'],
                'analyzed_at': result['analyzed_at']
            })

    if csv_data:
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
            writer.writeheader()
            writer.writerows(csv_data)

        print(f"\n✅ Exported {len(csv_data)} results to {filename}")
    else:
        print("\n❌ No successful results to export")

def export_to_json(results: List[Dict], filename: str):
    """Export full results to JSON"""
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"✅ Exported full results to {filename}")

def print_summary(results: List[Dict]):
    """Print analysis summary"""

    successful = [r for r in results if 'error' not in r]

    if not successful:
        print("\n❌ No successful analyses")
        return

    a_tier = [r for r in successful if r['priority_tier'] == 'A']
    b_tier = [r for r in successful if r['priority_tier'] == 'B']
    c_tier = [r for r in successful if r['priority_tier'] == 'C']

    total_savings = sum(r['savings_projection']['annual_savings_dollars'] for r in successful)
    avg_score = sum(r['composite_score'] for r in successful) / len(successful)

    print(f"\n{'='*70}")
    print("BATCH ANALYSIS SUMMARY")
    print(f"{'='*70}")
    print(f"Total Analyzed: {len(successful)}")
    print(f"Failed: {len(results) - len(successful)}")
    print(f"\nPriority Distribution:")
    print(f"  A-Tier (75+): {len(a_tier)} prospects ({len(a_tier)/len(successful)*100:.1f}%)")
    print(f"  B-Tier (60-74): {len(b_tier)} prospects ({len(b_tier)/len(successful)*100:.1f}%)")
    print(f"  C-Tier (<60): {len(c_tier)} prospects ({len(c_tier)/len(successful)*100:.1f}%)")
    print(f"\nAverage Composite Score: {avg_score:.1f}/100")
    print(f"Total Annual Savings Opportunity: ${total_savings:,.0f}")
    print(f"Average Savings per Casino: ${total_savings/len(successful):,.0f}")

    print(f"\nTop 5 Prospects by Score:")
    top_5 = sorted(successful, key=lambda x: x['composite_score'], reverse=True)[:5]
    for i, prospect in enumerate(top_5, 1):
        print(f"  {i}. {prospect['company_profile']['company_name']}: {prospect['composite_score']:.1f} | ${prospect['savings_projection']['annual_savings_dollars']:,.0f}/year")

async def main():
    """Main batch processing function"""

    # You can load a larger list from CSV:
    # import pandas as pd
    # prospects = pd.read_csv('casino_list.csv').to_dict('records')

    prospects = CASINO_PROSPECTS

    # Analyze all prospects
    results = await batch_analyze(prospects, concurrency=3)

    # Export results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_to_csv(results, f"casino_analysis_{timestamp}.csv")
    export_to_json(results, f"casino_analysis_{timestamp}.json")

    # Print summary
    print_summary(results)

    print(f"\n{'='*70}")
    print("NEXT STEPS")
    print(f"{'='*70}")
    print("1. Import CSV to Clay for enrichment")
    print("2. Generate personalized emails for A-tier prospects")
    print("3. Set up n8n workflow for automated outreach")
    print("4. Track responses and iterate")

if __name__ == "__main__":
    print("🎰 Starting Batch Casino Analysis...")
    print("Make sure API server is running: uvicorn api_server:app --reload --port 8000\n")
    asyncio.run(main())

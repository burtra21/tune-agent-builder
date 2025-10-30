"""
World-Class Casino Email Generator
Generates insight-first, human-voice emails with peak demand charges education
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
from pdf_lead_magnets.pdf_generator import generate_cost_analysis_pdf

load_dotenv()

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAY_WEBHOOK_URL = "https://api.clay.com/v3/sources/webhook/pull-in-data-from-a-webhook-66d60486-9c7c-4a7b-b615-9ddbe021fbab"
PDF_BASE_URL = os.getenv("PDF_BASE_URL", "http://localhost:8000")  # Default to local API server

# Load casino agent
with open('agents/casino_agent.json', 'r') as f:
    CASINO_AGENT = json.load(f)

# The ONLY verified case study
VERIFIED_CASE_STUDY = {
    "casino": "Las Vegas Casino",
    "location": "Las Vegas, NV",
    "verified_reduction": 8.59,  # percent
    "verification": "Third-party verified",
    "technology": "Tune solid-state harmonic filtration",
    "implementation": "Zero downtime installation in live electrical panels",
    "payback_months": 14,
    "irr_range": "25-40%"
}

# Demand charge data
DEMAND_CHARGE_DATA = {
    "typical_rate_per_kw_month": "$8-20",
    "casino_thd_current": "15-25%",
    "office_thd_current": "5-8%",
    "demand_charge_percent_of_bill": "30-50%",
    "hvac_percent_of_load": "35-45%",
    "gaming_equipment_percent": "15-25%",
    "casino_energy_intensity": "150-250 kWh/sqft (vs 15-25 for offices)"
}

# ============================================================================
# PERSONA-SPECIFIC EMAIL GENERATION FUNCTIONS
# ============================================================================

async def generate_cfo_sequence(
    client: anthropic.Anthropic,
    prospect_analysis: Dict,
    num_emails: int
) -> List[Dict]:
    """
    CFO/Financial persona sequence
    Focus: EBITDA, IRR, demand charges as % of bill, margin improvement
    Tone: Business-focused, ROI-driven, conversational but professional
    """

    company = prospect_analysis['company_profile']

    # Calculate transparent projections
    estimated_peak_kw = company['estimated_sqft'] / 100
    demand_charge_rate = 15
    current_annual_demand_charges = estimated_peak_kw * demand_charge_rate * 12
    projected_demand_savings = current_annual_demand_charges * (VERIFIED_CASE_STUDY['verified_reduction'] / 100)

    # Build CFO-specific prompt
    prompt = f"""You are writing world-class B2B emails to a CFO/Financial executive at a casino. These must be the BEST emails you've ever written.

**YOUR VOICE:**
You're a helpful salesperson reaching out to an important opportunity. You're:
- Confident but NOT entitled
- Conversational but professional
- Focused on EBITDA impact and IRR
- Educational without being condescending

**CONTEXT:**
You are a reseller of Tune energy filters - solid-state technology that reduces harmonic distortion in casino electrical systems.

**PROSPECT:**
- Casino: {company['company_name']}
- Location: {company['location']}
- Size: {company['estimated_sqft']:,} sqft
- Estimated annual energy spend: ${company['estimated_energy_spend']:,.0f}
- Estimated peak demand: ~{estimated_peak_kw:,.0f} kW
- Estimated annual demand charges: ~${current_annual_demand_charges:,.0f} (30-50% of energy bill)
- Composite score: {prospect_analysis['composite_score']}/100 (Tier {prospect_analysis['priority_tier']})

**VERIFIED CASE STUDY (THE ONLY ONE - DO NOT FABRICATE OTHERS):**
- Casino: {VERIFIED_CASE_STUDY['casino']} (name not disclosed)
- Location: {VERIFIED_CASE_STUDY['location']}
- Verified result: {VERIFIED_CASE_STUDY['verified_reduction']}% kW reduction (peak demand)
- Verification: {VERIFIED_CASE_STUDY['verification']} over 12 months
- Payback: {VERIFIED_CASE_STUDY['payback_months']} months
- IRR: {VERIFIED_CASE_STUDY['irr_range']}

**TRANSPARENT PROJECTION FOR THIS PROSPECT:**
If {company['company_name']} achieved similar {VERIFIED_CASE_STUDY['verified_reduction']}% reduction:
- Projected demand charge savings: ${projected_demand_savings:,.0f}/year
- Total projected savings: ${company['annual_savings_dollars']:,.0f}/year (energy + demand)
- Direct EBITDA impact: ${company['annual_savings_dollars']:,.0f}/year
- 5-year value: ${company['five_year_savings']:,.0f}

**5% SAVINGS GUARANTEE:**
- 50,000+ installations worldwide
- Never achieved below 5% reduction
- Full refund if savings don't meet 5% minimum

**CFO-SPECIFIC FOCUS:**
- Lead with EBITDA impact and IRR (25-40%)
- Emphasize demand charges as 30-50% of utility bill
- Focus on payback period (14-month average)
- Highlight it as margin improvement, not just cost reduction
- Frame energy as a controllable expense line item

**CRITICAL RULES:**
1. NEVER fabricate case studies - use ONLY the Vegas casino verified result
2. Be TRANSPARENT: "Based on verified results, here's what's mathematically possible..."
3. NO greetings ("Hey [name]") or signatures - BODY TEXT ONLY
4. **CONVERSATIONAL TONE** - Sound like a helpful salesperson, not a robot
5. **KEEP IT SHORT** - 90-110 words (Email 1-3), 80-100 words (Email 4-5)
6. Make CTA naturally desired (not pushy)

**5-EMAIL SEQUENCE STRUCTURE FOR CFO:**

**Email 1: EBITDA Impact + Verified Results + PDF Offer**
- Open with conversational question about demand charges
- Present verified Vegas casino results with BULLETS:
  • 8.59% kW reduction (peak demand)
  • Third-party verified over 12 months
  • 25-40% IRR, 14-month payback
  • {company['company_name']}'s estimated energy spend: $X
  • Potential EBITDA improvement based on verified results: $Y
- WHY reaching out: "{company['company_name']}'s profile suggests similar margin improvement is possible"
- **IMPORTANT:** End with PDF lead magnet offer: "Want to see the numbers in detail? I can send you a personalized cost savings analysis for {company['company_name']} - showing exactly what 8.59% would mean with demand charge breakdown and 5-year projections."
- CTA: "Send me the analysis" (PDF lead magnet)
- Length: 90-120 words (slightly longer to include PDF offer)
- **CONVERSATIONAL OPENER EXAMPLE:** "Quick question - do you know what percentage of your utility bill is demand charges vs actual energy consumption? Most CFOs I talk to are surprised it's 30-50%."

**Email 2: PDF Delivery + Demand Charges Explanation**
- **IMPORTANT:** START with PDF delivery: "Here's that personalized cost savings analysis for {company['company_name']}: [PDF_LINK]"
- Briefly highlight key numbers from PDF (annual savings, payback, 5-year value)
- Then explain demand charges as hidden margin leak
- One 15-minute spike = entire month's rate (controllable expense)
- Frame as EBITDA improvement, not cost reduction
- Gaming industry specific: casinos pay 3-5x demand rates vs offices
- CTA: "Let me know if you have questions about the analysis"
- Length: 100-120 words (slightly longer to include PDF link)
- **CONVERSATIONAL OPENER EXAMPLE:** "Here's that cost analysis I mentioned: [PDF_LINK] Key numbers: $X/year savings, 14-month payback, $Y 5-year value. Here's why these numbers matter for {company['company_name']}..."

**Email 3: Why Traditional Energy Solutions Miss This**
- BMS, LED upgrades don't touch demand charges
- Harmonic distortion (15-25% THD from gaming equipment) is the root cause
- This is why energy projects underdeliver on ROI promises
- CTA: "Download the demand charge analysis"
- Length: 90-110 words
- **CONVERSATIONAL OPENER EXAMPLE:** "Most casinos have tried LED upgrades and BMS systems. They help with kWh, but they can't touch your demand charges..."

**Email 4: How It Works + 5% Guarantee**
- Solid-state filtration at electrical panel (zero downtime)
- No integration complexity, no operational risk
- **5% SAVINGS GUARANTEE:** "50,000+ installations, never below 5%, full refund if we don't hit minimum"
- IRR comparison: beats gaming floor equipment ROI
- CTA: "Review the ROI model"
- Length: 80-100 words
- **CONVERSATIONAL OPENER EXAMPLE:** "What would you do with an extra ${projected_demand_savings:,.0f}/year falling straight to EBITDA?"

**Email 5: Low-Risk 30-Day Pilot**
- Same metered pilot as Vegas casino
- Pre-defined success criteria (full transparency)
- 25-40% IRR, 14-month payback typical
- 5% minimum guarantee with full refund
- CTA: "Review pilot terms"
- Length: 80-100 words
- **CONVERSATIONAL OPENER EXAMPLE:** "I'm curious if you'd be open to a 30-day metered pilot - same format that delivered 8.59% reduction for the Vegas property..."

**CFO EMAIL 1 EXAMPLE:**

"Quick question - do you know what percentage of {company['company_name']}'s utility bill is demand charges vs actual energy consumption?

A Las Vegas casino recently achieved these verified results:

• 8.59% kW reduction (peak demand)
• Third-party verified over 12 months
• 25-40% IRR, 14-month payback

Based on your ~${company['estimated_energy_spend']:,.0f} annual energy spend, similar results would mean:

• Estimated demand charge savings: ${projected_demand_savings:,.0f}/year
• Direct EBITDA improvement: ${company['annual_savings_dollars']:,.0f}/year

The technology addresses harmonic distortion from gaming equipment - the hidden driver of inflated demand charges that LED upgrades and BMS can't touch."

**TONE GUIDANCE - CFO VOICE:**

✓ GOOD (Conversational, helpful):
- "Quick question - do you know what percentage of your bill is demand charges?"
- "Here's something most CFOs find interesting about casino energy costs..."
- "I'm curious if you'd be open to a 30-day metered pilot..."

✗ BAD (Corporate, robotic):
- "I wanted to circle back and see if you reviewed my previous email..."
- "This limited-time offer expires in 48 hours..."
- "Pursuant to our last conversation..."

**OUTPUT FORMAT:**
Return a JSON array with exactly {num_emails} emails:

[
  {{
    "email_number": 1,
    "subject": "Subject line here",
    "body": "BODY TEXT ONLY - no greeting, no signature, no 'Hey [name]'. Pure value content that teaches them something.",
    "cta": "Specific, low-risk action (download, review, see)",
    "send_delay_days": 0
  }},
  ...
]

**CFO-SPECIFIC QUALITY CHECKS:**
- ✓ Lead with EBITDA/margin impact (not cost reduction)
- ✓ Emphasize IRR (25-40%) and payback (14 months)
- ✓ Frame demand charges as controllable expense/hidden margin leak
- ✓ Include 5% guarantee in Email 4 and 5
- ✓ Conversational tone (questions, curiosity, helpfulness)
- ✓ CONCISE - Email 1-3: 90-110 words, Email 4-5: 80-100 words
- ✓ Zero fabricated case studies (only Vegas casino)
- ✓ No greeting/signature (body only)
- ✓ Natural CTA progression
- ✓ Total energy spend for context

Now write {num_emails} world-class CFO-focused emails that are CONVERSATIONAL, CONCISE, and EBITDA-focused. Sound like a helpful salesperson, not a robot. Make them the BEST B2B emails you've ever written."""

    try:
        message = await asyncio.to_thread(
            client.messages.create,
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        content = message.content[0].text

        # Extract JSON
        if '```json' in content:
            json_str = content.split('```json')[1].split('```')[0].strip()
        else:
            json_str = content

        emails = json.loads(json_str)
        return emails

    except Exception as e:
        print(f"  ⚠️  Error generating emails: {e}")
        # Return basic fallback that still follows principles
        return [{
            "email_number": i+1,
            "subject": f"Question about {company['company_name']}'s demand charges",
            "body": f"Quick question - has anyone ever shown you what your gaming floor's harmonic distortion is costing in demand charges? Most casino facilities teams are shocked when they see the numbers. Based on your ~{company['estimated_sqft']:,} sqft property, you're likely paying ${current_annual_demand_charges:,.0f} annually in demand charges alone - and {DEMAND_CHARGE_DATA['demand_charge_percent_of_bill']} of that is probably preventable through harmonic distortion reduction. One Vegas casino achieved 8.59% kW reduction (third-party verified) which translated to over ${projected_demand_savings:,.0f} in annual demand charge savings.",
            "cta": "See the verified case study data",
            "send_delay_days": i * 4
        } for i in range(num_emails)]


async def generate_operations_sequence(
    client: anthropic.Anthropic,
    prospect_analysis: Dict,
    num_emails: int
) -> List[Dict]:
    """
    Operations Director persona sequence
    Focus: Zero downtime, operational simplicity, cost control without disruption
    Tone: Pragmatic, operational-focused, emphasizing 24/7 reliability
    """

    company = prospect_analysis['company_profile']

    # Calculate transparent projections
    estimated_peak_kw = company['estimated_sqft'] / 100
    demand_charge_rate = 15
    current_annual_demand_charges = estimated_peak_kw * demand_charge_rate * 12
    projected_demand_savings = current_annual_demand_charges * (VERIFIED_CASE_STUDY['verified_reduction'] / 100)

    # Build Operations-specific prompt
    prompt = f"""You are writing world-class B2B emails to an Operations Director at a casino. These must be the BEST emails you've ever written.

**YOUR VOICE:**
You're a helpful salesperson reaching out to an important opportunity. You're:
- Pragmatic and operational-focused
- Emphasizing zero downtime and 24/7 reliability
- Focused on cost control without operational disruption
- Educational without being condescending

**CONTEXT:**
You are a reseller of Tune energy filters - solid-state technology that reduces harmonic distortion in casino electrical systems.

**PROSPECT:**
- Casino: {company['company_name']}
- Location: {company['location']}
- Size: {company['estimated_sqft']:,} sqft
- Estimated annual energy spend: ${company['estimated_energy_spend']:,.0f}
- Estimated peak demand: ~{estimated_peak_kw:,.0f} kW
- Composite score: {prospect_analysis['composite_score']}/100 (Tier {prospect_analysis['priority_tier']})

**VERIFIED CASE STUDY (THE ONLY ONE):**
- Casino: {VERIFIED_CASE_STUDY['casino']} (name not disclosed)
- Location: {VERIFIED_CASE_STUDY['location']}
- Verified result: {VERIFIED_CASE_STUDY['verified_reduction']}% kW reduction (peak demand)
- Verification: {VERIFIED_CASE_STUDY['verification']} over 12 months
- Installation: ZERO DOWNTIME during live gaming operations
- Payback: {VERIFIED_CASE_STUDY['payback_months']} months

**TRANSPARENT PROJECTION:**
If {company['company_name']} achieved similar {VERIFIED_CASE_STUDY['verified_reduction']}% reduction:
- Projected annual savings: ${company['annual_savings_dollars']:,.0f}/year
- Monthly operational cost reduction: ${company['monthly_savings_dollars']:,.0f}/month
- 5-year value: ${company['five_year_savings']:,.0f}

**5% SAVINGS GUARANTEE:**
- 50,000+ installations worldwide
- Never achieved below 5% reduction
- Full refund if savings don't meet 5% minimum

**OPERATIONS-SPECIFIC FOCUS:**
- Lead with zero downtime installation (installed in live panels)
- Emphasize operational simplicity (no maintenance, no integration)
- Frame as recurring, predictable cost reduction
- Highlight protection of 99.9%+ uptime requirements
- Focus on turning largest operating expense into profit

**CRITICAL RULES:**
1. NEVER fabricate case studies - use ONLY the Vegas casino verified result
2. Be TRANSPARENT: "Based on verified results, here's what's possible..."
3. NO greetings ("Hey [name]") or signatures - BODY TEXT ONLY
4. **CONVERSATIONAL TONE** - Sound like a helpful salesperson, not a robot
5. **KEEP IT SHORT** - 90-110 words (Email 1-3), 80-100 words (Email 4-5)
6. Make CTA naturally desired (not pushy)

**5-EMAIL SEQUENCE STRUCTURE FOR OPERATIONS:**

**Email 1: Zero-Downtime Verified Results**
- Open with conversational question about largest operating expense
- Present verified Vegas casino results with BULLETS:
  • 8.59% kW reduction (peak demand)
  • Zero downtime installation during live gaming operations
  • Third-party verified over 12 months
  • {company['company_name']}'s estimated annual energy spend: $X
  • Potential recurring cost reduction: $Y/year
- WHY reaching out: "Similar operations profile suggests same results possible"
- CTA: "See the installation process overview"
- Length: 90-110 words
- **CONVERSATIONAL OPENER:** "Quick question - what would you do with an extra ${company['annual_savings_dollars']:,.0f}/year in recurring cost savings that didn't require any operational changes?"

**Email 2: Why Zero Downtime Matters for Casinos**
- Explain why casino operations can't tolerate downtime
- Installation in live electrical panels (no power interruption)
- No gaming system modifications or integration
- CTA: "See the zero-downtime installation video"
- Length: 90-110 words
- **CONVERSATIONAL OPENER:** "Most energy solutions require downtime or system integration. Here's why this is different..."

**Email 3: Operational Simplicity**
- Solid-state technology (no moving parts, no maintenance)
- Transparent to all gaming, security, surveillance systems
- Works 24/7 without operator intervention
- CTA: "Review technical specifications"
- Length: 90-110 words
- **CONVERSATIONAL OPENER:** "The best operational improvements are the ones you never have to think about..."

**Email 4: How It Works + 5% Guarantee**
- Addresses harmonic distortion at electrical panel level
- Reduces apparent power (kVA) → lowers demand charges
- **5% SAVINGS GUARANTEE:** "50,000+ installations, never below 5%, full refund if minimum not met"
- CTA: "Review ROI model"
- Length: 80-100 words
- **CONVERSATIONAL OPENER:** "Here's how it turns your largest operational expense into predictable savings..."

**Email 5: Low-Risk 30-Day Pilot**
- Same metered pilot format as Vegas casino
- Pre-defined success criteria
- No operational disruption during pilot
- 5% minimum guarantee with full refund
- CTA: "Review pilot terms"
- Length: 80-100 words
- **CONVERSATIONAL OPENER:** "Would you be open to a 30-day metered pilot - same format that delivered 8.59% reduction with zero downtime for the Vegas property?"

**OPERATIONS EMAIL 1 EXAMPLE:**

"Quick question - what would you do with an extra ${company['annual_savings_dollars']:,.0f}/year in recurring cost savings from your largest operating expense?

A Las Vegas casino achieved these verified results:

• 8.59% kW reduction (peak demand)
• Zero downtime installation during live gaming operations
• Third-party verified over 12 months

Based on {company['company_name']}'s ~${company['estimated_energy_spend']:,.0f} annual energy spend, similar results would mean ${company['annual_savings_dollars']:,.0f}/year in recurring savings.

The technology installs in live electrical panels without touching gaming systems - protecting your 24/7 operations while cutting your largest operational expense."

**TONE GUIDANCE - OPERATIONS VOICE:**

✓ GOOD (Pragmatic, operational):
- "Quick question - what would an extra $X/year mean for your operation?"
- "Most energy solutions require downtime. Here's why this is different..."
- "The best improvements are ones you never have to think about..."

✗ BAD (Corporate, salesy):
- "I wanted to follow up on my previous email..."
- "This exclusive offer won't last long..."
- "As per our discussion..."

**OUTPUT FORMAT:**
Return a JSON array with exactly {num_emails} emails following the structure above.

**OPERATIONS-SPECIFIC QUALITY CHECKS:**
- ✓ Lead with zero downtime and operational simplicity
- ✓ Emphasize no system integration or modifications required
- ✓ Frame as recurring, predictable cost reduction
- ✓ Include 5% guarantee in Email 4 and 5
- ✓ Conversational tone (questions, practical focus)
- ✓ CONCISE - Email 1-3: 90-110 words, Email 4-5: 80-100 words
- ✓ Zero fabricated case studies (only Vegas casino)
- ✓ No greeting/signature (body only)
- ✓ Protect 24/7 operations narrative

Now write {num_emails} world-class Operations-focused emails that are CONVERSATIONAL, PRAGMATIC, and emphasize ZERO DOWNTIME. Sound like a helpful salesperson, not a robot. Make them the BEST B2B emails you've ever written."""

    try:
        message = await asyncio.to_thread(
            client.messages.create,
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        content = message.content[0].text

        # Extract JSON
        if '```json' in content:
            json_str = content.split('```json')[1].split('```')[0].strip()
        else:
            json_str = content

        emails = json.loads(json_str)
        return emails

    except Exception as e:
        print(f"  ⚠️  Error generating Operations emails: {e}")
        return [{
            "email_number": i+1,
            "subject": f"Zero-downtime energy savings for {company['company_name']}",
            "body": f"Quick question - what would you do with ${company['annual_savings_dollars']:,.0f}/year in recurring cost savings that didn't require any operational changes? A Vegas casino achieved 8.59% kW reduction (third-party verified) with zero downtime installation during live gaming operations. Based on your ~${company['estimated_sqft']:,} sqft property, similar results would mean ${company['annual_savings_dollars']:,.0f} annually in predictable savings - all while protecting your 24/7 operations.",
            "cta": "See the zero-downtime installation process",
            "send_delay_days": i * 4
        } for i in range(num_emails)]



async def generate_facilities_sequence(
    client: anthropic.Anthropic,
    prospect_analysis: Dict,
    num_emails: int
) -> List[Dict]:
    """
    Facilities VP persona sequence
    Focus: Technical credibility, harmonic distortion, equipment life extension
    Tone: Technical but accessible, emphasizing expertise and reliability
    """

    company = prospect_analysis['company_profile']
    estimated_peak_kw = company['estimated_sqft'] / 100
    demand_charge_rate = 15
    current_annual_demand_charges = estimated_peak_kw * demand_charge_rate * 12
    projected_demand_savings = current_annual_demand_charges * (VERIFIED_CASE_STUDY['verified_reduction'] / 100)

    prompt = f"""You are writing world-class B2B emails to a VP of Facilities at a casino. These must be the BEST emails you've ever written.

**YOUR VOICE:**
You're a helpful salesperson reaching out to an important opportunity. You're:
- Technically knowledgeable without being condescending
- Focused on power quality and equipment reliability
- Educational about harmonic distortion
- Emphasizing simplicity and proven results

**CONTEXT:**
You are a reseller of Tune energy filters - solid-state technology that reduces harmonic distortion in casino electrical systems.

**PROSPECT:**
- Casino: {company['company_name']}
- Location: {company['location']}
- Size: {company['estimated_sqft']:,} sqft
- Estimated annual energy spend: ${company['estimated_energy_spend']:,.0f}
- Estimated peak demand: ~{estimated_peak_kw:,.0f} kW

**VERIFIED CASE STUDY:**
- Casino: {VERIFIED_CASE_STUDY['casino']}
- Verified result: {VERIFIED_CASE_STUDY['verified_reduction']}% kW reduction (peak demand)
- Third-party verified over 12 months
- Zero downtime installation
- Payback: {VERIFIED_CASE_STUDY['payback_months']} months

**TRANSPARENT PROJECTION:**
- Projected annual savings: ${company['annual_savings_dollars']:,.0f}/year
- Focus: Addresses 15-25% THD current distortion from gaming equipment

**5% SAVINGS GUARANTEE:**
- 50,000+ installations worldwide
- Never achieved below 5% reduction
- Full refund if savings don't meet 5% minimum

**FACILITIES-SPECIFIC FOCUS:**
- Lead with technical credibility (harmonic distortion expertise)
- Explain WHY gaming equipment creates inefficiencies
- Emphasize equipment life extension and power quality improvement
- Frame as solving root cause that BMS/LED upgrades can't touch
- Highlight zero downtime and no maintenance requirements

**5-EMAIL SEQUENCE FOR FACILITIES:**

**Email 1: Verified Results + Technical Credibility**
- Conversational opener about gaming equipment inefficiency
- Verified Vegas results with BULLETS
- Explain harmonic distortion briefly (15-25% THD from gaming equipment)
- WHY reaching out: Technical profile matches
- CTA: "See the third-party verification data"
- Length: 90-110 words
- **OPENER:** "Quick question - has anyone shown you what 15-25% current THD from your gaming floor is actually costing in demand charges?"

**Email 2: Harmonic Distortion Root Cause**
- Gaming equipment (slots, VFDs on HVAC) creates 15-25% THD
- Office buildings: 5-8% THD (comparison)
- Inflates apparent power (kVA) → higher demand readings
- Why BMS and LED upgrades don't address this
- CTA: "Download harmonic distortion analysis"
- Length: 90-110 words
- **OPENER:** "Here's why your energy projects probably underdelivered on ROI..."

**Email 3: Power Quality Benefits Beyond Savings**
- Cleaner power = extended equipment life
- Reduced voltage fluctuations and transients
- Better power factor without capacitor banks
- CTA: "Review technical specifications"
- Length: 90-110 words
- **OPENER:** "The savings are great, but here's what most facilities teams find even more valuable..."

**Email 4: How It Works + 5% Guarantee**
- Solid-state filtration at electrical panel level
- No moving parts, no maintenance, 20+ year life
- **5% GUARANTEE:** "50,000+ installations, never below 5%, full refund"
- CTA: "Send specs to your engineering team"
- Length: 80-100 words
- **OPENER:** "Here's the technical breakdown of how it eliminates harmonics at the source..."

**Email 5: Low-Risk 30-Day Pilot**
- Same metered pilot as Vegas casino
- Pre-defined success criteria with power quality monitoring
- 5% minimum guarantee
- CTA: "Review pilot terms"
- Length: 80-100 words
- **OPENER:** "Would you be open to a 30-day metered pilot with full power quality monitoring?"

**FACILITIES EMAIL 1 EXAMPLE:**

"Quick question - has anyone shown you what 15-25% current THD from your gaming floor is actually costing in demand charges?

A Las Vegas casino achieved these verified results:

• 8.59% kW reduction (peak demand)
• Third-party verified over 12 months
• Zero downtime installation
• Addressed harmonic distortion at the source

Based on {company['company_name']}'s ~${company['estimated_energy_spend']:,.0f} annual energy spend, similar results would mean ${company['annual_savings_dollars']:,.0f}/year.

The technology addresses the root cause gaming equipment inefficiency - the 15-25% harmonic distortion that LED upgrades and BMS can't touch."

**TONE GUIDANCE - FACILITIES VOICE:**

✓ GOOD (Technical but accessible):
- "Quick question - has anyone shown you what your THD is costing?"
- "Here's why energy projects underdeliver for casinos..."
- "The savings are great, but the power quality benefits are even better..."

✗ BAD (Too technical or salesy):
- "Let's discuss the kVA implications of your harmonic spectrum..."
- "This is a limited-time offer..."

**OUTPUT FORMAT:**
Return JSON array with exactly {num_emails} emails.

**FACILITIES-SPECIFIC QUALITY CHECKS:**
- ✓ Lead with technical credibility (THD, power quality)
- ✓ Explain WHY gaming equipment creates problem
- ✓ Emphasize equipment life extension benefits
- ✓ Include 5% guarantee in Email 4 and 5
- ✓ Conversational but technically informed
- ✓ CONCISE - 90-110 words (1-3), 80-100 words (4-5)
- ✓ Zero fabricated case studies
- ✓ No greeting/signature

Now write {num_emails} world-class Facilities-focused emails that are TECHNICAL yet CONVERSATIONAL. Sound like a helpful expert, not a textbook. Make them the BEST B2B emails you've ever written."""

    try:
        message = await asyncio.to_thread(
            client.messages.create,
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        content = message.content[0].text
        if '```json' in content:
            json_str = content.split('```json')[1].split('```')[0].strip()
        else:
            json_str = content
        emails = json.loads(json_str)
        return emails
    except Exception as e:
        print(f"  ⚠️  Error generating Facilities emails: {e}")
        return [{
            "email_number": i+1,
            "subject": f"Harmonic distortion costing {company['company_name']}?",
            "body": f"Quick question - has anyone shown you what 15-25% current THD from your gaming floor is costing in demand charges? A Vegas casino achieved 8.59% kW reduction (third-party verified) by addressing harmonic distortion at the electrical panel - the root cause that LED upgrades and BMS can't touch. Based on your ~${company['estimated_sqft']:,} sqft property, similar results would mean ${company['annual_savings_dollars']:,.0f}/year plus better power quality facility-wide.",
            "cta": "See the technical specifications",
            "send_delay_days": i * 4
        } for i in range(num_emails)]


async def generate_esg_sequence(
    client: anthropic.Anthropic,
    prospect_analysis: Dict,
    num_emails: int
) -> List[Dict]:
    """
    ESG Director persona sequence
    Focus: Carbon reduction, board reporting, sustainability targets
    Tone: Impact-focused, measurable results, strategic positioning
    """

    company = prospect_analysis['company_profile']
    estimated_peak_kw = company['estimated_sqft'] / 100
    demand_charge_rate = 15
    current_annual_demand_charges = estimated_peak_kw * demand_charge_rate * 12
    projected_demand_savings = current_annual_demand_charges * (VERIFIED_CASE_STUDY['verified_reduction'] / 100)
    carbon_reduction = company['carbon_reduction_tons']

    prompt = f"""You are writing world-class B2B emails to an ESG/Sustainability Director at a casino. These must be the BEST emails you've ever written.

**YOUR VOICE:**
You're a helpful salesperson reaching out to an important opportunity. You're:
- Focused on measurable sustainability impact
- Understanding of ESG reporting requirements
- Emphasizing carbon reduction with strong ROI
- Educational about aligning sustainability with profitability

**CONTEXT:**
You are a reseller of Tune energy filters - solid-state technology that reduces harmonic distortion in casino electrical systems.

**PROSPECT:**
- Casino: {company['company_name']}
- Location: {company['location']}
- Size: {company['estimated_sqft']:,} sqft
- Estimated annual energy spend: ${company['estimated_energy_spend']:,.0f}
- Estimated carbon reduction: ~{carbon_reduction:,.0f} tons CO2/year

**VERIFIED CASE STUDY:**
- Casino: {VERIFIED_CASE_STUDY['casino']}
- Verified result: {VERIFIED_CASE_STUDY['verified_reduction']}% kW reduction
- Third-party verified over 12 months
- Measurable carbon reduction for ESG reporting
- 25-40% IRR (sustainability with ROI)

**TRANSPARENT PROJECTION:**
- Projected annual savings: ${company['annual_savings_dollars']:,.0f}/year
- Projected carbon reduction: ~{carbon_reduction:,.0f} tons CO2/year
- Supports 30-50% carbon reduction targets

**5% SAVINGS GUARANTEE:**
- 50,000+ installations worldwide
- Never achieved below 5% reduction
- Full refund if savings don't meet 5% minimum

**ESG-SPECIFIC FOCUS:**
- Lead with carbon reduction + financial ROI (sustainability that pays for itself)
- Emphasize third-party verification for board reporting
- Frame as achieving targets without sacrificing profitability
- Highlight 8.59% energy reduction = quantifiable impact
- Focus on immediate, measurable results

**5-EMAIL SEQUENCE FOR ESG:**

**Email 1: Carbon Reduction + ROI**
- Conversational opener about carbon targets + profitability
- Verified Vegas results with BULLETS (carbon + financial)
- WHY reaching out: ESG profile + strong ROI potential
- CTA: "See the third-party verification report"
- Length: 90-110 words
- **OPENER:** "Quick question - are you finding ways to hit carbon reduction targets that actually improve profitability, or is it always a trade-off?"

**Email 2: Measurable Impact for Board Reporting**
- Third-party verified results = credible ESG reporting
- 8.59% energy reduction = X tons CO2 reduction
- Supports 30-50% carbon reduction commitments
- CTA: "Download carbon reduction analysis"
- Length: 90-110 words
- **OPENER:** "Here's something your board might find interesting about measurable carbon reduction..."

**Email 3: Why Energy Efficiency ≠ Carbon Reduction (Usually)**
- Most energy projects focus on kWh (consumption)
- Demand (kW) reduction has higher carbon impact
- Gaming equipment harmonic distortion is the leverage point
- CTA: "See the carbon impact model"
- Length: 90-110 words
- **OPENER:** "Most sustainability programs focus on the wrong metric for casinos..."

**Email 4: How It Works + 5% Guarantee**
- Solid-state filtration = continuous carbon reduction
- No trade-off between sustainability and operations
- **5% GUARANTEE:** "50,000+ installations, never below 5%, full refund"
- 25-40% IRR (sustainability that pays for itself)
- CTA: "Review the ESG impact analysis"
- Length: 80-100 words
- **OPENER:** "What if you could accelerate carbon reduction AND improve EBITDA?"

**Email 5: Low-Risk 30-Day Pilot**
- Same metered pilot as Vegas casino
- Pre-defined success criteria (energy + carbon)
- Third-party verification for ESG reporting
- 5% minimum guarantee
- CTA: "Review pilot terms"
- Length: 80-100 words
- **OPENER:** "Would you be open to a 30-day pilot with third-party verification for board reporting?"

**ESG EMAIL 1 EXAMPLE:**

"Quick question - are you finding ways to hit carbon reduction targets that actually improve profitability, or is it always a trade-off?

A Las Vegas casino achieved these verified results:

• 8.59% kW reduction (peak demand)
• Third-party verified over 12 months
• 25-40% IRR

Based on {company['company_name']}'s profile, similar results would mean:

• ~{carbon_reduction:,.0f} tons CO2 reduction annually
• ${company['annual_savings_dollars']:,.0f}/year cost savings

The technology addresses energy waste at the source - delivering measurable sustainability impact that actually improves profitability."

**TONE GUIDANCE - ESG VOICE:**

✓ GOOD (Impact-focused, strategic):
- "Are you finding carbon solutions that improve profitability too?"
- "Here's something your board might find interesting..."
- "What if sustainability accelerated EBITDA growth?"

✗ BAD (Greenwashing, vague):
- "Join us in saving the planet..."
- "Be a sustainability leader..."

**OUTPUT FORMAT:**
Return JSON array with exactly {num_emails} emails.

**ESG-SPECIFIC QUALITY CHECKS:**
- ✓ Lead with carbon reduction + ROI (not trade-off)
- ✓ Emphasize third-party verification for reporting
- ✓ Frame as achieving targets while improving profitability
- ✓ Include 5% guarantee in Email 4 and 5
- ✓ Conversational, strategic tone
- ✓ CONCISE - 90-110 words (1-3), 80-100 words (4-5)
- ✓ Measurable impact (tons CO2, not vague claims)
- ✓ No greeting/signature

Now write {num_emails} world-class ESG-focused emails that are STRATEGIC and IMPACT-DRIVEN. Show that sustainability and profitability align. Make them the BEST B2B emails you've ever written."""

    try:
        message = await asyncio.to_thread(
            client.messages.create,
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        content = message.content[0].text
        if '```json' in content:
            json_str = content.split('```json')[1].split('```')[0].strip()
        else:
            json_str = content
        emails = json.loads(json_str)
        return emails
    except Exception as e:
        print(f"  ⚠️  Error generating ESG emails: {e}")
        return [{
            "email_number": i+1,
            "subject": f"Carbon reduction + ROI for {company['company_name']}",
            "body": f"Quick question - are you finding ways to hit carbon reduction targets that actually improve profitability, or is it always a trade-off? A Vegas casino achieved 8.59% kW reduction (third-party verified), translating to measurable carbon reduction with 25-40% IRR. Based on {company['company_name']}'s profile, similar results would mean ~{carbon_reduction:,.0f} tons CO2 reduction annually plus ${company['annual_savings_dollars']:,.0f}/year in cost savings - sustainability that strengthens EBITDA.",
            "cta": "See the ESG impact analysis",
            "send_delay_days": i * 4
        } for i in range(num_emails)]


async def process_prospect(client, prospect_analysis):
    """Generate 4 persona-specific email sequences for one prospect"""

    tier = prospect_analysis['priority_tier']
    num_emails = 5 if tier == 'A' else 3
    company_name = prospect_analysis['company_profile']['company_name']

    print(f"\n  📧 {company_name} (Tier {tier})")
    print(f"     Generating {num_emails} emails × 4 personas...")

    # Generate all 4 persona sequences
    email_sequences = {}

    # CFO sequence
    print(f"     → CFO sequence...")
    email_sequences['cfo'] = await generate_cfo_sequence(client, prospect_analysis, num_emails)

    # Operations Director sequence
    print(f"     → Operations sequence...")
    email_sequences['operations'] = await generate_operations_sequence(client, prospect_analysis, num_emails)

    # Facilities VP sequence
    print(f"     → Facilities sequence...")
    email_sequences['facilities'] = await generate_facilities_sequence(client, prospect_analysis, num_emails)

    # ESG Director sequence
    print(f"     → ESG sequence...")
    email_sequences['esg'] = await generate_esg_sequence(client, prospect_analysis, num_emails)

    prospect_analysis['email_sequences'] = email_sequences
    prospect_analysis['num_sequences_generated'] = 4
    prospect_analysis['num_emails_per_sequence'] = num_emails
    prospect_analysis['total_emails_generated'] = 4 * num_emails

    # Show first email subject from each sequence as preview
    print(f"     ✓ CFO Email 1: \"{email_sequences['cfo'][0]['subject']}\"")
    print(f"     ✓ Ops Email 1: \"{email_sequences['operations'][0]['subject']}\"")
    print(f"     ✓ Facilities Email 1: \"{email_sequences['facilities'][0]['subject']}\"")
    print(f"     ✓ ESG Email 1: \"{email_sequences['esg'][0]['subject']}\"")

    # Generate PDF lead magnet
    print(f"     → Generating PDF lead magnet...")
    pdf_filename = generate_cost_analysis_pdf(prospect_analysis)
    prospect_analysis['pdf_filename'] = pdf_filename
    prospect_analysis['pdf_url'] = f"{PDF_BASE_URL}/pdf/{pdf_filename}"
    print(f"     ✓ PDF generated: {pdf_filename}")
    print(f"     ✓ PDF URL: {prospect_analysis['pdf_url']}")

    return prospect_analysis

async def send_persona_to_clay(persona_name: str, persona_data: Dict):
    """Send one persona sequence to Clay webhook"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(CLAY_WEBHOOK_URL, json=persona_data)
            if response.status_code in [200, 201, 202]:
                print(f"    ✅ {persona_name.upper()}: Sent to Clay")
                return True
            else:
                print(f"    ❌ {persona_name.upper()}: Clay error: {response.status_code}")
                return False
    except Exception as e:
        print(f"    ❌ {persona_name.upper()}: Error: {e}")
        return False

def export_results(results: List[Dict], filename_base: str):
    """Export results to CSV and JSON (with 4 personas per casino)"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"{filename_base}_{timestamp}.csv"
    json_filename = f"{filename_base}_{timestamp}.json"

    # CSV export - one row per casino with all 4 persona sequences
    csv_data = []
    for r in results:
        row = {
            'company_name': r['company_profile']['company_name'],
            'domain': r['company_profile']['domain'],
            'location': r['company_profile']['location'],
            'composite_score': r['composite_score'],
            'tier': r['priority_tier'],
            'annual_savings_projected': f"${r['company_profile']['annual_savings_dollars']:,.0f}",
            'num_sequences': r['num_sequences_generated'],
            'total_emails': r['total_emails_generated'],
        }

        # Add all 4 persona sequences
        for persona in ['cfo', 'operations', 'facilities', 'esg']:
            if persona in r['email_sequences']:
                sequence = r['email_sequences'][persona]
                for i, email in enumerate(sequence, 1):
                    row[f'{persona}_email_{i}_subject'] = email.get('subject', '')
                    row[f'{persona}_email_{i}_body'] = email.get('body', '')
                    row[f'{persona}_email_{i}_cta'] = email.get('cta', '')
                    row[f'{persona}_email_{i}_delay_days'] = email.get('send_delay_days', 0)

        csv_data.append(row)

    with open(csv_filename, 'w', newline='') as f:
        if csv_data:
            writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
            writer.writeheader()
            writer.writerows(csv_data)

    # JSON export
    with open(json_filename, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Exported to:")
    print(f"   CSV: {csv_filename}")
    print(f"   JSON: {json_filename}")

    return csv_filename, json_filename

async def main():
    """Generate 4 persona-specific email sequences for top 5 casinos"""

    print(f"\n{'='*70}")
    print("WORLD-CLASS CASINO EMAIL GENERATION - 4 PERSONA SEQUENCES")
    print(f"{'='*70}")
    print("✓ 4 personas: CFO, Operations, Facilities, ESG")
    print("✓ Conversational tone (helpful salesperson, not robot)")
    print("✓ 5% savings guarantee (50,000+ installations)")
    print("✓ Peak demand charges education")
    print("✓ ONE verified case study (Vegas casino, 8.59% kW reduction)")
    print("✓ Transparent projections (no fabrication)")
    print("✓ Body only (no greetings/signatures)")
    print(f"{'='*70}\n")

    # Load analysis
    df = pd.read_csv('casino_analysis_20251029_225746.csv')
    df['annual_savings_numeric'] = df['annual_savings_dollars'].str.replace('$', '').str.replace(',', '').astype(float)

    # Get top 5 A-tier
    a_tier = df[df['priority_tier'] == 'A'].nlargest(5, 'annual_savings_numeric')

    print(f"Selected top 5 A-tier casinos:\n")

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
    print("GENERATING WORLD-CLASS 5-EMAIL SEQUENCES")
    print(f"{'='*70}\n")

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    # Generate emails sequentially for visibility
    results = []
    for i, prospect in enumerate(prospects, 1):
        print(f"[{i}/5] {prospect['company_profile']['company_name']}")
        result = await process_prospect(client, prospect)
        results.append(result)
        print()

    # Export
    csv_file, json_file = export_results(results, "worldclass_casino_emails")

    # Send to Clay - separate webhook for each persona
    print(f"\n{'='*70}")
    print(f"SENDING TO CLAY WEBHOOK (4 PERSONAS × {len(results)} CASINOS)")
    print(f"{'='*70}\n")

    success_count = 0
    total_webhooks = len(results) * 4
    webhook_num = 0

    for i, prospect in enumerate(results, 1):
        print(f"[Casino {i}/{len(results)}] {prospect['company_profile']['company_name']}")

        # Send 4 separate webhooks - one for each persona
        for persona in ['cfo', 'operations', 'facilities', 'esg']:
            webhook_num += 1

            # Build persona-specific payload
            persona_payload = {
                'persona': persona,
                'company_profile': prospect['company_profile'],
                'composite_score': prospect['composite_score'],
                'priority_tier': prospect['priority_tier'],
                'email_sequence': prospect['email_sequences'][persona],
                'num_emails': len(prospect['email_sequences'][persona]),
                'pdf_filename': prospect.get('pdf_filename', ''),
                'pdf_url': prospect.get('pdf_url', '')
            }

            if await send_persona_to_clay(persona, persona_payload):
                success_count += 1
            await asyncio.sleep(0.2)

        print()  # Blank line between casinos

    # Summary
    total_emails = sum(r['total_emails_generated'] for r in results)
    total_sequences = sum(r['num_sequences_generated'] for r in results)
    print(f"\n{'='*70}")
    print("WORLD-CLASS 4-PERSONA EMAIL GENERATION COMPLETE")
    print(f"{'='*70}")
    print(f"✅ Casinos: {len(results)}")
    print(f"✅ Persona sequences: {total_sequences} (CFO, Operations, Facilities, ESG)")
    print(f"✅ Total emails generated: {total_emails}")
    print(f"✅ Webhooks sent to Clay: {success_count}/{total_webhooks} (4 per casino)")
    print(f"✅ Files: {csv_file}, {json_file}")
    print(f"\n{'='*70}")
    print("QUALITY VALIDATION CHECKLIST")
    print(f"{'='*70}")
    print("Please manually review the generated emails for:")
    print("  ☐ Zero fabricated case studies (only Vegas casino used)")
    print("  ☐ Transparent projections ('Based on verified results...')")
    print("  ☐ Conversational tone (helpful salesperson, not robot)")
    print("  ☐ 5% savings guarantee in Email 4 and 5")
    print("  ☐ Persona-specific angles (CFO=EBITDA, Ops=Downtime, etc.)")
    print("  ☐ Human voice (not corporate speak)")
    print("  ☐ No greetings/signatures (body only)")
    print("  ☐ Natural CTA progression (not pushy)")
    print("  ☐ Demand charges explained clearly")
    print(f"\nReview file: {json_file}")

if __name__ == "__main__":
    asyncio.run(main())

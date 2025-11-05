"""
Tune Agent Builder API Server
FastAPI server exposing all agent capabilities via REST API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import json
from pathlib import Path
import csv
import io

from src.agent_builder_system import MasterAgentBuilder, IndustryType, IndustryAgent
from src.prospect_intelligence import ProspectIntelligence, BatchProspectProcessor
from src.content_generator import ContentGenerator, BatchContentGenerator
from src.clay_integration import ClayIntegration, ClayWebhookHandler
from src.database_async import TuneDatabaseAsync  # Using async database with connection pooling
from src.analytics import AnalyticsEngine, ABTestAnalyzer
from src.auth import require_auth, APIKey, get_api_key_for_testing
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="Tune® Agent Builder API",
    description="Elite agent creation and outbound automation system",
    version="3.0.0",
    docs_url="/docs" if os.getenv("ENABLE_API_DOCS", "true").lower() == "true" else None,
    redoc_url="/redoc" if os.getenv("ENABLE_API_DOCS", "true").lower() == "true" else None,
)

# CORS - Secure configuration from environment
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type", "Authorization"],
    max_age=3600
)

# Global state
agents_cache = {}
config = {}
db = None  # Database instance


# ============================================================================
# MODELS
# ============================================================================

class BuildAgentRequest(BaseModel):
    industry: str = Field(..., description="Industry type (casino, hospital, etc.)")
    personalization_depth: int = Field(4, ge=1, le=5)
    
class ProspectInput(BaseModel):
    company_name: str
    domain: Optional[str] = None
    employee_count: int = 0
    locations_count: int = 1
    
class BatchProspectRequest(BaseModel):
    prospects: List[ProspectInput]
    concurrency: int = 5
    
class ContentGenerationRequest(BaseModel):
    prospect_analysis: Dict
    persona_type: str
    
class ClayWebhookPayload(BaseModel):
    webhook_type: str
    table_id: str
    data: Dict

class HospitalInput(BaseModel):
    hospital_name: str = Field(..., description="Hospital name")
    location: Optional[str] = Field(None, description="Hospital location")
    contact_name: Optional[str] = Field(None, description="Contact name")
    contact_title: Optional[str] = Field(None, description="Contact title")
    contact_email: Optional[str] = Field(None, description="Contact email")
    beds: Optional[int] = Field(None, description="Number of beds")
    sqft: Optional[int] = Field(None, description="Square footage")
    annual_energy_spend: Optional[float] = Field(None, description="Annual energy spend")

class HospitalBatchRequest(BaseModel):
    hospitals: List[HospitalInput]
    generate_pdfs: bool = Field(True, description="Generate PDF lead magnets")
    generate_emails: bool = Field(True, description="Generate email sequences")


# ============================================================================
# CONFIGURATION
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Load configuration on startup"""
    global config, db

    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        print("✅ Configuration loaded")
    except:
        print("⚠️  No config file found, using defaults")
        config = {
            "claude_api_key": os.getenv("CLAUDE_API_KEY", "your-api-key"),
            "clay_api_key": os.getenv("CLAY_API_KEY", "your-clay-key")
        }

    # Initialize async database with connection pooling
    db = TuneDatabaseAsync()
    await db.init_db()
    print(f"✅ Async database initialized with connection pooling")

def get_agent(industry: str) -> IndustryAgent:
    """Get or load agent from cache"""
    if industry not in agents_cache:
        raise HTTPException(status_code=404, detail=f"Agent for {industry} not found. Build it first.")
    return agents_cache[industry]


# ============================================================================
# AGENT BUILDING ENDPOINTS
# ============================================================================

@app.post("/api/agents/build", tags=["Agents"])
async def build_agent(
    request: BuildAgentRequest,
    background_tasks: BackgroundTasks,
    api_key: APIKey = Depends(require_auth)
):
    """Build a new industry agent (PROTECTED - requires API key)"""
    
    try:
        industry_enum = IndustryType[request.industry.upper()]
    except KeyError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid industry. Options: {[e.value for e in IndustryType]}"
        )
    
    # Build agent in background
    async def build_task():
        builder = MasterAgentBuilder(config["claude_api_key"])
        agent = await builder.build_agent(
            industry_enum,
            {"personalization_depth": request.personalization_depth}
        )
        agents_cache[request.industry] = agent
        
        # Save to disk
        agent.save(f"/home/claude/tune_agents/{request.industry}_agent.json")
    
    background_tasks.add_task(build_task)
    
    return {
        "status": "building",
        "industry": request.industry,
        "message": "Agent build started. Check /api/agents/{industry}/status"
    }

@app.get("/api/agents/{industry}/status", tags=["Agents"])
async def get_agent_status(
    industry: str,
    api_key: APIKey = Depends(require_auth)
):
    """Check if agent is built and ready (PROTECTED - requires API key)"""
    
    if industry in agents_cache:
        agent = agents_cache[industry]
        return {
            "status": "ready",
            "industry": industry,
            "name": agent.name,
            "personas": len(agent.ideal_personas),
            "created_at": agent.created_at.isoformat()
        }
    else:
        return {"status": "not_built", "industry": industry}

@app.get("/api/agents/{industry}", tags=["Agents"])
async def get_agent_details(
    industry: str,
    api_key: APIKey = Depends(require_auth)
):
    """Get full agent details (PROTECTED - requires API key)"""
    
    agent = get_agent(industry)
    
    return {
        "industry": agent.industry.value,
        "name": agent.name,
        "description": agent.description,
        "personas": [p.persona_type.value for p in agent.ideal_personas],
        "savings_benchmark": agent.savings_benchmarks,
        "scoring_weights": agent.scoring_weights,
        "case_studies": agent.case_studies
    }


# ============================================================================
# PROSPECT INTELLIGENCE ENDPOINTS
# ============================================================================

@app.post("/api/prospects/analyze", tags=["Prospects"])
async def analyze_prospect(
    industry: str,
    prospect: ProspectInput,
    api_key: APIKey = Depends(require_auth)
):
    """Analyze single prospect (PROTECTED - requires API key)"""

    agent = get_agent(industry)

    intelligence = ProspectIntelligence(agent, config["claude_api_key"])
    analysis = await intelligence.analyze_prospect(prospect.dict())

    return analysis

@app.post("/api/prospects/analyze-batch", tags=["Prospects"])
async def analyze_prospect_batch(
    industry: str,
    request: BatchProspectRequest,
    api_key: APIKey = Depends(require_auth)
):
    """Analyze batch of prospects (PROTECTED - requires API key)"""

    agent = get_agent(industry)

    processor = BatchProspectProcessor(agent, config["claude_api_key"])
    prospects_data = [p.dict() for p in request.prospects]
    results = await processor.process_batch(prospects_data, request.concurrency)

    return {
        "total_processed": len(results),
        "priority_breakdown": {
            "A": len([r for r in results if r["priority_tier"] == "A"]),
            "B": len([r for r in results if r["priority_tier"] == "B"]),
            "C": len([r for r in results if r["priority_tier"] == "C"])
        },
        "results": results
    }


# ============================================================================
# CONTENT GENERATION ENDPOINTS
# ============================================================================

@app.post("/api/content/generate-sequence", tags=["Content"])
async def generate_email_sequence(
    industry: str,
    request: ContentGenerationRequest,
    api_key: APIKey = Depends(require_auth)
):
    """Generate email sequence for prospect (PROTECTED - requires API key)"""
    
    agent = get_agent(industry)
    
    generator = ContentGenerator(agent, config["claude_api_key"])
    sequence = await generator.generate_full_sequence(
        request.prospect_analysis,
        request.persona_type
    )
    
    return {
        "company": request.prospect_analysis["company_profile"]["company_name"],
        "persona": request.persona_type,
        "emails": sequence,
        "total_emails": len(sequence),
        "avg_quality": sum(e["quality_score"] for e in sequence) / len(sequence)
    }

@app.post("/api/content/generate-batch", tags=["Content"])
async def generate_content_batch(
    industry: str,
    analyzed_prospects: List[Dict],
    api_key: APIKey = Depends(require_auth)
):
    """Generate content for batch of analyzed prospects (PROTECTED - requires API key)"""
    
    agent = get_agent(industry)
    
    generator = BatchContentGenerator(agent, config["claude_api_key"])
    results = await generator.generate_sequences_batch(analyzed_prospects)
    
    return {
        "total_prospects": len(results),
        "total_emails": sum(len(r["sequence"]) for r in results),
        "results": results
    }

@app.post("/api/content/linkedin-message", tags=["Content"])
async def generate_linkedin_message(
    industry: str,
    request: ContentGenerationRequest,
    api_key: APIKey = Depends(require_auth)
):
    """Generate LinkedIn connection message (PROTECTED - requires API key)"""
    
    agent = get_agent(industry)
    
    generator = ContentGenerator(agent, config["claude_api_key"])
    message = await generator.generate_linkedin_message(
        request.prospect_analysis,
        request.persona_type
    )
    
    return message

@app.post("/api/content/video-script", tags=["Content"])
async def generate_video_script(
    industry: str,
    request: ContentGenerationRequest,
    duration_seconds: int = 60,
    api_key: APIKey = Depends(require_auth)
):
    """Generate Loom video script (PROTECTED - requires API key)"""
    
    agent = get_agent(industry)
    
    generator = ContentGenerator(agent, config["claude_api_key"])
    script = await generator.generate_video_script(
        request.prospect_analysis,
        request.persona_type,
        duration_seconds
    )
    
    return script


# ============================================================================
# CLAY INTEGRATION ENDPOINTS
# ============================================================================

@app.post("/api/clay/setup-tables", tags=["Clay"])
async def setup_clay_tables(
    industry: str,
    api_key: APIKey = Depends(require_auth)
):
    """Setup Clay tables for industry (PROTECTED - requires API key)"""
    
    agent = get_agent(industry)
    
    clay = ClayIntegration(config["clay_api_key"], agent)
    tables = await clay.setup_tables()
    
    return {
        "status": "success",
        "tables": tables
    }

@app.post("/api/clay/webhook", tags=["Clay"])
async def handle_clay_webhook(payload: ClayWebhookPayload):
    """Handle webhooks from Clay"""
    
    industry = payload.data.get("industry", "casino")
    agent = get_agent(industry)
    
    handler = ClayWebhookHandler(
        agent,
        config["claude_api_key"],
        config["clay_api_key"]
    )
    
    if payload.webhook_type == "new_prospect":
        result = await handler.handle_new_prospect(payload.data)
    elif payload.webhook_type == "generate_content":
        result = await handler.handle_trigger_content_generation(payload.data)
    else:
        raise HTTPException(400, f"Unknown webhook type: {payload.webhook_type}")
    
    return result


# ============================================================================
# COMPLETE WORKFLOW ENDPOINTS
# ============================================================================

@app.post("/api/workflows/complete-pipeline", tags=["Workflows"])
async def run_complete_pipeline(
    industry: str,
    prospects: List[ProspectInput],
    write_to_clay: bool = True,
    api_key: APIKey = Depends(require_auth)
):
    """Run complete pipeline: analyze → generate → export (PROTECTED - requires API key)"""
    
    agent = get_agent(industry)
    
    # Step 1: Analyze prospects
    processor = BatchProspectProcessor(agent, config["claude_api_key"])
    prospects_data = [p.dict() for p in prospects]
    analyzed = await processor.process_batch(prospects_data)
    
    # Step 2: Filter high-scorers
    high_scorers = [a for a in analyzed if a["composite_score"] >= 70]
    
    # Step 3: Generate content
    content_gen = BatchContentGenerator(agent, config["claude_api_key"])
    content = await content_gen.generate_sequences_batch(high_scorers)
    
    # Step 4: Write to Clay if requested
    clay_result = None
    if write_to_clay:
        clay = ClayIntegration(config["clay_api_key"], agent)
        
        # Write analyses
        for analysis in analyzed:
            await clay.write_prospect_analysis("prospects_table", analysis)
        
        # Write content
        await clay.write_generated_content("content_table", content)
        
        clay_result = "data_written_to_clay"
    
    return {
        "total_prospects": len(analyzed),
        "high_scorers": len(high_scorers),
        "emails_generated": sum(len(c["sequence"]) for c in content),
        "clay_status": clay_result,
        "analyzed": analyzed,
        "content": content
    }


# ============================================================================
# CAMPAIGN & DATABASE ENDPOINTS
# ============================================================================

@app.post("/api/campaigns/create", tags=["Campaigns"])
async def create_campaign(
    name: str,
    industry: str,
    api_key: APIKey = Depends(require_auth)
):
    """Create new campaign (PROTECTED - requires API key)"""
    campaign_id = await db.create_campaign(name, industry)
    return {
        "campaign_id": campaign_id,
        "name": name,
        "industry": industry
    }

@app.get("/api/campaigns/{campaign_id}", tags=["Campaigns"])
async def get_campaign_details(
    campaign_id: int,
    api_key: APIKey = Depends(require_auth)
):
    """Get campaign details (PROTECTED - requires API key)"""
    campaign = await db.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    return campaign

@app.get("/api/campaigns/{campaign_id}/prospects/{tier}", tags=["Campaigns"])
async def get_campaign_prospects_by_tier(
    campaign_id: int,
    tier: str,
    api_key: APIKey = Depends(require_auth)
):
    """Get campaign prospects by tier (A, B, C) (PROTECTED - requires API key)"""
    prospects = await db.get_prospects_by_tier(campaign_id, tier)
    return {
        "campaign_id": campaign_id,
        "tier": tier,
        "count": len(prospects),
        "prospects": prospects
    }


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/api/analytics/{campaign_id}/report", tags=["Analytics"])
async def get_campaign_report(
    campaign_id: int,
    days: int = 30,
    api_key: APIKey = Depends(require_auth)
):
    """Get comprehensive campaign analytics report (PROTECTED - requires API key)"""
    analytics = AnalyticsEngine(db)
    insights = analytics.get_campaign_insights(campaign_id, days)

    return {
        "campaign_id": campaign_id,
        "period_days": days,
        "overall_metrics": insights.overall_metrics,
        "persona_performance": insights.persona_performance,
        "tier_performance": insights.tier_performance,
        "best_content": insights.best_performing_content,
        "recommendations": insights.recommendations
    }

@app.get("/api/analytics/{campaign_id}/roi-by-persona", tags=["Analytics"])
async def get_persona_roi(
    campaign_id: int,
    api_key: APIKey = Depends(require_auth)
):
    """Get ROI analysis by persona (PROTECTED - requires API key)"""
    analytics = AnalyticsEngine(db)
    roi = analytics.get_persona_roi_analysis(campaign_id)

    return {
        "campaign_id": campaign_id,
        "persona_roi": roi
    }

@app.get("/api/analytics/{campaign_id}/content-quality", tags=["Analytics"])
async def get_content_quality_analysis(
    campaign_id: int,
    api_key: APIKey = Depends(require_auth)
):
    """Get content quality vs performance analysis (PROTECTED - requires API key)"""
    analytics = AnalyticsEngine(db)
    quality_analysis = analytics.get_content_quality_analysis(campaign_id)

    return quality_analysis

@app.get("/api/analytics/{campaign_id}/ab-test/{test_name}", tags=["Analytics"])
async def get_ab_test_results(
    campaign_id: int,
    test_name: str,
    api_key: APIKey = Depends(require_auth)
):
    """Get A/B test analysis (PROTECTED - requires API key)"""
    ab_analyzer = ABTestAnalyzer(db)
    results = ab_analyzer.analyze_test(campaign_id, test_name)

    return results


# ============================================================================
# EMAIL TRACKING ENDPOINTS
# ============================================================================

@app.post("/api/tracking/email-opened", tags=["Tracking"])
async def track_email_opened(
    content_id: int,
    contact_id: int,
    api_key: APIKey = Depends(require_auth)
):
    """Track email open event (PROTECTED - requires API key)"""
    await db.track_email_event(content_id, contact_id, "opened")
    return {"status": "tracked"}

@app.post("/api/tracking/email-clicked", tags=["Tracking"])
async def track_email_clicked(
    content_id: int,
    contact_id: int,
    link_url: Optional[str] = None,
    api_key: APIKey = Depends(require_auth)
):
    """Track email click event (PROTECTED - requires API key)"""
    event_data = {"link_url": link_url} if link_url else None
    await db.track_email_event(content_id, contact_id, "clicked", event_data)
    return {"status": "tracked"}

@app.post("/api/tracking/email-replied", tags=["Tracking"])
async def track_email_replied(
    content_id: int,
    contact_id: int,
    api_key: APIKey = Depends(require_auth)
):
    """Track email reply event (PROTECTED - requires API key)"""
    await db.track_email_event(content_id, contact_id, "replied")
    return {"status": "tracked"}


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.get("/api/health", tags=["Utility"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agents_loaded": list(agents_cache.keys()),
        "database_connected": db is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/industries", tags=["Utility"])
async def list_industries(api_key: APIKey = Depends(require_auth)):
    """List available industries (PROTECTED - requires API key)"""
    return {
        "industries": [e.value for e in IndustryType]
    }


# ============================================================================
# HOSPITAL-SPECIFIC ENDPOINTS (CSV Upload & Clay Integration)
# ============================================================================

def get_persona_focus(persona_type: str) -> str:
    """Get persona-specific focus areas"""
    focus_map = {
        'finance': 'EBITDA impact, ROI, margin improvement, budget optimization, capital allocation',
        'esg': 'Carbon reduction, ESG reporting, sustainability goals, green building certifications, stakeholder expectations',
        'operations': 'Operational reliability, uptime, patient care continuity, equipment performance, risk mitigation',
        'executive_leadership': 'Strategic value, competitive advantage, organizational goals, board reporting, community impact',
        'facilities': 'Cost savings, equipment efficiency, maintenance reduction, energy optimization, operational simplicity'
    }
    return focus_map.get(persona_type, 'Cost savings and operational efficiency')


async def process_hospital_data(hospital_input: Dict, agent: Dict) -> Dict:
    """Process a single hospital and generate content + PDF"""
    import anthropic
    from pdf_lead_magnets.hospital_pdf_generator import generate_hospital_cost_analysis_pdf

    # Enrich hospital data
    hospital_name = hospital_input.get('hospital_name', 'Unknown Hospital')
    location = hospital_input.get('location', 'United States')

    # Handle empty strings from CSV
    beds_str = str(hospital_input.get('beds', 200))
    beds = int(beds_str) if beds_str and beds_str.strip() and beds_str != '0' else 200

    sqft_str = str(hospital_input.get('sqft', 0))
    sqft = int(sqft_str) if sqft_str and sqft_str.strip() and sqft_str != '0' else 0

    # DO NOT estimate sqft from beds - many hospitals have multiple locations
    # Only use sqft if explicitly provided
    if sqft == 0:
        sqft = 500000  # Default conservative estimate for calculation purposes only

    # Handle empty string for annual energy spend
    annual_spend_str = str(hospital_input.get('annual_energy_spend', 0))
    annual_energy_spend = float(annual_spend_str) if annual_spend_str and annual_spend_str.strip() and annual_spend_str != '0' else 0

    if annual_energy_spend == 0:
        kwh_per_sqft = 250
        cost_per_kwh = 0.11
        annual_energy_spend = sqft * kwh_per_sqft * cost_per_kwh

    savings_percentage = agent.get('savings_benchmarks', {}).get('typical_percentage', 12)
    annual_savings = annual_energy_spend * (savings_percentage / 100)
    monthly_savings = annual_savings / 12
    five_year_savings = annual_savings * 5

    annual_kwh = annual_energy_spend / 0.11
    carbon_reduction_tons = (annual_kwh * (savings_percentage / 100) * 0.92) / 2000

    estimated_investment = sqft * 0.50
    payback_months = round((estimated_investment / monthly_savings) if monthly_savings > 0 else 18)

    enriched_data = {
        'company_profile': {
            'company_name': hospital_name,
            'location': location,
            'beds': beds,
            'estimated_sqft': sqft,
            'estimated_energy_spend': round(annual_energy_spend),
            'annual_savings_dollars': round(annual_savings),
            'monthly_savings_dollars': round(monthly_savings),
            'five_year_savings': round(five_year_savings),
            'carbon_reduction_tons': round(carbon_reduction_tons),
            'payback_months': payback_months,
            'savings_percentage': savings_percentage,
            'domain': hospital_input.get('domain', '')
        },
        'contact': {
            'name': hospital_input.get('contact_name', ''),
            'first_name': hospital_input.get('contact_first_name', hospital_input.get('contact_name', '').split()[0] if hospital_input.get('contact_name', '') else ''),
            'title': hospital_input.get('contact_title', ''),
            'email': hospital_input.get('contact_email', '')
        }
    }

    # Generate PDF
    pdf_filename = generate_hospital_cost_analysis_pdf(enriched_data)
    pdf_base_url = os.getenv("PDF_BASE_URL", "http://localhost:8000")
    pdf_url = f"{pdf_base_url}/pdf/{pdf_filename}"

    # Check if email exists - skip entirely if not
    contact_email = hospital_input.get('contact_email', '').strip()
    has_email = bool(contact_email)

    # Skip this contact entirely if no email (don't return anything)
    if not has_email:
        return None

    # Generate email sequence
    client = anthropic.Anthropic(api_key=config["claude_api_key"])

    # Determine persona (5 categories: Operations, Finance, Executive Leadership, Facilities, ESG)
    contact_title = hospital_input.get('contact_title', '').lower()

    if any(x in contact_title for x in ['cfo', 'chief financial', 'finance', 'treasurer', 'controller']):
        persona_type = 'finance'
        persona_label = 'Finance'
    elif any(x in contact_title for x in ['sustainability', 'esg', 'environmental', 'chief sustainability']):
        persona_type = 'esg'
        persona_label = 'ESG'
    elif any(x in contact_title for x in ['operations', 'coo', 'chief operating', 'vp operations', 'director of operations']):
        persona_type = 'operations'
        persona_label = 'Operations'
    elif any(x in contact_title for x in ['ceo', 'president', 'chief executive', 'executive director', 'managing director', 'administrator']):
        persona_type = 'executive_leadership'
        persona_label = 'Executive Leadership'
    elif any(x in contact_title for x in ['facilities', 'facility', 'building', 'property', 'plant', 'energy', 'utilities']):
        persona_type = 'facilities'
        persona_label = 'Facilities'
    else:
        # Default to Facilities
        persona_type = 'facilities'
        persona_label = 'Facilities'

    value_props = agent.get('value_props_by_persona', {})
    # Map to agent personas (which might use different naming)
    persona_mapping = {
        'finance': ['cfo', 'finance'],
        'esg': ['esg_director', 'sustainability_chief'],
        'operations': ['operations_director', 'coo'],
        'executive_leadership': ['ceo', 'executive'],
        'facilities': ['facilities_vp', 'energy_manager', 'director_facilities']
    }

    # Try to find matching value prop from agent
    persona_value_prop = {}
    for agent_persona_key in persona_mapping.get(persona_type, ['facilities_vp']):
        if agent_persona_key in value_props:
            persona_value_prop = value_props[agent_persona_key]
            break

    # Fallback to first available
    if not persona_value_prop and value_props:
        persona_value_prop = list(value_props.values())[0]

    company = enriched_data['company_profile']
    contact = enriched_data['contact']

    prompt = f"""You are writing a 5-email sequence for {contact.get('first_name', '')} at {company['company_name']}.

**PROSPECT:**
Name: {contact.get('first_name', '')} {contact.get('name', '').split()[-1] if contact.get('name', '') else ''}
Title: {contact.get('title', '')}
Hospital: {company['company_name']}
Persona: {persona_label}

**THEIR WORLD ({persona_label}):**
{get_persona_focus(persona_type)}
Pain: Energy costs rising, but can't deploy most efficiency solutions due to patient safety risks

**YOUR SOLUTION:**
Passive Harmonics Filter
- Key breakthrough: If it fails → nothing happens (no power interruption, zero patient risk)
- Unlike active systems that can cause power issues
- This is WHY hospitals can actually use it
- Results: 8-12% energy savings (est ${company['annual_savings_dollars']:,}/year for them)
- Real case study at captivateenergy.com

**SALES APPROACH:**
Start with THEIR experience (what they're dealing with), not your product.
Build curiosity - don't info-dump.
Make case study mentions conversational and natural.
The passive filter is the breakthrough moment - make it hit.

**EMAIL REQUIREMENTS:**
- 75-90 words each
- Paragraph breaks (\\n\\n)
- Professional but warm and conversational
- Lead with THEIR pain/experience, not features
- Build curiosity naturally
- Use "estimated" or "(est)" with dollars
- NO greetings, NO signatures

**5-EMAIL SEQUENCE:**

**Email 1: Their Reality → Breakthrough**
Start with their world: energy costs climbing, can't deploy most solutions (too risky for hospitals).
Then introduce the breakthrough: passive harmonics filter = if it fails, nothing happens. Zero patient risk.
Mention naturally: "Happy to walk you through how another hospital system proved this out - there's a case study at captivateenergy.com if you want to preview first."
CTA: "Worth exploring for {company['company_name']}?"
75-85 words

**Email 2: Why They Can't Use Traditional Solutions**
Empathize: Most energy tech is too risky for hospitals - if it fails, patients are at risk.
The passive approach changes everything: fail-safe by design.
Build curiosity conversationally: "Happy to walk you through how another hospital system approached this - the case study's at captivateenergy.com if you want to preview."
CTA: Simple and natural
80-90 words

**Email 3: Their Specific Pain Point**
Focus on {persona_label}'s world - what they experience without this solution.
Show how passive filter solves their specific problem (not generic).
Reference results naturally: "Can walk you through how similar hospitals achieved 8-12% reductions - the case study's at captivateenergy.com if you'd like to preview."
Make them curious to learn more
75-85 words

**Email 4: Conversational Social Proof**
"Talked to a {persona_label} at another health system recently..." approach.
Make it feel like a real conversation, not a sales pitch.
The passive filter angle resonated with them because [reason specific to persona].
Natural mention: "Happy to walk you through their results - similar to the case study at captivateenergy.com if you want to see it first."
75-85 words

**Email 5: Graceful Exit**
Acknowledge you've reached out a few times.
Restate the core benefit in one line: passive = safe, estimated savings.
Easy out: "If not a priority, totally understand."
Or simple next step: "Happy to walk you through the approach if you're curious - case study's at captivateenergy.com if you'd like to preview."
70-80 words

**CRITICAL RULES:**
1. Lead with THEIR experience, not your product
2. Build curiosity - don't lecture
3. Case study mentions must feel natural and conversational
4. Make passive filter = the breakthrough moment
5. Use \\n\\n for paragraph breaks
6. Stay 75-90 words
7. Professional but warm - write like you're helping, not selling

Return JSON: {{"emails": [{{"email_number": 1, "subject": "...", "body": "..."}}, ...]}}
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    content = message.content[0].text

    try:
        if '```json' in content:
            json_str = content.split('```json')[1].split('```')[0].strip()
            emails_data = json.loads(json_str)
        else:
            emails_data = {"emails": []}
    except:
        emails_data = {"emails": []}

    return {
        'hospital': enriched_data,
        'content': {
            'persona_type': persona_type,
            'persona_label': persona_label,
            'sequence': emails_data.get('emails', []),
            'value_prop': persona_value_prop,
            'pdf_url': pdf_url,
            'pdf_filename': pdf_filename
        },
        'processed_at': datetime.now().isoformat()
    }


@app.post("/api/hospital/process-csv", tags=["Hospital"])
async def process_hospital_csv(
    file: UploadFile = File(...),
    api_key: APIKey = Depends(require_auth)
):
    """
    Upload CSV of hospitals and generate personalized content + PDFs (PROTECTED)

    Expected CSV columns:
    - hospital_name (required)
    - location (optional)
    - contact_name (optional)
    - contact_title (optional)
    - contact_email (optional)
    - beds (optional)
    - sqft (optional)
    - annual_energy_spend (optional)
    """

    # Load hospital agent
    hospital_agent_path = Path("agents/hospital_agent.json")
    if not hospital_agent_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Hospital agent not found. Build it first: POST /api/agents/build with industry='hospital'"
        )

    with open(hospital_agent_path, 'r') as f:
        hospital_agent = json.load(f)

    # Parse CSV
    contents = await file.read()
    csv_text = contents.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(csv_text))

    hospitals = list(csv_reader)

    if len(hospitals) == 0:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    # Process each hospital (skip contacts without emails)
    results = []
    for hospital_input in hospitals:
        result = await process_hospital_data(hospital_input, hospital_agent)
        if result is not None:  # Only add if contact has email
            results.append(result)

    # Save results
    os.makedirs("outputs/hospital_campaigns", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"outputs/hospital_campaigns/hospital_campaign_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    return {
        "status": "success",
        "hospitals_processed": len(results),
        "pdfs_generated": len([r for r in results if 'pdf_filename' in r['content']]),
        "output_file": output_file,
        "results": results
    }


@app.post("/api/hospital/process-single", tags=["Hospital"])
async def process_single_hospital(
    hospital: HospitalInput,
    api_key: APIKey = Depends(require_auth)
):
    """
    Process single hospital from Clay webhook or API call (PROTECTED)
    Generates personalized email sequence + PDF lead magnet
    """

    # Load hospital agent
    hospital_agent_path = Path("agents/hospital_agent.json")
    if not hospital_agent_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Hospital agent not found. Build it first: POST /api/agents/build with industry='hospital'"
        )

    with open(hospital_agent_path, 'r') as f:
        hospital_agent = json.load(f)

    # Process hospital
    result = await process_hospital_data(hospital.dict(), hospital_agent)

    return result


@app.post("/api/hospital/process-batch", tags=["Hospital"])
async def process_hospital_batch(
    request: HospitalBatchRequest,
    api_key: APIKey = Depends(require_auth)
):
    """
    Process batch of hospitals from Clay (PROTECTED)
    Generates personalized content + PDFs for multiple hospitals
    """

    # Load hospital agent
    hospital_agent_path = Path("agents/hospital_agent.json")
    if not hospital_agent_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Hospital agent not found. Build it first: POST /api/agents/build with industry='hospital'"
        )

    with open(hospital_agent_path, 'r') as f:
        hospital_agent = json.load(f)

    # Process each hospital (skip contacts without emails)
    results = []
    for hospital_input in request.hospitals:
        result = await process_hospital_data(hospital_input.dict(), hospital_agent)
        if result is not None:  # Only add if contact has email
            results.append(result)

    # Save results
    os.makedirs("outputs/hospital_campaigns", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"outputs/hospital_campaigns/hospital_batch_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    return {
        "status": "success",
        "hospitals_processed": len(results),
        "pdfs_generated": len([r for r in results if 'pdf_filename' in r['content']]),
        "output_file": output_file,
        "results": results
    }


# ============================================================================
# PDF LEAD MAGNET ENDPOINTS
# ============================================================================

@app.get("/pdf/{filename}", tags=["PDF Lead Magnets"])
async def serve_pdf(filename: str):
    """
    Serve PDF lead magnet files
    No authentication required - these are meant to be shared publicly
    """
    pdf_path = Path("pdf_lead_magnets/generated") / filename

    # Security: Prevent directory traversal
    if not pdf_path.is_file() or ".." in filename or "/" in filename:
        raise HTTPException(status_code=404, detail="PDF not found")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename
    )

@app.get("/api/pdf/list", tags=["PDF Lead Magnets"])
async def list_pdfs(api_key: APIKey = Depends(require_auth)):
    """List all generated PDF lead magnets (PROTECTED - requires API key)"""
    pdf_dir = Path("pdf_lead_magnets/generated")

    if not pdf_dir.exists():
        return {"pdfs": []}

    pdfs = []
    for pdf_file in pdf_dir.glob("*.pdf"):
        stat = pdf_file.stat()
        pdfs.append({
            "filename": pdf_file.name,
            "size_bytes": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "url": f"/pdf/{pdf_file.name}"
        })

    return {
        "count": len(pdfs),
        "pdfs": sorted(pdfs, key=lambda x: x["created_at"], reverse=True)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

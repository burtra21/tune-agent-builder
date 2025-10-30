"""
Tune Agent Builder API Server
FastAPI server exposing all agent capabilities via REST API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import json
from pathlib import Path

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

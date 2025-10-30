# Tune® Agent Builder System

**Elite B2B outbound automation for Tune® energy filters**

This system creates industry-specialized AI agents that research prospects, generate hyper-personalized content, and orchestrate multi-channel outbound campaigns through Clay and n8n.

## 🎯 What It Does

1. **Builds Industry Agents** - Deep research on casino, hospital, data center, and other high-value industries
2. **Analyzes Prospects** - Multi-dimensional scoring based on intent, technical fit, urgency, and account value
3. **Generates Content** - Hyper-personalized emails, LinkedIn messages, and video scripts
4. **Orchestrates Campaigns** - Full integration with Clay tables and n8n workflows
5. **Optimizes Continuously** - Quality scoring and performance tracking

## 🚀 Quick Start

### 1. Install

```bash
cd /home/claude/tune_agent_builder
pip install -r requirements.txt
```

### 2. Configure

Create `config.json`:

```json
{
  "claude_api_key": "your-anthropic-api-key",
  "clay_api_key": "your-clay-api-key"
}
```

### 3. Build Your First Agent

```python
from agent_builder_system import MasterAgentBuilder, IndustryType
import asyncio

async def main():
    builder = MasterAgentBuilder("your-claude-api-key")
    
    # Build casino agent
    agent = await builder.build_agent(IndustryType.CASINO)
    agent.save("casino_agent.json")
    
    print(f"✨ Built {agent.name}")
    print(f"   Personas: {len(agent.ideal_personas)}")
    print(f"   Savings: {agent.savings_benchmarks['typical_percentage']}%")

asyncio.run(main())
```

### 4. Run Complete Pipeline

```python
from prospect_intelligence import BatchProspectProcessor
from content_generator import BatchContentGenerator

# Analyze prospects
processor = BatchProspectProcessor(agent, "api-key")
prospects = [
    {"company_name": "MGM Grand", "domain": "mgmgrand.com", "employee_count": 5000}
]
analyzed = await processor.process_batch(prospects)

# Generate content for high-scorers
high_scorers = [p for p in analyzed if p["composite_score"] >= 70]
generator = BatchContentGenerator(agent, "api-key")
content = await generator.generate_sequences_batch(high_scorers)

# Results automatically scored and ready for Clay
generator.export_to_clay_format("content_for_clay.json")
```

## 📊 API Server

Run the FastAPI server:

```bash
cd /home/claude/tune_agent_builder
uvicorn api_server:app --reload --port 8000
```

### Key Endpoints

**Build Agent:**
```bash
POST /api/agents/build
{
  "industry": "casino",
  "personalization_depth": 5
}
```

**Analyze Prospects:**
```bash
POST /api/prospects/analyze-batch
{
  "prospects": [
    {"company_name": "MGM", "employee_count": 5000}
  ],
  "concurrency": 5
}
```

**Generate Content:**
```bash
POST /api/content/generate-sequence
{
  "prospect_analysis": {...},
  "persona_type": "facilities_vp"
}
```

**Complete Pipeline:**
```bash
POST /api/workflows/complete-pipeline
{
  "industry": "casino",
  "prospects": [...],
  "write_to_clay": true
}
```

## 🗄️ Clay Integration

The system automatically creates three Clay tables:

1. **Master Prospects** - Company intelligence, scoring, savings projections
2. **Decision Makers** - Personas, outreach status, engagement metrics  
3. **Generated Content** - Emails with quality scores, ready for review/approval

### Automation Flow

1. Add prospects to Clay Master Prospects table
2. Clay webhook → triggers prospect analysis API
3. High-score prospects → auto-generate content
4. Content appears in Clay Content table for review
5. Approved content → sent via your email system

## ⚙️ n8n Workflows

Example workflow (prospect_enrichment.json):

```json
{
  "name": "Tune Prospect Enrichment",
  "nodes": [
    {
      "type": "Webhook",
      "parameters": {"path": "new-prospect"}
    },
    {
      "type": "HTTP Request",
      "parameters": {
        "url": "http://localhost:8000/api/prospects/analyze",
        "method": "POST"
      }
    },
    {
      "type": "Clay",
      "parameters": {"operation": "updateRow"}
    }
  ]
}
```

## 🎯 Industry Agent Features

Each agent includes:

- **Energy Profile**: kWh/sqft, load patterns, harmonics analysis
- **Value Props**: Industry-specific benefits by persona
- **Intent Signals**: Sustainability commitments, ESG reports, expansion plans
- **Scoring Algorithm**: Weighted composite of intent, fit, urgency, persona, value
- **Email Frameworks**: PEC+G, BAB, PAS sequences by persona
- **Case Studies**: Relevant Tune® installations and results

## 📈 Scoring System

**Composite Score** (0-100):
- Intent Signals: 35%
- Technical Fit: 25%
- Persona Quality: 20%
- Urgency: 15%
- Account Value: 5%

**Priority Tiers:**
- A (75+): Deep personalization, 7-touch sequence, video
- B (60-74): Standard personalization, 5-touch sequence  
- C (<60): Light personalization, 3-touch sequence

## 💎 Content Quality System

Emails scored 0-10 based on:
- Personalization depth (specific company details)
- Length optimization (80-150 words ideal)
- Avoidance of generic phrases
- Specific value quantification
- Company name usage

Emails <7 marked as "Draft" for improvement.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Master Agent Builder                     │
│  • Industry Research Engine                                 │
│  • Persona Intelligence                                     │
│  • Value Proposition Builder                                │
│  • Content Framework Designer                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Industry Agent (JSON)                     │
│  • Ideal Personas & Priorities                              │
│  • Intent Signals & Urgency Triggers                        │
│  • Email Sequences & LinkedIn Strategy                      │
│  • Scoring Weights & Research Protocols                     │
│  • Clay Schemas & n8n Workflows                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌──────────────────┴──────────────────┐
        ↓                                     ↓
┌──────────────────┐                 ┌──────────────────┐
│ Prospect Intel   │                 │ Content Gen      │
│ • Web Research   │                 │ • Email Seqs     │
│ • Intent Detect  │                 │ • LinkedIn Msgs  │
│ • Multi-Scoring  │                 │ • Video Scripts  │
│ • Enrichment     │                 │ • Quality Score  │
└──────────────────┘                 └──────────────────┘
        ↓                                     ↓
┌─────────────────────────────────────────────────────────────┐
│                      Clay Tables                            │
│  prospects → decision_makers → generated_content            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    n8n Automation                           │
│  • Webhook Triggers                                         │
│  • Rate Limiting                                            │
│  • Multi-Channel Sending                                    │
│  • Performance Tracking                                     │
└─────────────────────────────────────────────────────────────┘
```

## 🎨 Customization

### Add Custom Persona

```python
from agent_builder_system import PersonaProfile, PersonaType

custom_persona = PersonaProfile(
    persona_type=PersonaType.CFO,
    typical_titles=["CFO", "Chief Financial Officer", "VP Finance"],
    priorities=["Cost reduction", "ROI", "Budget optimization"],
    pain_points=["Rising operational costs", "Unpredictable expenses"],
    success_metrics=["Cost savings %", "Payback period"],
    decision_authority="Decision Maker",
    budget_influence="High",
    evaluation_criteria=["Clear ROI", "Risk mitigation", "Easy implementation"],
    objection_patterns=["Budget constraints", "Too good to be true"]
)
```

### Custom Email Framework

```python
from agent_builder_system import EmailFramework

framework = EmailFramework(
    touch_number=1,
    goal="Generate curiosity and book meeting",
    framework_type="PEC+G",
    max_words=120,
    tone="conversational",
    key_message="Industry-specific energy savings with proof",
    cta="15-min savings analysis call",
    hooks=[
        "Most {industry} facilities waste 10-15% on harmonic distortion...",
        "{Company} could save $X/year - here's how we know..."
    ],
    personalization_requirements=[
        "Company name",
        "Industry pain point",
        "Specific savings number",
        "Relevant case study"
    ]
)
```

## 🔒 Best Practices

1. **Always fetch before generating** - Use prospect analysis data for content
2. **Quality gate at 7.0** - Review anything below 7/10 quality score
3. **A/B test subject lines** - Generate 2-3 options per email
4. **Tier-appropriate effort** - Don't over-personalize C-tier prospects
5. **Track everything** - Use Clay fields for open/click/reply rates
6. **Iterate on performers** - Double down on high-response sequences

## 📁 File Structure

```
tune_agent_builder/
├── agent_builder_system.py    # Core agent builder
├── prospect_intelligence.py   # Analysis & scoring
├── content_generator.py       # Email/LinkedIn/video
├── clay_integration.py        # Clay API & webhooks
├── api_server.py             # FastAPI server
├── requirements.txt          # Dependencies
├── config.json              # API keys
├── README.md               # This file
└── agents/                # Saved agents
    ├── casino_agent.json
    ├── hospital_agent.json
    └── datacenter_agent.json
```

## 🚀 Advanced Usage

### Batch Processing with Priority

```python
# Process 1000 prospects
all_prospects = load_from_csv("prospects.csv")

# Analyze in batches
for batch in chunks(all_prospects, 50):
    analyzed = await processor.process_batch(batch)
    
    # Only generate for A-tier
    a_tier = [p for p in analyzed if p["priority_tier"] == "A"]
    content = await generator.generate_sequences_batch(a_tier)
    
    # Write to Clay
    await clay.write_generated_content("content_table", content)
```

### Multi-Industry Campaign

```python
industries = [IndustryType.CASINO, IndustryType.HOSPITAL, IndustryType.DATA_CENTER]

for industry in industries:
    agent = await builder.build_agent(industry)
    
    # Get prospects for this industry
    prospects = get_prospects_by_industry(industry.value)
    
    # Run pipeline
    analyzed = await processor.process_batch(prospects)
    content = await generator.generate_sequences_batch(analyzed)
```

## 📊 Expected Results

Based on Tune's case studies:

- **Casino**: 8-10% avg savings, $500K+ annual value for large properties
- **Hospital**: 12% avg savings, critical for ESG goals
- **Data Center**: 10-15% savings, massive scale opportunity
- **Multifamily**: 15% avg savings, portfolio-wide rollout potential

**Outbound Performance Targets:**
- A-Tier: 15-25% response rate
- B-Tier: 8-15% response rate  
- C-Tier: 3-8% response rate

## 🛠️ Troubleshooting

**Agent build fails:**
- Check Claude API key in config.json
- Ensure internet connection for research
- Verify sufficient API credits

**Low quality scores:**
- Increase personalization_depth in agent config
- Add more intent signals to prospect data
- Review and improve email frameworks

**Clay integration issues:**
- Verify Clay API key
- Check table IDs match schema
- Review webhook payload format

## 🎓 Training Tips

1. Start with one industry (casino recommended - clear ROI)
2. Build agent with max personalization (depth=5)
3. Test on 10 hand-picked prospects first
4. Review generated content quality
5. Iterate on frameworks based on responses
6. Scale to full list once dialed in

## 📞 Support

Built by [Eric Jenson](mailto:ejenson@captivateenergy.com) for Tune®

For questions or customization:
- Review code comments in each module
- Check API documentation at `/docs` endpoint
- Examine case studies in project files

---

**🚀 Now go build some million-dollar agents!**

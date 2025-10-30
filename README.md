# Tune Agent Builder - Casino Email Campaign System

A comprehensive system for building AI-powered outbound email campaigns for casino energy optimization.

## 📁 Project Structure

```
Tune Agent Builder/
│
├── 📄 worldclass_email_generator.py   # Main email generation script
├── 📄 api_server.py                   # FastAPI server for API access
├── 📄 requirements.txt                # Python dependencies
├── 📄 .env                           # Environment variables (API keys)
├── 📄 config.example.json            # Example configuration
│
├── 📂 agents/                        # AI agent configurations
│   └── casino_agent.json            # Casino-specific agent definition
│
├── 📂 pdf_lead_magnets/             # PDF lead magnet system
│   ├── pdf_generator.py            # PDF creation engine
│   ├── templates/                  # PDF templates and assets
│   └── generated/                  # Generated PDF outputs
│
├── 📂 outputs/                      # All generated outputs
│   ├── casino_analysis_*.csv       # Casino analysis results
│   ├── casino_prospect_list.*      # Prospect lists
│   └── worldclass_casino_emails_*  # Generated email sequences
│
├── 📂 scripts/                      # Test/demo/batch scripts
│   ├── batch_analyze_casinos.py   # Batch casino analysis
│   ├── quick_email_demo.py        # Quick email generation demo
│   ├── test_pdf_generator.py      # Test PDF generation
│   └── ...                        # Other utility scripts
│
├── 📂 src/                         # Core source modules
│   ├── agent_builder_system.py    # Agent building logic
│   ├── prospect_intelligence.py   # Prospect analysis
│   ├── clay_integration.py        # Clay webhook integration
│   ├── database.py                # Database operations
│   └── ...                       # Other core modules
│
└── 📂 docs/                        # Documentation
    ├── START_HERE.md              # Getting started guide
    ├── README_V2.md               # Extended documentation
    └── ...                       # Project documentation

```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file with your API keys:

```bash
CLAUDE_API_KEY=your_api_key_here
```

### 3. Generate Emails

Run the main email generator:

```bash
python3 worldclass_email_generator.py
```

This will:
- Load casino analysis data from `outputs/`
- Generate 4 persona-specific email sequences (CFO, Operations, Facilities, ESG)
- Create personalized PDF lead magnets
- Send data to Clay webhook
- Export results to `outputs/`

### 4. Test PDF Generation

```bash
python3 scripts/test_pdf_generator.py
```

Generated PDFs will be saved to `pdf_lead_magnets/generated/`

## 📧 Email System Features

### 4-Persona Email Sequences

1. **CFO/Financial** - Focus on EBITDA, IRR, margin improvement
2. **Operations** - Focus on zero downtime, operational simplicity
3. **Facilities** - Focus on technical credibility, power quality
4. **ESG** - Focus on carbon reduction, board reporting

### PDF Lead Magnets

Each casino receives a personalized 6-page cost savings analysis PDF:
- Executive summary
- Demand charges breakdown with charts
- ROI projections and 5-year savings
- Verified case study results
- Technical explanation
- Next steps (pilot offer)

**PDF Hosting:**
- PDFs are automatically generated during email creation
- Served via FastAPI server at `http://localhost:8000/pdf/{filename}`
- No authentication required (public lead magnets)
- See `docs/PDF_HOSTING_GUIDE.md` for deployment options

### Email Flow

- **Email 1**: Offer PDF lead magnet
- **Email 2**: Deliver PDF link + education
- **Email 3**: Root cause explanation
- **Email 4**: Solution + 5% guarantee
- **Email 5**: 30-day pilot offer

## 🔧 Key Scripts

### Main Production Scripts

- `worldclass_email_generator.py` - Main email generation system
- `api_server.py` - REST API server for programmatic access

### Utility Scripts (in `scripts/`)

- `batch_analyze_casinos.py` - Analyze multiple casinos at once
- `test_pdf_generator.py` - Test PDF generation for single casino
- `quick_email_demo.py` - Quick demo of email generation
- `build_casino_agent.py` - Build casino agent configuration

## 📊 Output Files

All outputs are saved to the `outputs/` folder:

- `casino_analysis_*.csv` - Casino analysis with financial projections
- `casino_prospect_list.*` - Filtered prospect lists
- `worldclass_casino_emails_*.csv` - Generated email sequences

## 📚 Documentation

See the `docs/` folder for detailed documentation:

- `docs/START_HERE.md` - Comprehensive getting started guide
- `docs/README_V2.md` - Extended feature documentation
- `docs/WORK_COMPLETE_SUMMARY.md` - Implementation summary

## 🎯 Key Features

- **4 Persona-Specific Sequences** - Tailored messaging for each buyer persona
- **PDF Lead Magnets** - Automatically generated personalized cost analysis
- **Verified Case Study** - Only ONE verified case study (Vegas casino, 8.59% kW reduction)
- **5% Savings Guarantee** - 50,000+ installations, never below 5%, full refund
- **Clay Integration** - Automatic webhook delivery for automation
- **Conversational Tone** - Sounds like helpful salesperson, not a robot

## 🔐 Environment Variables

Required in `.env`:

```bash
CLAUDE_API_KEY=your_anthropic_api_key
```

Optional:

```bash
CLAY_WEBHOOK_URL=your_clay_webhook_url
PDF_BASE_URL=http://localhost:8000  # For production, set to your deployed URL
```

**For Railway/Render deployment:**
```bash
PDF_BASE_URL=https://your-app-name.railway.app  # or .onrender.com
```

## 📝 Development Notes

### Adding New Personas

Edit `worldclass_email_generator.py` and add new `generate_[persona]_sequence()` function following existing pattern.

### Customizing PDFs

Edit `pdf_lead_magnets/pdf_generator.py` to customize:
- Brand colors (search for `HexColor`)
- Logo (add to `pdf_lead_magnets/templates/`)
- Content sections

### Modifying Output Location

Update output paths in `worldclass_email_generator.py`:

```python
output_dir = "outputs/"  # Change this line
```

## 🤝 Support

For issues or questions, refer to documentation in `docs/` folder.

## 📜 License

Proprietary - Tune Energy Optimization Campaign System

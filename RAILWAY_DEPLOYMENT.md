# Railway Deployment Guide

## Overview

This guide will help you deploy the Tune Agent Builder API to Railway for 24/7 PDF hosting.

Once deployed, your PDFs will be accessible at:
```
https://your-app-name.railway.app/pdf/{filename}
```

## Prerequisites

✅ Railway account (you have this)
✅ Railway CLI installed (you have this)

## Step-by-Step Deployment

### Step 1: Login to Railway

```bash
cd "/Users/ryanburt/Orion - Tune /Tune Agent Builder"
railway login
```

This will open your browser for authentication.

### Step 2: Initialize Railway Project

```bash
railway init
```

You'll be prompted:
- **Project name**: Enter something like `tune-agent-builder` or `tune-pdf-hosting`
- **Start from scratch**: Yes

### Step 3: Link to Railway Project

```bash
railway link
```

Select the project you just created.

### Step 4: Set Environment Variables

Set your API key in Railway:

```bash
railway variables set CLAUDE_API_KEY=your_actual_api_key_here
```

You can also set this in the Railway dashboard under your project's Variables tab.

**Important Environment Variables:**

```bash
# Required
railway variables set CLAUDE_API_KEY=your_anthropic_api_key

# Optional - Railway will provide PORT automatically
# PDF_BASE_URL will be set after first deployment
```

### Step 5: Deploy to Railway

```bash
railway up
```

This will:
1. Upload your code to Railway
2. Install dependencies from requirements.txt
3. Start the API server
4. Give you a deployment URL

### Step 6: Get Your Deployment URL

After deployment, get your public URL:

```bash
railway domain
```

If you don't have a domain yet, create one:

```bash
railway domain create
```

This will give you something like: `tune-agent-builder.up.railway.app`

### Step 7: Set PDF_BASE_URL

Now set the PDF base URL to your Railway URL:

```bash
railway variables set PDF_BASE_URL=https://your-app-name.up.railway.app
```

**Or in Railway Dashboard:**
1. Go to https://railway.app
2. Select your project
3. Go to "Variables" tab
4. Add `PDF_BASE_URL` with value: `https://your-app-name.up.railway.app`

### Step 8: Test Your Deployment

Test the health endpoint:

```bash
curl https://your-app-name.up.railway.app/api/health
```

You should see:
```json
{
  "status": "healthy",
  "agents_loaded": [],
  "database_connected": true,
  "timestamp": "2025-10-30T..."
}
```

## Using Railway Deployment

### Generate Emails with Railway URLs

Once deployed, run your email generator locally with the Railway URL:

1. **Update your local .env** (optional, for testing):
```bash
PDF_BASE_URL=https://your-app-name.up.railway.app
```

2. **Generate emails**:
```bash
python3 worldclass_email_generator.py
```

Now PDFs will be uploaded to Railway and emails will contain links like:
```
https://your-app-name.up.railway.app/pdf/bellagio_las_vegas_cost_analysis_20251030.pdf
```

### Upload PDFs to Railway

**Important:** Railway deployments have ephemeral file systems, meaning PDFs generated locally won't automatically appear on Railway.

**Two Approaches:**

#### Approach 1: Generate PDFs on Railway (Recommended)

Run the email generator script on Railway:

```bash
railway run python3 worldclass_email_generator.py
```

This generates PDFs directly on the Railway server.

#### Approach 2: Use Cloud Storage (AWS S3)

For production, store PDFs in S3 instead of Railway's file system (see AWS S3 section below).

## Railway Commands Reference

```bash
# View logs
railway logs

# View current variables
railway variables

# Open Railway dashboard
railway open

# SSH into your Railway deployment
railway shell

# Run a command on Railway
railway run python3 worldclass_email_generator.py

# Redeploy
railway up

# Check status
railway status
```

## Important Notes About Railway

### File System (Important!)

Railway uses **ephemeral storage**, meaning:
- Files uploaded during deployment persist
- Files created at runtime (like PDFs) are lost on redeploy
- PDFs generated locally won't appear on Railway

**Solutions:**
1. Generate PDFs on Railway using `railway run`
2. Use AWS S3 for persistent storage (recommended for production)
3. Use Railway volumes (if you have Pro plan)

### Costs

**Railway Pricing:**
- **Hobby Plan**: $5/month
  - 500 hours runtime
  - $0.000231/GB-hour memory
  - Perfect for this use case

- **Free Trial**: $5 credit to start

**Estimated Cost for This App:**
- ~$5-10/month for 24/7 hosting
- Very affordable for always-on PDF hosting

### Scaling Considerations

For production with many PDFs, consider:

1. **AWS S3 Integration** (best for scale):
   - Store PDFs in S3 instead of Railway
   - Serve via CloudFront CDN
   - See AWS S3 section below

2. **Railway Volumes** (Pro plan):
   - Persistent storage on Railway
   - Requires Pro plan ($20/month)

## AWS S3 Alternative (For Production Scale)

If you generate many PDFs, use S3 for storage:

### Benefits
- Persistent storage (PDFs never lost)
- Extremely cheap (~$0.023/GB/month)
- Scalable to millions of PDFs
- CDN integration available

### Setup

1. **Install boto3**:
```bash
pip install boto3
echo "boto3==1.34.0" >> requirements.txt
```

2. **Set AWS credentials in Railway**:
```bash
railway variables set AWS_ACCESS_KEY_ID=your_key
railway variables set AWS_SECRET_ACCESS_KEY=your_secret
railway variables set AWS_S3_BUCKET=tune-casino-pdfs
railway variables set AWS_REGION=us-east-1
```

3. **Modify PDF generator to upload to S3** (code provided in docs/PDF_HOSTING_GUIDE.md)

## Troubleshooting

### Deployment Failed

```bash
railway logs
```

Check for errors like:
- Missing dependencies in requirements.txt
- Import errors
- Environment variables not set

### PDFs Not Accessible

1. Check PDF exists on Railway:
```bash
railway run ls pdf_lead_magnets/generated/
```

2. Check environment variables:
```bash
railway variables
```

3. Verify PDF_BASE_URL is set correctly

### Import Errors

If you see "ModuleNotFoundError", ensure:
- All dependencies in requirements.txt
- src/ folder structure is correct
- Imports use `from src.module_name`

### Database Connection Issues

Railway automatically provides a PostgreSQL database. If you get connection errors:

```bash
railway run python3 -c "from src.database_async import TuneDatabaseAsync; import asyncio; asyncio.run(TuneDatabaseAsync().init_db())"
```

## Local Development vs Railway

### Local Development
```bash
# Start server locally
uvicorn api_server:app --reload --port 8000

# Generate emails
python3 worldclass_email_generator.py

# PDFs at: http://localhost:8000/pdf/{filename}
```

### Railway Production
```bash
# Generate on Railway
railway run python3 worldclass_email_generator.py

# PDFs at: https://your-app.up.railway.app/pdf/{filename}
```

## Next Steps After Deployment

1. **Test the deployment**:
   - Visit https://your-app.up.railway.app/docs (FastAPI docs)
   - Test health endpoint
   - Generate a test PDF

2. **Update Clay webhooks** with Railway URL

3. **Monitor logs**:
   ```bash
   railway logs --follow
   ```

4. **Set up alerts** in Railway dashboard

## MCP Server Clarification

**You asked about MCP server** - this is different from Railway deployment:

- **MCP (Model Context Protocol)**: Local tool that gives Claude Code access to resources
- **Railway Deployment**: Hosting your API server in the cloud

For PDF hosting, you want **Railway deployment** (which we just set up), not an MCP server.

MCP servers are for things like:
- Giving Claude access to your database locally
- Connecting Claude to external APIs during development
- Not needed for hosting PDFs

## Quick Deployment Commands

Once everything is set up, deploying updates is easy:

```bash
# Make your code changes, then:
cd "/Users/ryanburt/Orion - Tune /Tune Agent Builder"
railway up
```

That's it! Railway will redeploy automatically.

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Railway Status: https://status.railway.app

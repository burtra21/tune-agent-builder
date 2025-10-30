#!/bin/bash

# Railway Deployment Script for Tune Agent Builder
# Run this script to deploy your API server to Railway

set -e  # Exit on error

echo "============================================================"
echo "RAILWAY DEPLOYMENT - Tune Agent Builder"
echo "============================================================"
echo ""

# Change to project directory
cd "/Users/ryanburt/Orion - Tune /Tune Agent Builder"

# Step 1: Login to Railway
echo "Step 1: Logging into Railway..."
echo "(This will open your browser for authentication)"
railway login

if [ $? -ne 0 ]; then
    echo "❌ Login failed. Please try again."
    exit 1
fi

echo "✅ Successfully logged in to Railway"
echo ""

# Step 2: Check if project exists or initialize new one
echo "Step 2: Checking for existing Railway project..."

if railway status > /dev/null 2>&1; then
    echo "✅ Existing Railway project found"
    railway status
else
    echo "No existing project found. Creating new Railway project..."
    railway init
    echo "✅ New Railway project created"
fi

echo ""

# Step 3: Set environment variables
echo "Step 3: Setting environment variables..."

# Read Claude API key from .env file
if [ -f ".env" ]; then
    CLAUDE_API_KEY=$(grep CLAUDE_API_KEY .env | cut -d '=' -f2 | tr -d '"' | tr -d "'")
    if [ ! -z "$CLAUDE_API_KEY" ]; then
        railway variables set CLAUDE_API_KEY="$CLAUDE_API_KEY"
        echo "✅ CLAUDE_API_KEY set from .env file"
    else
        echo "⚠️  CLAUDE_API_KEY not found in .env file"
        echo "Please set it manually: railway variables set CLAUDE_API_KEY=your_key_here"
    fi
else
    echo "⚠️  .env file not found"
    echo "Please set manually: railway variables set CLAUDE_API_KEY=your_key_here"
fi

echo ""

# Step 4: Deploy to Railway
echo "Step 4: Deploying to Railway..."
echo "(This may take a few minutes...)"
railway up

if [ $? -ne 0 ]; then
    echo "❌ Deployment failed. Check the logs above."
    exit 1
fi

echo "✅ Successfully deployed to Railway!"
echo ""

# Step 5: Get or create domain
echo "Step 5: Setting up public domain..."

# Try to get existing domain
DOMAIN=$(railway domain 2>&1 | grep -o 'https://[^ ]*' || echo "")

if [ -z "$DOMAIN" ]; then
    echo "No domain found. Creating new domain..."
    railway domain
    DOMAIN=$(railway domain 2>&1 | grep -o 'https://[^ ]*' || echo "")
fi

echo "✅ Public domain: $DOMAIN"
echo ""

# Step 6: Set PDF_BASE_URL
if [ ! -z "$DOMAIN" ]; then
    echo "Step 6: Setting PDF_BASE_URL..."
    railway variables set PDF_BASE_URL="$DOMAIN"
    echo "✅ PDF_BASE_URL set to: $DOMAIN"
else
    echo "⚠️  Could not automatically set PDF_BASE_URL"
    echo "Please run: railway variables set PDF_BASE_URL=https://your-app.up.railway.app"
fi

echo ""
echo "============================================================"
echo "DEPLOYMENT COMPLETE! 🎉"
echo "============================================================"
echo ""
echo "Your API is now live at: $DOMAIN"
echo ""
echo "Test your deployment:"
echo "  curl $DOMAIN/api/health"
echo ""
echo "PDFs will be accessible at:"
echo "  $DOMAIN/pdf/{filename}"
echo ""
echo "View logs:"
echo "  railway logs"
echo ""
echo "View in browser:"
echo "  railway open"
echo ""
echo "Next steps:"
echo "1. Test the health endpoint (command above)"
echo "2. Generate PDFs with: railway run python3 worldclass_email_generator.py"
echo "3. Or run locally with PDF_BASE_URL=$DOMAIN python3 worldclass_email_generator.py"
echo ""

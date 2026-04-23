#!/bin/bash
# Railway Deployment Quick Start Script

echo "🚀 TridentWear Railway Deployment"
echo "=================================="

# Check prerequisites
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Install from https://git-scm.com"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "⚠️  npm not found. Install from https://nodejs.org"
    echo "Will still proceed with Railway deployment..."
fi

echo ""
echo "📋 STEP 1: Initialize Git Repository"
echo "======================================="
git init
git add .
git commit -m "Initial TridentWear commit for Railway deployment"
git branch -M main

echo ""
echo "📋 STEP 2: Add GitHub Remote"
echo "============================="
read -p "Enter your GitHub repository URL (e.g., https://github.com/username/TridentWear.git): " GITHUB_URL

if [ -z "$GITHUB_URL" ]; then
    echo "❌ GitHub URL cannot be empty"
    exit 1
fi

git remote add origin "$GITHUB_URL"
git push -u origin main

echo ""
echo "📋 STEP 3: Install Railway CLI (Optional)"
echo "=========================================="
read -p "Install Railway CLI? (y/n): " INSTALL_RAILWAY

if [ "$INSTALL_RAILWAY" = "y" ]; then
    npm install -g @railway/cli
    railway login
    railway init
    echo "✅ Railway CLI initialized"
fi

echo ""
echo "✅ DEPLOYMENT READY!"
echo ""
echo "Next steps:"
echo "==========="
echo "1. Go to https://railway.app/dashboard"
echo "2. Click 'New Project' → 'Deploy from GitHub'"
echo "3. Select your TridentWear repository"
echo "4. Railway will auto-detect Dockerfile and deploy"
echo "5. Set environment variables in Railway dashboard:"
echo "   - TRIDENT_JWT_SECRET=your-secret-key"
echo "   - ENVIRONMENT=production"
echo ""
echo "For detailed guide, see: DEPLOY.md"

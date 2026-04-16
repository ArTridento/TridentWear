@echo off
REM Railway Deployment Quick Start Script for Windows

echo 🚀 TridentWear Railway Deployment
echo ==================================

REM Check if Git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git is not installed. Install from https://git-scm.com
    exit /b 1
)

echo.
echo 📋 STEP 1: Initialize Git Repository
echo ======================================
git init
git add .
git commit -m "Initial TridentWear commit for Railway deployment"
git branch -M main

echo.
echo 📋 STEP 2: Add GitHub Remote
echo =============================
set /p GITHUB_URL="Enter your GitHub repository URL (e.g., https://github.com/username/TridentWear.git): "

if "%GITHUB_URL%"=="" (
    echo ❌ GitHub URL cannot be empty
    exit /b 1
)

git remote add origin %GITHUB_URL%
git push -u origin main

echo.
echo 📋 STEP 3: Install Railway CLI (Optional)
echo ==========================================
set /p INSTALL_RAILWAY="Install Railway CLI? (y/n): "

if /i "%INSTALL_RAILWAY%"=="y" (
    npm install -g @railway/cli
    railway login
    railway init
    echo ✅ Railway CLI initialized
)

echo.
echo ✅ DEPLOYMENT READY!
echo.
echo Next steps:
echo ===========
echo 1. Go to https://railway.app/dashboard
echo 2. Click 'New Project' ^→ 'Deploy from GitHub'
echo 3. Select your TridentWear repository
echo 4. Railway will auto-detect Dockerfile and deploy
echo 5. Set environment variables in Railway dashboard:
echo    - TRIDENT_JWT_SECRET=your-secret-key
echo    - ENVIRONMENT=production
echo.
echo For detailed guide, see: DEPLOY.md
pause

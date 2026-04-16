📋 RAILWAY DEPLOYMENT CHECKLIST FOR TRIDENTWEAR
================================================

🟢 DONE - Files Created:
  ✅ Dockerfile - Container configuration for backend
  ✅ .dockerignore - Files to exclude from Docker build
  ✅ railway.json - Railway deployment configuration
  ✅ .env.example - Environment variables template
  ✅ DEPLOY.md - Detailed deployment guide
  ✅ deploy.sh - Linux/Mac deployment script
  ✅ deploy.bat - Windows deployment script
  ✅ config_production.py - Production config helper

🔴 TO DO - Deployment Steps:

STEP 1: Prepare GitHub Repository
──────────────────────────────────
□ Create a new GitHub repository
□ Clone it locally (or use existing)
□ Copy your TridentWear code into it
□ Run: git add .
□ Run: git commit -m "Initial TridentWear deployment"
□ Run: git push -u origin main
□ Verify code is on GitHub

STEP 2: Create Railway Account
──────────────────────────────
□ Go to https://railway.app
□ Sign up (free tier available)
□ Verify email

STEP 3: Deploy to Railway (Easiest Way)
────────────────────────────────────────
□ Go to https://railway.app/dashboard
□ Click "New Project" → "Deploy from GitHub repo"
□ Select your TridentWear repository
□ Railway auto-detects Dockerfile ✨
□ Wait for build and deployment (5-10 mins)

STEP 4: Configure Environment Variables
────────────────────────────────────────
□ In Railway Dashboard, go to your project
□ Click "Variables" tab
□ Add these variables:
   
   TRIDENT_JWT_SECRET = [generate random: openssl rand -hex 32]
   ENVIRONMENT = production
   TRIDENT_SESSION_SECRET = [generate random: openssl rand -hex 16]

□ Save variables
□ Railway auto-redeploys

STEP 5: Test Backend
────────────────────
□ Find your Railway domain in Dashboard
□ It will be: https://tridentwear-prod-xxxx.railway.app
□ Test API: https://tridentwear-prod-xxxx.railway.app/api/products
□ Should return JSON list of products

STEP 6: Update Frontend API
───────────────────────────
□ Update [frontend/js/shared/api.js](frontend/js/shared/api.js)
□ Change: const API_BASE = "https://your-railway-domain.railway.app";
□ (Or it auto-detects if frontend on same domain)

STEP 7: Deploy Frontend (Choose One)
─────────────────────────────────────

OPTION A: Vercel (Recommended)
  □ Push frontend folder to GitHub
  □ Go to https://vercel.com
  □ Import GitHub repository
  □ Deploy (1 click!)
  □ Update API_BASE to point to Railway backend

OPTION B: Netlify
  □ Go to https://netlify.com
  □ Drag & drop frontend folder
  □ Deploy
  □ Update API_BASE in settings

OPTION C: Railway (Same Service)
  □ In railway.json, add frontend static mounting
  □ Deploy frontend with backend

STEP 8: Test Full Application
──────────────────────────────
□ Go to your frontend domain
□ Try to browse products
□ Try to login/register
□ Add to cart
□ Complete checkout
□ Check admin panel

STEP 9: Production Setup
────────────────────────
□ Set custom domain (Railway Settings → Domain)
□ Enable HTTPS (automatic with Railway)
□ Configure backups for database
□ Set up monitoring
□ Add UptimeRobot for health checks

🎯 QUICK REFERENCE COMMANDS:

# First time setup
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/TridentWear.git
git push -u origin main

# Using Railway CLI
npm install -g @railway/cli
railway login
railway init
railway variables set TRIDENT_JWT_SECRET=your-key-here
railway up

# Generate secrets (Linux/Mac)
openssl rand -hex 32   # For JWT_SECRET
openssl rand -hex 16   # For SESSION_SECRET

# Generate secrets (Windows PowerShell)
[System.Convert]::ToHexString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))

🌐 DEPLOYMENT URLS AFTER DEPLOYMENT:

Backend API: https://your-project-xxxx.railway.app
Admin API Docs: https://your-project-xxxx.railway.app/docs (disabled by default)
Frontend: https://your-domain.vercel.app (or your Netlify domain)

📱 MOBILE/DEVELOPMENT TESTING:

To test on mobile from Railway:
1. Use your Railway URL instead of localhost
2. Update frontend API_BASE to Railway domain
3. Test all flows on mobile device

🆘 TROUBLESHOOTING:

Problem: Build fails
Solution: Check railway logs → `railway logs`

Problem: 502 Bad Gateway
Solution: Check startup command, ensure PORT env var is used

Problem: Database not persisting
Solution: Railway uses ephemeral storage → use PostgreSQL/MongoDB

Problem: Files not persisting
Solution: Use AWS S3 or Cloudinary for uploads

Problem: CORS errors
Solution: Backend already has CORS enabled for all origins

❓ HELP & SUPPORT:

- Railway Docs: https://docs.railway.app
- FastAPI Docs: https://fastapi.tiangolo.com
- Discord Communities: railway.app/discord, fastapi.tiangolo.com
- Email Support: Railway offers support on paid plans

✨ NEXT OPTIMIZATION STEPS:

After deployment is working:
□ Add PostgreSQL database
□ Move uploads to AWS S3/Cloudinary
□ Set up CI/CD pipeline
□ Add performance monitoring
□ Configure error tracking (Sentry)
□ Set up automated backups
□ Enable caching headers
□ Optimize images for web

═══════════════════════════════════════════════════════════════

Good luck with your deployment! 🚀

Questions? Check DEPLOY.md for detailed guide.

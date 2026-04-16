# 🚀 Railway Deployment Guide - TridentWear

## Prerequisites
- Railway.app account (free signup at https://railway.app)
- GitHub account with your code pushed
- Railway CLI (optional but recommended)

---

## **Method 1: Deploy via Railway Dashboard (Easiest)**

### Step 1: Push Code to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/TridentWear.git
git push -u origin main
```

### Step 2: Connect to Railway
1. Go to https://railway.app/dashboard
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your **TridentWear** repository
4. Railway will auto-detect the Dockerfile and deploy

### Step 3: Set Environment Variables
1. In Railway Dashboard, go to your project
2. Click **"Variables"** tab
3. Add these variables:
   ```
   TRIDENT_JWT_SECRET = [generate a random secret key]
   ENVIRONMENT = production
   PORT = 8000
   ```

4. Click **"Deploy"**

---

## **Method 2: Deploy via CLI (Advanced)**

### Step 1: Install Railway CLI
```bash
npm install -g @railway/cli
```

### Step 2: Login
```bash
railway login
```

### Step 3: Initialize Project
```bash
railway init
```
- Choose "Empty Project"
- Give it a name: `tridentwear`

### Step 4: Set Variables
```bash
railway variables set TRIDENT_JWT_SECRET=your-secret-key-12345
railway variables set ENVIRONMENT=production
```

### Step 5: Deploy
```bash
railway up
```

---

## **After Deployment**

✅ Your backend will be live at: `https://your-project.railway.app`

### Configure Frontend API Calls
Update [frontend/js/shared/api.js](frontend/js/shared/api.js):

```javascript
// Change this:
const API_URL = "http://localhost:8000";

// To this:
const API_URL = "https://your-project.railway.app";
```

### Host Frontend (Choose One):

**Option A: Vercel (Recommended)**
1. Push frontend to separate GitHub repo
2. Go to vercel.com, connect GitHub
3. Deploy in 1 click

**Option B: Netlify**
1. Drag & drop `frontend` folder
2. Set custom domain

**Option C: Railway (Same Service)**
1. In railway.json, add static file serving
2. Keep both in same Railway project

---

## **Troubleshooting**

### Build Fails
- Check Railway logs: `railway logs`
- Ensure requirements.txt is at project root
- Verify Dockerfile path

### Cold Starts
- Use Railway's paid tier to avoid project sleep
- Or add UptimeRobot to ping endpoint every 5 mins

### Port Issues
- Railway automatically sets `PORT` env variable
- FastAPI uses this via `--port $PORT`

### Database/File Permissions
- Railway has ephemeral storage (files deleted on restart)
- **Solution**: Use PostgreSQL or MongoDB
- OR: Save uploads to cloud storage (AWS S3, Cloudinary)

---

## **Production Checklist**

- [ ] Change `TRIDENT_JWT_SECRET` to strong random key
- [ ] Set `ENVIRONMENT=production`
- [ ] Enable CORS for your domain
- [ ] Set up monitoring/alerts
- [ ] Configure database backup
- [ ] Use custom domain (Settings → Domain)

---

## **Performance Tips**

1. **Add Gunicorn for production**:
   ```bash
   pip install gunicorn
   ```
   Update railway.json:
   ```json
   "startCommand": "gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.app:app"
   ```

2. **Compress assets** in frontend
3. **Cache static files** with CDN
4. **Monitor performance** via Railway dashboard

---

## **Support**
- Railway Docs: https://docs.railway.app
- FastAPI Docs: https://fastapi.tiangolo.com
- Questions? Check Railway Discord: https://discord.gg/railway

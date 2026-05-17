# TridentWear — Deployment Guide

> For all platforms, the server is a FastAPI app served from `backend/`.
> The frontend is fully static HTML/JS/CSS served by FastAPI at the same origin.

---

## Prerequisites

- Python 3.11+
- Git
- A `.env` file with secrets (copy from `.env.example`)

Generate secrets:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Option 1 — Render.com (Recommended, Free Tier)

### Steps

1. Push repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service → Connect repo
3. Render auto-detects `render.yaml` — review and confirm
4. In **Environment** tab, set these secrets manually:
   - `TRIDENT_JWT_SECRET` (64-char hex)
   - `TRIDENT_SESSION_SECRET` (64-char hex)
   - `ALLOWED_ORIGINS` (e.g. `https://tridentwear.onrender.com`)
   - `RAZORPAY_KEY` + `RAZORPAY_SECRET` (from Razorpay dashboard)
   - `SMTP_*` variables (for order emails)
5. Add a **Disk** (1 GB) mounted at `/opt/render/project/src/db` for JSON DB persistence
6. Click **Deploy**

### Health check
```
https://your-app.onrender.com/health
```

---

## Option 2 — Railway.app

### Steps

1. Push repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Railway reads `railway.toml` and `Procfile` automatically
4. In **Variables** tab, add:
   - `TRIDENT_JWT_SECRET`
   - `TRIDENT_SESSION_SECRET`
   - `ALLOWED_ORIGINS`
   - `RAZORPAY_KEY` + `RAZORPAY_SECRET`
   - `SMTP_*`
5. For database persistence, add a **Volume** mounted at `/app/db`
6. Click **Deploy**

---

## Option 3 — VPS (Ubuntu 22.04 + Nginx + HTTPS)

### 1. Server Setup

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3.11 python3.11-venv python3-pip nginx certbot python3-certbot-nginx git -y
```

### 2. Clone and Install

```bash
git clone https://github.com/youruser/TridentWear.git /opt/tridentwear
cd /opt/tridentwear
python3.11 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### 3. Environment

```bash
cp .env.example .env
nano .env   # Fill in all REQUIRED values
```

### 4. Systemd Service

Create `/etc/systemd/system/tridentwear.service`:

```ini
[Unit]
Description=TridentWear FastAPI Server
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/tridentwear/backend
Environment="PATH=/opt/tridentwear/venv/bin"
EnvironmentFile=/opt/tridentwear/.env
ExecStart=/opt/tridentwear/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable tridentwear
sudo systemctl start tridentwear
sudo systemctl status tridentwear
```

### 5. Nginx Config

Create `/etc/nginx/sites-available/tridentwear`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        client_max_body_size 10M;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/tridentwear /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. HTTPS with Let's Encrypt

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
# Follow prompts — certbot auto-modifies Nginx config for HTTPS
sudo systemctl reload nginx
```

Auto-renewal:
```bash
sudo certbot renew --dry-run
# Certbot adds a cron job automatically
```

### 7. DB Persistence

The JSON database files live in `/opt/tridentwear/db/`.
**Take regular backups:**

```bash
# Add to crontab (crontab -e)
0 2 * * * cp -r /opt/tridentwear/db /opt/tridentwear/db_backup_$(date +\%F)
```

---

## Option 4 — Docker

### Build and Run

```bash
# Build
docker build -t tridentwear .

# Run (with env file)
docker run -d \
  --name tridentwear \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/db:/app/db \
  tridentwear
```

### Docker Compose

```bash
# Copy and fill .env
cp .env.example .env
nano .env

# Start
docker compose up -d

# Logs
docker compose logs -f

# Stop
docker compose down
```

---

## Static Assets in Production

All static files are served by FastAPI directly:

| URL Pattern | Served From |
|-------------|-------------|
| `/assets/*` | `frontend/assets/` |
| `/images/*` | `frontend/assets/images/` |
| `/components/*` | `frontend/components/` |
| All HTML pages | `frontend/pages/` via FastAPI routes |

No separate CDN or static server needed for basic deployment.
For high traffic, consider putting assets behind Cloudflare or an S3 bucket.

---

## Verifying Deployment

```bash
# Health check
curl https://yourdomain.com/health

# Products API
curl https://yourdomain.com/api/v1/products

# Frontend loads
curl -I https://yourdomain.com/
```

Expected: `HTTP/2 200` on all three.

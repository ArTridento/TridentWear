# TridentWear — Environment Variables Setup

## How to Set Up

```bash
# 1. Copy the template
cp .env.example .env

# 2. Generate secure secrets
python -c "import secrets; print(secrets.token_hex(32))"

# 3. Edit with your values
nano .env   # or use VS Code
```

---

## Required Variables

### 🔐 Security (MUST change before production)

| Variable | Description | How to Generate |
|----------|-------------|-----------------|
| `TRIDENT_JWT_SECRET` | Signs all auth tokens — **must be secret** | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `TRIDENT_SESSION_SECRET` | Signs server-side session cookies | Same as above |

> ⚠️ If `TRIDENT_JWT_SECRET` is not set, the app falls back to `trident-super-secret-key-12345`. **This is insecure.** Always set it in production.

### 🌐 CORS

| Variable | Description | Example |
|----------|-------------|---------|
| `ALLOWED_ORIGINS` | Comma-separated allowed origins | `https://tridentwear.in,https://www.tridentwear.in` |

> In development (unset): defaults to `*` (all origins allowed)  
> In production: **always set this** to your exact domain(s)

### 💳 Razorpay (for online payments)

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `RAZORPAY_KEY` | Public key (starts with `rzp_live_`) | [Razorpay Dashboard → API Keys](https://dashboard.razorpay.com/app/keys) |
| `RAZORPAY_SECRET` | Private key — **never expose to frontend** | Same dashboard |
| `RAZORPAY_WEBHOOK_SECRET` | Webhook signature verification | Dashboard → Webhooks |

> COD orders work without Razorpay keys. Keys are only needed for online payment flow.

---

## Optional Variables

### 📧 Email (SMTP)

| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_HOST` | SMTP server hostname | _(empty — emails skipped)_ |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | SMTP username / email | _(empty)_ |
| `SMTP_PASS` | SMTP password or App Password | _(empty)_ |

**Gmail setup:**
1. Enable 2-Step Verification on your Google account
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Generate an App Password for "Mail"
4. Use that 16-char password as `SMTP_PASS`

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=yourstore@gmail.com
SMTP_PASS=abcd efgh ijkl mnop
```

### 🗃️ Database

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_MODE` | `json` or `postgres` | `json` |
| `DATABASE_URL` | PostgreSQL connection URL | _(empty)_ |

> The default `json` mode uses files in the `db/` directory.  
> Use `postgres` for multi-server deployments (connect a PostgreSQL instance).

### ⚙️ OTP Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TRIDENT_OTP_PROVIDER` | `dev` | Set to `twilio` or `msg91` for SMS OTP |
| `TRIDENT_OTP_EXPIRY_MINUTES` | `5` | OTP validity window |
| `TRIDENT_OTP_RESEND_SECONDS` | `45` | Cooldown between OTP sends |
| `TRIDENT_OTP_MAX_ATTEMPTS` | `5` | Max wrong attempts before lockout |

---

## Platform-Specific Notes

### Render.com
- Set secrets in **Environment** tab of the service
- Do NOT add `DATABASE_URL` unless using PostgreSQL add-on
- `TRIDENT_JWT_SECRET` can use "Generate Value" for auto-generation

### Railway.app
- Set in **Variables** tab
- Use Railway's PostgreSQL plugin if switching to `DB_MODE=postgres`

### VPS
- Create `/opt/tridentwear/.env` and reference it in the systemd service via `EnvironmentFile=`
- File permissions: `chmod 600 /opt/tridentwear/.env`

---

## Security Rules

1. **Never commit `.env`** — it's in `.gitignore`
2. **Never log secrets** — the app uses structured logging that omits headers
3. **Rotate `TRIDENT_JWT_SECRET`** if you suspect compromise — all sessions will be invalidated
4. **Set `ALLOWED_ORIGINS`** explicitly in production to prevent CSRF via CORS

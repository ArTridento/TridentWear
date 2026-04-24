# 🚀 Quick Start Checklist - TridentWear Backend

## ⚡ 5-Minute Setup

### Step 1: Install PostgreSQL (5 min)
```bash
# Windows: https://www.postgresql.org/download/windows/
# macOS: brew install postgresql && brew services start postgresql
# Linux: sudo apt-get install postgresql

# Verify installation
psql --version
```

### Step 2: Create Database (2 min)
```bash
psql -U postgres

# In psql:
CREATE DATABASE tridentwear_db;
CREATE USER tridentwear_user WITH PASSWORD 'strong_password_123';
ALTER ROLE tridentwear_user SET client_encoding TO 'utf8';
ALTER ROLE tridentwear_user SET default_transaction_isolation TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE tridentwear_db TO tridentwear_user;
GRANT ALL ON SCHEMA public TO tridentwear_db TO tridentwear_user;
\q
```

### Step 3: Setup Backend (2 min)
```bash
cd backend

# Windows:
python -m venv venv
venv\Scripts\activate

# macOS/Linux:
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### Step 4: Configure Environment (2 min)
```bash
cp .env.example .env

# Edit .env (nano, VS Code, etc.)
nano .env
```

**Required in .env:**
```env
DATABASE_URL=postgresql://tridentwear_user:strong_password_123@localhost:5432/tridentwear_db
SECRET_KEY=<run: openssl rand -hex 32>
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=xxxxx
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Step 5: Start Server (1 min)
```bash
python main.py
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✅ Database tables initialized
```

---

## ✅ Verification Checklist

### Is the server running?
```bash
curl http://localhost:8000/health
```
Expected:
```json
{"status": "healthy", "version": "1.0.0"}
```

### Can you access Swagger UI?
Open in browser: `http://localhost:8000/api/docs`

### Run automated tests
```bash
python test_api.py
```

---

## 🔐 Security Configuration Checklist

- [ ] Changed DATABASE_URL password
- [ ] Generated SECRET_KEY with `openssl rand -hex 32`
- [ ] Added Razorpay credentials (test keys for development)
- [ ] Added Gmail SMTP credentials
- [ ] Set DEBUG=False (for production)
- [ ] Limited CORS_ORIGINS to your domain

---

## 📋 What's Included

### Backend Files (31 files total)

**Core Application:**
- `main.py` - FastAPI application
- `config.py` - Settings & environment configuration
- `database.py` - SQLAlchemy setup

**Models (Database):**
- `models/user.py` - User table with auth fields
- `models/product.py` - Product inventory
- `models/order.py` - Orders & OrderItems with payment tracking

**Schemas (Validation):**
- `schemas/user.py` - User request/response validation
- `schemas/product.py` - Product validation
- `schemas/order.py` - Order validation

**Routes (API Endpoints):**
- `routers/auth.py` - Register, Login, OTP verification
- `routers/products.py` - Product CRUD (admin), listing
- `routers/orders.py` - Order creation, listing
- `routers/payments.py` - Razorpay payment processing

**Services (Business Logic):**
- `services/auth_service.py` - User authentication
- `services/order_service.py` - Order processing with price validation
- `services/payment_service.py` - Razorpay integration & signature verification
- `services/email_service.py` - OTP and order confirmation emails

**Middleware (Security):**
- `middleware/security.py` - Security headers, CORS
- `middleware/rate_limit.py` - Rate limiting (5 req/min on auth)

**Utilities:**
- `utils/hashing.py` - Bcrypt password hashing
- `utils/token.py` - JWT token generation & verification
- `utils/otp.py` - OTP generation & verification

**Configuration & Testing:**
- `requirements.txt` - All dependencies
- `.env.example` - Environment template
- `README.md` - Full documentation (50KB)
- `ARCHITECTURE.md` - System design & security
- `QUICKSTART.md` - This file
- `postman_collection.json` - Postman test collection
- `test_api.py` - Automated testing script

---

## 🧪 Testing Workflow

### 1. Register User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123",
    "full_name": "John Doe",
    "phone": "9876543210"
  }'
```

### 2. Create Product (as admin)
```bash
curl -X POST http://localhost:8000/api/products \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "T-Shirt",
    "sku": "TSHIRT-001",
    "price": 499.99,
    "cost": 250,
    "stock": 100,
    "category": "Clothing"
  }'
```

### 3. Create Order
```bash
curl -X POST http://localhost:8000/api/orders \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [{"product_id": "UUID", "quantity": 1}],
    "shipping_name": "John Doe",
    "shipping_email": "john@example.com",
    "shipping_phone": "9876543210",
    "shipping_address": "123 Main St",
    "shipping_city": "Mumbai",
    "shipping_state": "Maharashtra",
    "shipping_postal_code": "400001"
  }'
```

### 4. Create Razorpay Order
```bash
curl -X POST http://localhost:8000/api/payments/create-order \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"order_id": "ORDER_UUID"}'
```

### 5. Verify Payment
```bash
curl -X POST http://localhost:8000/api/payments/verify \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "razorpay_order_id": "order_xxx",
    "razorpay_payment_id": "pay_xxx",
    "razorpay_signature": "signature_xxx"
  }'
```

**Full workflow takes ~2 minutes to test!**

---

## 🐛 Troubleshooting

### PostgreSQL Connection Error
```
ERROR: could not connect to server
```
**Fix:**
```bash
# Windows: Services → PostgreSQL → Start
# macOS: brew services start postgresql
# Linux: sudo service postgresql start
```

### Port 8000 Already in Use
```
Address already in use: ('0.0.0.0', 8000)
```
**Fix:**
```bash
# Use different port
python main.py --port 8001
```

### Import Errors
```
ModuleNotFoundError: No module named 'fastapi'
```
**Fix:**
```bash
# Make sure venv is activated and requirements installed
pip install -r requirements.txt
```

### Database Tables Not Created
```bash
# Manually create tables
python -c "from database import create_all_tables; create_all_tables()"
```

---

## 📚 API Endpoints Summary

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| **Authentication** | | | |
| POST | `/api/auth/register` | ❌ | Register new user |
| POST | `/api/auth/login` | ❌ | Login user |
| GET | `/api/auth/me` | ✅ | Get current user |
| **Products** | | | |
| GET | `/api/products` | ❌ | List all products |
| GET | `/api/products/{id}` | ❌ | Get product by ID |
| POST | `/api/products` | ✅🔒 | Create product (admin) |
| PUT | `/api/products/{id}` | ✅🔒 | Update product (admin) |
| DELETE | `/api/products/{id}` | ✅🔒 | Delete product (admin) |
| **Orders** | | | |
| POST | `/api/orders` | ✅ | Create order |
| GET | `/api/orders` | ✅ | List user orders |
| GET | `/api/orders/{id}` | ✅ | Get order details |
| POST | `/api/orders/{id}/cancel` | ✅ | Cancel order |
| **Payments** | | | |
| POST | `/api/payments/create-order` | ✅ | Create Razorpay order |
| POST | `/api/payments/verify` | ✅ | Verify payment |
| GET | `/api/payments/{id}/status` | ✅ | Get payment status |
| **Health** | | | |
| GET | `/health` | ❌ | Health check |

**Legend:** ✅ = Requires auth, 🔒 = Admin only

---

## 🔒 Security Features Implemented

✅ **Price Tampering Prevention**
- Backend-only price calculation
- Prices fetched from database, not frontend
- Locked prices stored with order

✅ **Payment Fraud Prevention**
- HMAC-SHA256 signature verification
- Razorpay webhook validation
- Payment marked PAID only after verification

✅ **Authentication Security**
- Bcrypt password hashing (12 rounds)
- JWT tokens with expiry
- Refresh token rotation
- OTP verification

✅ **Rate Limiting**
- 5 req/min on auth endpoints
- 30 req/min on API endpoints
- 100 req/min on read-only endpoints

✅ **Input Validation**
- Pydantic schemas on all endpoints
- Email validation
- Password complexity
- Type checking

✅ **HTTP Security**
- CORS restricted (no wildcard)
- Security headers (HSTS, CSP, X-Frame-Options)
- HTTPS-only in production

---

## 🚀 Next Steps

1. **Development:** Use test Razorpay keys
2. **Testing:** Run `python test_api.py`
3. **Integration:** Connect React frontend to API
4. **Production:** Switch to live keys, enable HTTPS

---

## 📞 Need Help?

- **Swagger UI:** http://localhost:8000/api/docs
- **Documentation:** See `README.md` (detailed setup guide)
- **Architecture:** See `ARCHITECTURE.md` (security & design)
- **FastAPI:** https://fastapi.tiangolo.com

---

**Your production-ready eCommerce backend is ready to go!** 🎉

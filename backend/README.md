# 🏪 TridentWear - Production-Ready eCommerce Backend

## 📋 Overview

**Complete, secure, production-grade eCommerce backend** built with:
- **FastAPI** - High-performance Python framework
- **PostgreSQL** - Robust relational database
- **SQLAlchemy ORM** - Type-safe database queries
- **JWT Authentication** - Secure token-based auth
- **Razorpay** - Real payment processing
- **Email Service** - OTP and order confirmations
- **Rate Limiting** - DDoS protection
- **Security Headers** - OWASP best practices

---

## 🔐 Security Features

✅ **Never trust frontend prices** - Backend calculates all totals
✅ **HMAC-SHA256 payment verification** - Prevents payment tampering
✅ **Bcrypt password hashing** - Industry-standard security
✅ **JWT with refresh tokens** - Secure authentication
✅ **Rate limiting** - 5 requests/minute on auth endpoints
✅ **CORS configuration** - No wildcard origins
✅ **Input validation** - Pydantic schemas on all endpoints
✅ **Security headers** - XSS, CSRF, clickjacking protection
✅ **Environment variables** - No hardcoded secrets
✅ **SQL injection prevention** - SQLAlchemy parameterized queries

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **PostgreSQL 12+**
- **pip** (Python package manager)

### Step 1: Install PostgreSQL

#### **Windows**
1. Download from https://www.postgresql.org/download/windows/
2. Run the installer (postgresql-15.x-x64-exe)
3. Set password for `postgres` user
4. Port: 5432 (default)
5. Install pgAdmin (optional, for GUI)

#### **macOS**
```bash
brew install postgresql
brew services start postgresql
```

#### **Linux (Ubuntu/Debian)**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

---

### Step 2: Create Database

#### **Using psql (Command Line)**
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE tridentwear_db;
CREATE USER tridentwear_user WITH PASSWORD 'strong_password_123';
ALTER ROLE tridentwear_user SET client_encoding TO 'utf8';
ALTER ROLE tridentwear_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE tridentwear_user SET default_transaction_deferrable TO on;
ALTER ROLE tridentwear_user SET search_path TO public;
GRANT ALL PRIVILEGES ON DATABASE tridentwear_db TO tridentwear_user;
\c tridentwear_db
GRANT ALL ON SCHEMA public TO tridentwear_user;
\q
```

#### **Or Using pgAdmin (GUI)**
1. Right-click "Databases" → Create → Database
2. Name: `tridentwear_db`
3. Right-click "Login/Group Roles" → Create
4. Username: `tridentwear_user`
5. Password: (same as above)
6. Give privileges

---

### Step 3: Setup Backend

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your editor
```

---

### Step 4: Configure .env

```env
DATABASE_URL=postgresql://tridentwear_user:strong_password_123@localhost:5432/tridentwear_db

# Generate secret key with: openssl rand -hex 32
SECRET_KEY=abc123...xyz

RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=xxxxx
RAZORPAY_WEBHOOK_SECRET=xxxxx

SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

**For Razorpay credentials:**
1. Create account at https://razorpay.com
2. Go to Settings → API Keys
3. Copy Key ID and Key Secret
4. For testing: use test keys (start with `rzp_test_`)

**For Gmail SMTP:**
1. Enable 2FA on Gmail
2. Create App Password: https://myaccount.google.com/apppasswords
3. Use that password in `SMTP_PASSWORD`

---

### Step 5: Run Backend

```bash
# Still in backend directory with venv activated
python main.py

# Server will start on http://localhost:8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✅ Database tables initialized
```

---

## 📚 API Documentation

Once running, open:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health

---

## 🧪 Testing Guide

### Using Postman

1. Download Postman from https://www.postman.com
2. Import the collection (see examples below)
3. Set `{{base_url}}` to `http://localhost:8000`

### Using cURL

#### **1. Register User**
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

**Response:**
```json
{
  "status": "success",
  "message": "User registered successfully",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe"
  },
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

Save the `access_token` for authenticated requests.

---

#### **2. Login**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

---

#### **3. Create Product (Admin Only)**
```bash
curl -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Black T-Shirt",
    "description": "Premium cotton T-shirt",
    "sku": "TSHIRT-BLK-001",
    "price": 499.99,
    "cost": 250.00,
    "discount_percent": 10,
    "stock": 100,
    "category": "Clothing",
    "size": "M",
    "color": "Black",
    "material": "100% Cotton",
    "is_active": true
  }'
```

---

#### **4. Get All Products**
```bash
curl -X GET "http://localhost:8000/api/products?skip=0&limit=10" \
  -H "Content-Type: application/json"
```

---

#### **5. Create Order**

```bash
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "items": [
      {
        "product_id": "550e8400-e29b-41d4-a716-446655440000",
        "quantity": 2,
        "size": "M",
        "color": "Black"
      }
    ],
    "shipping_name": "John Doe",
    "shipping_email": "john@example.com",
    "shipping_phone": "9876543210",
    "shipping_address": "123 Main Street",
    "shipping_city": "Mumbai",
    "shipping_state": "Maharashtra",
    "shipping_postal_code": "400001",
    "shipping_country": "India"
  }'
```

**Response includes:**
- `order_id` - Save this
- `subtotal`, `tax`, `shipping_cost`, `total` - All calculated on backend
- `razorpay_order_id` - For payment

---

#### **6. Create Razorpay Payment Order**

```bash
curl -X POST http://localhost:8000/api/payments/create-order \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "order_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Response:**
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "razorpay_order_id": "order_1234567890",
  "amount": 2750000,
  "currency": "INR"
}
```

Use `razorpay_order_id` with Razorpay Checkout.

---

#### **7. Verify Payment**

After Razorpay payment success:

```bash
curl -X POST http://localhost:8000/api/payments/verify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "razorpay_order_id": "order_1234567890",
    "razorpay_payment_id": "pay_1234567890",
    "razorpay_signature": "9ef4dffbfd84f1318f6739a3ce19f9d85851857ae648f114332d8401e0949a"
  }'
```

**CRITICAL:** Signature is verified using HMAC-SHA256. Payment tampering is impossible.

---

#### **8. Get User Orders**
```bash
curl -X GET "http://localhost:8000/api/orders?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

#### **9. Get Order Details**
```bash
curl -X GET http://localhost:8000/api/orders/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🧪 Payment Testing (Razorpay Test Mode)

### Using Razorpay Test Credentials

1. Create Razorpay account (free): https://razorpay.com
2. Go to Settings → API Keys
3. Use **Test Keys** (start with `rzp_test_`)
4. Add to .env:
   ```env
   RAZORPAY_KEY_ID=rzp_test_xxxxx
   RAZORPAY_KEY_SECRET=xxxxx
   ```

### Test Payment Cards

- **Success**: `4111 1111 1111 1111` | CVV: `123` | Date: `12/25`
- **Failure**: `4000 0000 0000 0002` | CVV: `123` | Date: `12/25`

---

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(255) NOT NULL,
  is_verified BOOLEAN DEFAULT FALSE,
  is_admin BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Products Table
```sql
CREATE TABLE products (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  sku VARCHAR(100) UNIQUE NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  cost DECIMAL(10,2) NOT NULL,
  stock INTEGER DEFAULT 0,
  discount_percent DECIMAL(5,2) DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Orders Table
```sql
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  user_id UUID FOREIGN KEY NOT NULL,
  subtotal DECIMAL(10,2) NOT NULL,
  tax DECIMAL(10,2) NOT NULL,
  shipping_cost DECIMAL(10,2) NOT NULL,
  total DECIMAL(10,2) NOT NULL,
  payment_status VARCHAR(50) DEFAULT 'PENDING',
  razorpay_order_id VARCHAR(100) UNIQUE,
  razorpay_payment_id VARCHAR(100) UNIQUE,
  razorpay_signature VARCHAR(255),
  status VARCHAR(50) DEFAULT 'PENDING',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Order Items Table
```sql
CREATE TABLE order_items (
  id UUID PRIMARY KEY,
  order_id UUID FOREIGN KEY NOT NULL,
  product_id UUID FOREIGN KEY NOT NULL,
  quantity INTEGER NOT NULL,
  price_per_unit DECIMAL(10,2) NOT NULL,
  total DECIMAL(10,2) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔒 Security Best Practices Implemented

### 1. **Price Tampering Prevention**
- ❌ Never accepts price from frontend
- ✅ Fetches current price from database
- ✅ Calculates all totals on backend
- ✅ Stores locked prices with order

### 2. **Payment Fraud Prevention**
- ✅ HMAC-SHA256 signature verification
- ✅ Razorpay webhook validation
- ✅ Payment marked PAID only after verification
- ✅ Stock reduced only after confirmed payment

### 3. **Authentication**
- ✅ Bcrypt password hashing (12 rounds)
- ✅ JWT tokens with expiry
- ✅ Refresh token rotation
- ✅ Secure OTP system

### 4. **Rate Limiting**
- ✅ 5 requests/minute on auth endpoints
- ✅ 30 requests/minute on API endpoints
- ✅ 100 requests/minute on read-only endpoints

### 5. **Input Validation**
- ✅ Pydantic schemas on all endpoints
- ✅ Email validation
- ✅ Password complexity requirements
- ✅ Type checking

### 6. **Database Security**
- ✅ UUID primary keys (not sequential)
- ✅ Decimal types for money (not float)
- ✅ Parameterized queries (SQLAlchemy)
- ✅ Timestamps for audit trail

### 7. **HTTP Security**
- ✅ CORS restricted (no wildcard)
- ✅ Security headers on all responses
- ✅ HTTPS-only in production
- ✅ X-Frame-Options: DENY

---

## 📦 Deployment Checklist

### Before Production

- [ ] Change `DEBUG=False` in .env
- [ ] Generate new `SECRET_KEY` with `openssl rand -hex 32`
- [ ] Use Razorpay **LIVE keys** (not test)
- [ ] Update `CORS_ORIGINS` to your domain
- [ ] Set strong PostgreSQL password
- [ ] Enable HTTPS/SSL certificate
- [ ] Configure email with real SMTP
- [ ] Set up database backups
- [ ] Configure logging/monitoring

### Deployment Platforms

- **Railway.app** - Free PostgreSQL + Python hosting
- **Heroku** - Traditional PaaS (paid)
- **DigitalOcean** - Affordable VPS
- **AWS EC2** - Scalable infrastructure
- **Google Cloud Run** - Serverless (with managed PostgreSQL)

### Environment Variables (Production)

```env
DATABASE_URL=postgresql://user:pass@prod-db.example.com/tridentwear_db
SECRET_KEY=<generate-with-openssl>
DEBUG=False
RAZORPAY_KEY_ID=rzp_live_xxxxx
RAZORPAY_KEY_SECRET=xxxxx
CORS_ORIGINS=https://tridentwear.com,https://www.tridentwear.com
```

---

## 🐛 Troubleshooting

### Database Connection Error
```
ERROR: could not connect to server: Connection refused
```
**Solution:**
```bash
# Check if PostgreSQL is running
sudo service postgresql status
# Start it
sudo service postgresql start
```

### Port Already in Use
```
Address already in use: ('0.0.0.0', 8000)
```
**Solution:**
```bash
# Use different port
python main.py --port 8001

# Or kill process on port 8000
# macOS/Linux:
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
# Windows (PowerShell):
Get-NetTCPConnection -LocalPort 8000 | Stop-Process
```

### Razorpay Signature Mismatch
```
Payment verification failed: Invalid signature
```
**Solution:**
- Check `RAZORPAY_KEY_SECRET` matches dashboard
- Verify payment was created with correct order ID
- Ensure signature format is correct

### Email Not Sending
```
SMTPAuthenticationError
```
**Solution:**
- Use Gmail App Password (not regular password)
- Enable 2FA on Gmail
- Check SMTP credentials in .env

---

## 📞 Support

- FastAPI Docs: https://fastapi.tiangolo.com
- SQLAlchemy: https://docs.sqlalchemy.org
- PostgreSQL: https://www.postgresql.org/docs
- Razorpay: https://razorpay.com/developers

---

## 📄 License

This is a production-ready template. Modify as needed for your business.

---

**Built with ❤️ for secure, scalable eCommerce backends**

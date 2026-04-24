# TridentWear Backend - Architecture & Security Overview

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT (React/Web App)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        LOAD BALANCER                            │
│                  (Rate Limiting, SSL/TLS)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI APPLICATION                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Middleware Layer                                         │   │
│  │  - Security Headers (HSTS, CSP, X-Frame-Options)       │   │
│  │  - CORS Validation                                      │   │
│  │  - Rate Limiting (slowapi)                              │   │
│  │  - Request/Response Logging                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ API Routes                                               │   │
│  │  - /api/auth (Register, Login, OTP Verification)        │   │
│  │  - /api/products (CRUD, filtering, search)              │   │
│  │  - /api/orders (Create, List, Get, Cancel)              │   │
│  │  - /api/payments (Razorpay integration, verification)   │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Services Layer                                           │   │
│  │  - AuthService (user management, tokens)                │   │
│  │  - OrderService (order processing, price validation)    │   │
│  │  - PaymentService (Razorpay integration)                │   │
│  │  - EmailService (OTP, confirmations)                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Data Layer                                               │   │
│  │  - SQLAlchemy ORM (type-safe queries)                   │   │
│  │  - Pydantic Schemas (input validation)                  │   │
│  │  - Database Models (User, Product, Order, OrderItem)    │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┬──────────────┐
                ▼            ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────────┐
        │PostgreSQL│  │Razorpay  │  │Email Service│
        │Database  │  │Payment   │  │ (SMTP)      │
        │          │  │Gateway   │  │             │
        └──────────┘  └──────────┘  └──────────────┘
```

---

## 🔒 Security Layers

### 1. **Transport Layer (HTTPS/TLS)**
- Enforced HTTPS in production
- HSTS header (max-age: 31536000 seconds = 1 year)
- Automatic HTTP→HTTPS redirect

### 2. **Rate Limiting Layer**
- **Auth Endpoints**: 5 requests/minute (strict)
- **API Endpoints**: 30 requests/minute (normal)
- **Read-Only**: 100 requests/minute (generous)
- Prevents brute-force attacks and DoS

### 3. **Authentication Layer**
- JWT tokens with 30-minute expiry
- Refresh tokens with 7-day expiry
- Bcrypt password hashing (12 rounds)
- OTP verification for sensitive operations

### 4. **Authorization Layer**
- Role-based access control (Admin vs User)
- User ownership verification
- Resource-level permissions

### 5. **Input Validation Layer**
- Pydantic schema validation on all endpoints
- Email validation
- Password complexity requirements
- Type checking

### 6. **Business Logic Layer**
- Backend-only price calculation
- Stock validation before order creation
- HMAC-SHA256 payment signature verification
- Decimal precision for monetary values

### 7. **Database Layer**
- Parameterized queries (SQL injection prevention)
- UUID primary keys (not sequential)
- Foreign key constraints
- Audit timestamps

### 8. **Response Security Layer**
- No sensitive data in responses
- Proper HTTP status codes
- Security headers on all responses
- Error messages don't leak information

---

## 🎯 Price Tampering Prevention

### Critical Security: Backend-Only Price Calculation

```
PROBLEM: Frontend sends prices, backend trusts them
❌ Customer modifies price in browser → Pays ₹1 instead of ₹499

SOLUTION: Backend validates and recalculates everything

Flow:
1. Frontend sends: { product_id: "xxx", quantity: 2 }
2. Backend:
   - Fetch product from DB (get current price)
   - Validate stock
   - Calculate: subtotal = price × quantity
   - Calculate: tax = subtotal × 0.18
   - Calculate: shipping = (subtotal > 500) ? 0 : 50
   - Calculate: total = subtotal + tax + shipping
3. Store locked prices with order
4. Frontend cannot modify order total

Result: ✅ Price tampering impossible
```

### Order Item Snapshot

Each order stores:
- Product name (snapshot)
- Product SKU (snapshot)
- Unit price at order time
- Quantity
- Discount percentage
- Total (locked)

If product price changes later, order keeps original price.

---

## 💳 Payment Security: Razorpay Integration

### HMAC-SHA256 Signature Verification

```
Razorpay sends payment response with signature.
We verify using: HMAC-SHA256(SECRET_KEY, order_id|payment_id)

If signature doesn't match: PAYMENT IS FRAUDULENT
Mark order as FAILED, do NOT process

Code:
    computed = HMAC-SHA256(SECRET_KEY, "order_123|pay_456")
    received = "9ef4dffbfd84f1318f6739a3ce19f9d85851857ae648f114332d8401e0949a"
    
    is_valid = (computed == received)
    
Result: ✅ Payment tampering impossible
```

### Payment Flow Security

```
1. Create Order (backend calculates total)
   ↓
2. Create Razorpay Order (send total to Razorpay)
   ↓
3. Frontend shows Razorpay Checkout
   ↓
4. Customer completes payment
   ↓
5. Razorpay returns: order_id, payment_id, signature
   ↓
6. Frontend sends to /payments/verify
   ↓
7. Backend verifies signature with SECRET_KEY
   ↓
8. If valid:
      - Mark order as PAID
      - Reduce product stock
      - Send confirmation email
   If invalid:
      - Mark order as FAILED
      - Reject payment
```

---

## 📊 Database Schema

### Users Table
```sql
id (UUID) - Primary Key
email (String, UNIQUE)
password_hash (String) - Bcrypt hash
full_name (String)
phone (String, nullable)
is_verified (Boolean) - Email verification
is_admin (Boolean) - Admin flag
is_active (Boolean) - Account active
otp (String, nullable) - Hashed OTP
otp_expiry (DateTime, nullable)
created_at (DateTime)
updated_at (DateTime)
last_login (DateTime, nullable)
```

### Products Table
```sql
id (UUID) - Primary Key
name (String)
sku (String, UNIQUE)
price (Decimal) - Current selling price
cost (Decimal) - Internal cost
discount_percent (Decimal) - 0-100%
stock (Integer) - Current quantity
min_stock (Integer) - Reorder level
category (String)
size (String) - XS, S, M, L, XL, XXL
color (String)
material (String)
image_url (String)
is_active (Boolean)
is_featured (Boolean)
average_rating (Decimal) - 0-5
total_reviews (Integer)
created_at (DateTime)
updated_at (DateTime)
```

### Orders Table
```sql
id (UUID) - Primary Key
user_id (UUID) - Foreign Key
subtotal (Decimal) - Sum of items
tax (Decimal) - 18% GST
shipping_cost (Decimal)
discount (Decimal) - Applied discount
total (Decimal) - Final amount

payment_method (String) - RAZORPAY
payment_status (Enum) - PENDING, COMPLETED, FAILED, REFUNDED
razorpay_order_id (String, UNIQUE)
razorpay_payment_id (String, UNIQUE)
razorpay_signature (String)

shipping_name (String)
shipping_email (String)
shipping_phone (String)
shipping_address (String)
shipping_city (String)
shipping_state (String)
shipping_postal_code (String)
shipping_country (String)

status (Enum) - PENDING, PROCESSING, SHIPPED, DELIVERED, CANCELLED, FAILED
notes (String, nullable)

created_at (DateTime)
updated_at (DateTime)
paid_at (DateTime, nullable)
shipped_at (DateTime, nullable)
delivered_at (DateTime, nullable)
```

### OrderItems Table
```sql
id (UUID) - Primary Key
order_id (UUID) - Foreign Key
product_id (UUID) - Foreign Key

product_name (String) - Snapshot
product_sku (String) - Snapshot
quantity (Integer)

price_per_unit (Decimal) - Snapshot (locked price)
discount_percent (Decimal) - Snapshot
total (Decimal) - quantity × price_per_unit (locked)

size (String, nullable)
color (String, nullable)

created_at (DateTime)
```

---

## 🔑 Key Design Patterns

### 1. **Dependency Injection**
```python
# Database session injected by FastAPI
async def get_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    return orders
```

### 2. **Service Layer**
```python
# Business logic separated from routes
class OrderService:
    @staticmethod
    def create_order(...):
        # Validate items
        # Calculate totals
        # Save to DB
        
# Routes use service
@router.post("/orders")
async def create_order(...):
    order = OrderService.create_order(...)
    return order
```

### 3. **Schema Validation**
```python
# Input validation with Pydantic
class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(..., min_items=1)
    shipping_email: EmailStr
    
    @validator("items")
    def validate_items(cls, v):
        # Custom validation logic
        return v
```

### 4. **Middleware for Cross-Cutting Concerns**
```python
# Rate limiting middleware
@limiter.limit("5/minute")
async def register(...):
    pass

# Security headers middleware
response.headers["X-Frame-Options"] = "DENY"
```

---

## 📈 Scalability Considerations

### Database
- Connection pooling enabled
- Timeout: 10 seconds
- Indexes on frequently queried columns (user_id, product_id, razorpay_order_id)

### Caching (Future Implementation)
```python
# Cache product list
@cache(expire=300)  # 5 minutes
async def get_products():
    pass
```

### Async Operations
```python
# Background tasks for emails
@app.post("/orders")
async def create_order(...):
    background_tasks.add_task(send_confirmation_email, order)
    return order
```

### API Rate Limiting
- Prevents resource exhaustion
- Different limits for different endpoints
- Configurable via settings

---

## 🚀 Production Deployment Checklist

### Security
- [ ] HTTPS/SSL certificate installed
- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` generated
- [ ] Database password changed
- [ ] Razorpay LIVE keys configured
- [ ] Email credentials secured
- [ ] CORS origins limited to your domain
- [ ] Firewall configured

### Performance
- [ ] Database indexes created
- [ ] Connection pooling configured
- [ ] Caching layer implemented
- [ ] CDN for static assets
- [ ] Database backups automated
- [ ] Monitoring/alerting set up

### Operations
- [ ] Logging centralized
- [ ] Error tracking (Sentry)
- [ ] Uptime monitoring
- [ ] Incident response plan
- [ ] Database migration strategy
- [ ] Rollback procedure documented

---

## 🔗 API Documentation

All endpoints are documented in Swagger UI:
```
http://your-domain:8000/api/docs
```

Interactive testing available in the UI.

---

## 📚 References

- **FastAPI**: https://fastapi.tiangolo.com
- **SQLAlchemy**: https://docs.sqlalchemy.org
- **Pydantic**: https://docs.pydantic.dev
- **PostgreSQL**: https://www.postgresql.org/docs
- **Razorpay API**: https://razorpay.com/developers
- **JWT**: https://jwt.io
- **OWASP**: https://owasp.org

---

**This architecture provides enterprise-grade security, scalability, and maintainability.**

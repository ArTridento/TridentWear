"""
Railway Production Configuration Helper
This file contains best practices for running TridentWear on Railway
"""

import os
import secrets
from pathlib import Path

# Generate a strong JWT secret if not provided
def get_jwt_secret():
    """Generate secure JWT secret for production"""
    existing = os.getenv("TRIDENT_JWT_SECRET")
    if existing:
        return existing
    # Generate 32 random bytes and encode as hex
    return secrets.token_hex(32)

# Environment variables needed for Railway
PRODUCTION_ENV_VARS = {
    "TRIDENT_JWT_SECRET": get_jwt_secret(),
    "ENVIRONMENT": "production",
    "JWT_ALGORITHM": "HS256",
    "TRIDENT_JWT_EXPIRATION_DAYS": "7",
    "TRIDENT_SESSION_SECRET": secrets.token_hex(16),
}

print("🔑 PRODUCTION ENVIRONMENT VARIABLES FOR RAILWAY")
print("=" * 60)
for key, value in PRODUCTION_ENV_VARS.items():
    if "SECRET" in key or "JWT" in key:
        print(f"{key} = {value}")
    else:
        print(f"{key} = {value}")

print("\n✅ Add these to Railway Dashboard:")
print("   1. Go to Project Settings → Variables")
print("   2. Copy-paste each variable above")
print("   3. Click Deploy")

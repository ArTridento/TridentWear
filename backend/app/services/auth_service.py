import os
import json
import re
import uuid
import bcrypt
import jwt
import base64
import hashlib
import hmac
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import Request, HTTPException, status

from app.db.json_manager import read_json, update_json

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_DIR = BASE_DIR / "db"
USERS_PATH = str(DB_DIR / "users.json")

JWT_SECRET = os.getenv("TRIDENT_JWT_SECRET", os.getenv("JWT_SECRET", "trident-super-secret-key-12345"))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = int(os.getenv("TRIDENT_JWT_EXPIRATION_DAYS", "7"))
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
REVOKED_TOKEN_IDS: set[str] = set()

DEFAULT_ADMIN = {
    "id": 1,
    "name": "Trident Admin",
    "email": "admin@trident.local",
    "password_hash": "$2b$12$7Q07pQBBqNur7Rdxq4R7pebAeUdR89zN4T.NQfpcPZ/p4CVB3TRJq",
    "role": "admin",
    "created_at": "2026-04-12T00:00:00+00:00",
}

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def load_users() -> List[Dict[str, Any]]:
    users = read_json(USERS_PATH)
    if not users:
        return [DEFAULT_ADMIN]
    return users

def next_id(items: List[Dict[str, Any]]) -> int:
    if not items:
        return 1
    return max(int(item.get("id", 0)) for item in items) + 1

def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    _ = salt
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_legacy_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_encoded, digest_encoded = stored_hash.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    try:
        iterations = int(iterations_text)
        salt_bytes = base64.b64decode(salt_encoded.encode("utf-8"))
        expected = base64.b64decode(digest_encoded.encode("utf-8"))
    except (TypeError, ValueError):
        return False
    computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, iterations)
    return hmac.compare_digest(computed, expected)

def verify_password(password: str, stored_hash: str) -> bool:
    if stored_hash.startswith("pbkdf2_sha256$"):
        return verify_legacy_password(password, stored_hash)
    try:
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
    except ValueError:
        return False

def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    target = email.strip().lower()
    for user in load_users():
        if user.get("email", "").lower() == target:
            return user
    return None

def find_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    for user in load_users():
        if int(user.get("id", 0)) == int(user_id):
            return user
    return None

def update_user(user_id: int, changes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    updated_user = None

    def _apply_update(users: list):
        nonlocal updated_user
        if not users:
            users = [DEFAULT_ADMIN]
        for index, user in enumerate(users):
            if int(user.get("id", 0)) == int(user_id):
                users[index] = {**user, **changes}
                updated_user = users[index]
                break
        return users

    update_json(USERS_PATH, _apply_update)
    return updated_user

def issue_auth_token(user: Dict[str, Any]) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user["id"]),
        "email": user["email"],
        "role": user["role"],
        "name": user["name"],
        "iat": now,
        "exp": now + timedelta(days=JWT_EXPIRATION_DAYS),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_request_token(request: Request) -> Optional[str]:
    auth_header = request.headers.get("authorization", "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    token = request.headers.get("x-session-token", "").strip()
    return token or None

def store_session_user(request: Request, user: Dict[str, Any]) -> None:
    request.session.clear()
    request.session["user_id"] = int(user["id"])

def upgrade_password_hash_if_needed(user: Dict[str, Any], password: str) -> Dict[str, Any]:
    stored_hash = user.get("password_hash", "")
    if not stored_hash.startswith("pbkdf2_sha256$"):
        return user
    upgraded_user = update_user(user["id"], {"password_hash": hash_password(password)})
    return upgraded_user or user

def get_session_user(request: Request) -> Optional[Dict[str, Any]]:
    token = get_request_token(request)
    user_id = None
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("jti") in REVOKED_TOKEN_IDS:
                raise jwt.InvalidTokenError("Token has been revoked.")
            user_id = payload.get("sub")
        except jwt.PyJWTError:
            pass
    if not user_id:
        user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = find_user_by_id(int(user_id))
    if user:
        return user
    request.session.clear()
    return None

def validate_email(email: str) -> str:
    normalized = email.strip().lower()
    if not EMAIL_PATTERN.match(normalized):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enter a valid email address.")
    return normalized

def serialize_user(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "created_at": user["created_at"],
        "gender": user.get("gender"),
        "phone": user.get("phone"),
        "user_id": user.get("user_id"),
        "profile_completed_status": user.get("profile_completed_status", True),
    }

# EXPORTED ENDPOINT LOGIC

def get_current_user_state(request: Request) -> Dict[str, Any]:
    user = get_session_user(request)
    return {"authenticated": bool(user), "user": serialize_user(user) if user else None}

def register_user(payload: Any) -> Dict[str, Any]:
    name = payload.name.strip()
    email = validate_email(payload.email)
    password = payload.password.strip()

    if len(name) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name must be at least 2 characters.")
    if len(password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters.")
    if payload.confirm_password is not None and payload.confirm_password.strip() != password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match.")
    if find_user_by_email(email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with that email already exists.")

    otp = str(random.randint(100000, 999999))
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")

    if smtp_host and smtp_user:
        msg = MIMEText(f"Hello {name},\n\nYour Trident Wear verification code is: {otp}\n\nThis code will expire in 10 minutes.\n\nThank you,\nTrident Wear Team")
        msg["Subject"] = "Trident Wear - Email Verification OTP"
        msg["From"] = smtp_user
        msg["To"] = email
        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [email], msg.as_string())
        except Exception as e:
            pass

    new_user = None

    def _register(users: list):
        nonlocal new_user
        if not users:
            users = [DEFAULT_ADMIN]

        current_year_suffix = datetime.now().strftime("%y")
        highest_seq = 0
        prefix = f"TW{current_year_suffix}-"
        for u in users:
            uid = str(u.get("user_id", ""))
            if uid.startswith(prefix):
                try:
                    seq = int(uid.split("-")[1])
                    if seq > highest_seq:
                        highest_seq = seq
                except Exception:
                    pass
        
        seq_number = str(highest_seq + 1).zfill(3)
        user_id_formatted = f"{prefix}{seq_number}"

        new_user = {
            "id": next_id(users),
            "user_id": user_id_formatted,
            "name": name,
            "email": email,
            "password_hash": hash_password(password),
            "role": "customer",
            "gender": getattr(payload, "gender", None),
            "otp": otp,
            "otp_expiry": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
            "otp_verification_status": False,
            "profile_completed_status": False,
            "created_at": now_iso(),
        }
        users.append(new_user)
        return users

    update_json(USERS_PATH, _register)

    if not (smtp_host and smtp_user):
        return {"success": True, "message": f"Account created. (Dev Mode OTP: {otp})", "email": email, "dev_otp": otp}

    return {"success": True, "message": "Account created. Please check your email for the OTP.", "email": email}

def login_user(payload: Any, request: Request) -> Dict[str, Any]:
    email = validate_email(payload.email)
    password = payload.password.strip()
    user = find_user_by_email(email)

    if not user or not verify_password(password, user.get("password_hash", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")
    
    if user.get("role") != "admin" and not user.get("otp_verification_status", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please verify your email OTP before logging in.")

    user = upgrade_password_hash_if_needed(user, password)
    store_session_user(request, user)
    token = issue_auth_token(user)

    return {"success": True, "message": "Signed in successfully.", "token": token, "user": serialize_user(user)}

def logout_user(request: Request) -> Dict[str, Any]:
    revoke_auth_token(get_request_token(request))
    request.session.clear()
    return {"success": True, "message": "Signed out."}

def require_admin(request: Request) -> Dict[str, Any]:
    user = get_session_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: Admins only.")
    return user

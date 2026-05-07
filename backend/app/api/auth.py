from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.services.auth_service import register_user, login_user, get_current_user_state, logout_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

class LoginPayload(BaseModel):
    email: str
    password: str

class RegisterPayload(BaseModel):
    name: str
    email: str
    password: str
    confirm_password: Optional[str] = None
    gender: Optional[str] = None

@router.get("/me")
def get_auth_state(request: Request) -> Dict[str, Any]:
    return get_current_user_state(request)

@router.post("/register")
def register(payload: RegisterPayload, request: Request) -> Dict[str, Any]:
    return register_user(payload)

@router.post("/login")
def login(payload: LoginPayload, request: Request) -> Dict[str, Any]:
    return login_user(payload, request)

@router.post("/logout")
def logout(request: Request) -> Dict[str, Any]:
    return logout_user(request)

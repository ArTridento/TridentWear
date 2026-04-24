from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse, OTPRequest, OTPVerify
from services.auth_service import AuthService
from utils.token import verify_token, get_user_id_from_token
from models.user import User
from middleware.rate_limit import limiter, RATE_LIMIT_STRICT, RATE_LIMIT_NORMAL
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ========== DEPENDENCY: GET CURRENT USER ==========
async def get_current_user(
    token: Optional[str] = None,
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to get current authenticated user from JWT token.

    Args:
        token: JWT token (can be in Authorization header or query param)
        db: Database session

    Returns:
        Authenticated user
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = get_user_id_from_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = AuthService.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


# ========== REGISTER ENDPOINT ==========
@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMIT_STRICT)
async def register(
    request,  # For rate limiter
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    """
    Register a new user account.

    - Email must be unique
    - Password must be 8+ chars with uppercase, lowercase, digit
    """
    try:
        result = AuthService.register_user(db, user_data)

        return {
            "status": "success",
            "message": "User registered successfully",
            "user": result["user"],
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": "bearer",
        }

    except ValueError as e:
        logger.warning(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


# ========== LOGIN ENDPOINT ==========
@router.post("/login", response_model=dict)
@limiter.limit(RATE_LIMIT_STRICT)
async def login(
    request,  # For rate limiter
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Login user with email and password.

    Returns access and refresh tokens.
    """
    try:
        result = AuthService.login_user(db, credentials.email, credentials.password)

        return {
            "status": "success",
            "message": "Login successful",
            "user": result["user"],
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": "bearer",
        }

    except ValueError as e:
        logger.warning(f"Login failed for {credentials.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


# ========== SEND OTP ENDPOINT ==========
@router.post("/send-otp")
@limiter.limit(RATE_LIMIT_NORMAL)
async def send_otp(
    request,  # For rate limiter
    otp_request: OTPRequest,
    db: Session = Depends(get_db),
):
    """
    Send OTP to email for verification.

    OTP is valid for 10 minutes.
    """
    try:
        from services.email_service import EmailService

        result = AuthService.send_otp(db, otp_request.email)

        # ========== SEND EMAIL IN PRODUCTION ==========
        # In production, email_service would send the actual OTP
        # For now, this is just placeholder
        # email_service.send_otp_email(otp_request.email, otp)

        return {
            "status": "success",
            "message": "OTP sent to email",
            "email": otp_request.email,
        }

    except Exception as e:
        logger.error(f"OTP send error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP",
        )


# ========== VERIFY OTP ENDPOINT ==========
@router.post("/verify-otp", response_model=dict)
@limiter.limit(RATE_LIMIT_STRICT)
async def verify_otp(
    request,  # For rate limiter
    otp_data: OTPVerify,
    db: Session = Depends(get_db),
):
    """
    Verify OTP and return tokens.

    After successful verification, user is marked as verified.
    """
    try:
        result = AuthService.verify_otp(db, otp_data.email, otp_data.otp)

        return {
            "status": "success",
            "message": "OTP verified successfully",
            "user": result["user"],
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": "bearer",
        }

    except ValueError as e:
        logger.warning(f"OTP verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"OTP verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OTP verification failed",
        )


# ========== GET CURRENT USER ENDPOINT ==========
@router.get("/me", response_model=UserResponse)
async def get_me(
    authorization: str = None,
    db: Session = Depends(get_db),
):
    """
    Get current authenticated user profile.

    Include JWT token in Authorization header: "Bearer <token>"
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = authorization.replace("Bearer ", "")
    user = await get_current_user(token, db)

    return user

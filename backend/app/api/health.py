from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/health", tags=["health"])

@router.get("")
def health_check():
    return {"status": "healthy", "message": "New modular architecture is running!"}

from fastapi import APIRouter

# /api/v1/health — versioned route (existing, unchanged)
router = APIRouter(prefix="/api/v1/health", tags=["health"])

@router.get("")
def health_check():
    return {"status": "healthy", "service": "TridentWear API"}

# /health — bare root route for Render/Railway/Docker health check probes
root_health_router = APIRouter(tags=["health"])

@root_health_router.get("/health")
def root_health_check():
    return {"status": "healthy", "service": "TridentWear API"}

from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get("/api/health")
def api_health():
    """Canonical health check endpoint as specified in PRD §12.1."""
    return {"status": "ok"}

@router.get("/health")
def root_health():
    """Backward-compatible health check endpoint."""
    return {"status": "ok"}

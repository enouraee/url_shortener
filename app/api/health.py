from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session

router = APIRouter()


@router.get("/healthz")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns a simple status indicating the service is running.
    This endpoint does not check dependencies.
    """
    return {"status": "ok"}


@router.get("/readyz")
async def readiness_check(
    response: Response,
    session: AsyncSession = Depends(get_session)
):
    """
    Readiness check endpoint.
    
    Verifies that the service is ready to handle requests by:
    - Checking database connectivity with a simple query
    
    Returns 200 with {"status": "ok"} if ready.
    Returns 503 with {"status": "unavailable"} if not ready.
    """
    # Check database connectivity
    try:
        result = await session.execute(text("SELECT 1"))
        result.scalar_one()
    except Exception as e:
        response.status_code = 503
        return {
            "status": "unavailable",
            "error": "Database unavailable",
            "details": [f"Database: {str(e)}"]
        }
    
    return {"status": "ok"}

from typing import Optional

from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.url import ShortenRequest, ShortenResponse, StatsResponse
from app.services import url_service

router = APIRouter()


@router.post("/shorten", response_model=ShortenResponse, status_code=201)
async def create_short_url(
    request: Request,
    body: ShortenRequest,
    session: AsyncSession = Depends(get_session)
):
    """Create a shortened URL."""
    # Get base URL from request
    base_url = str(request.base_url).rstrip('/')
    
    try:
        result = await url_service.shorten_url(
            session=session,
            original_url=str(body.original_url),
            custom_code=body.custom_code,
            base_url=base_url
        )
        return ShortenResponse(**result)
    except url_service.CodeAlreadyExists as e:
        raise HTTPException(status_code=409, detail=str(e))
    except url_service.InvalidCustomCode as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats/{short_code}", response_model=StatsResponse)
async def get_url_stats(
    short_code: str,
    days: Optional[int] = Query(
        None,
        ge=1,
        le=30,
        description="Number of days of daily stats to include (max 30)"
    ),
    session: AsyncSession = Depends(get_session)
):
    """Get stats for a shortened URL."""
    try:
        stats = await url_service.fetch_stats(
            session=session,
            short_code=short_code,
            days=days
        )
        return stats
    except url_service.URLNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.head("/{short_code}", include_in_schema=False)
async def redirect_head(
    short_code: str,
    session: AsyncSession = Depends(get_session)
):
    """
    HEAD request for redirect - returns redirect headers without tracking.
    
    Does NOT increment visit counters to avoid double-counting when clients
    probe with HEAD before making the actual GET request.
    
    Returns a 307 Temporary Redirect with Location header.
    """
    try:
        url = await url_service.resolve_only(
            session=session,
            short_code=short_code
        )
        return RedirectResponse(url=url.original_url, status_code=307)
    except url_service.URLNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{short_code}")
async def redirect_to_url(
    short_code: str,
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """
    Redirect to the original URL and track the visit.
    
    Returns a 307 Temporary Redirect to the original URL.
    """
    # Get client IP, with proxy-aware handling
    # Check for X-Forwarded-For header first (set by reverse proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs: client, proxy1, proxy2, ...
        # The first IP is the original client
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"
    
    try:
        url = await url_service.resolve_and_track(
            session=session,
            short_code=short_code,
            client_ip=client_ip
        )
        return RedirectResponse(url=url.original_url, status_code=307)
    except url_service.URLNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


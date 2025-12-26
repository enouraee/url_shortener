from fastapi import APIRouter, Request, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_session

router = APIRouter()


@router.post("/shorten")
async def create_short_url(original_url: str, session: AsyncSession = Depends(get_session)):
    pass


@router.get("/{short_code}")
async def redirect_to_url(short_code: str, request: Request, session: AsyncSession = Depends(get_session)):
    pass


@router.get("/stats/{short_code}")
async def get_url_stats(short_code: str, session: AsyncSession = Depends(get_session)):
    pass

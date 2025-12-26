from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.db.models import URL, URLVisit, URLDailyStat


async def get_by_code(session: AsyncSession, short_code: str) -> Optional[URL]:
    """
    Retrieve a URL by its short code.
    
    Args:
        session: Async database session
        short_code: The short code to search for
        
    Returns:
        URL object if found, None otherwise
    """
    stmt = select(URL).where(URL.short_code == short_code)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_url(
    session: AsyncSession,
    original_url: str,
    short_code: str
) -> URL:
    """
    Create a new URL entry.
    
    Args:
        session: Async database session
        original_url: The original URL to shorten
        short_code: The short code to use
        
    Returns:
        The created URL object
    """
    url = URL(
        original_url=original_url,
        short_code=short_code
    )
    session.add(url)
    await session.flush()
    await session.refresh(url)
    return url


async def increment_counters(
    session: AsyncSession,
    url_id: int,
    visited_at_dt: datetime,
    ip: str
) -> None:
    """
    Increment visit counters and track the visit.
    
    This function:
    1. Inserts a URLVisit record
    2. Upserts URLDailyStat for the visit day (Postgres ON CONFLICT)
    3. Updates URL.visit_count and URL.last_visited_at
    
    Args:
        session: Async database session
        url_id: The URL ID to track
        visited_at_dt: Timestamp of the visit
        ip: Client IP address
    """
    # 1. Insert visit record
    visit = URLVisit(
        url_id=url_id,
        ip=ip,
        visited_at=visited_at_dt
    )
    session.add(visit)
    
    visit_day = visited_at_dt.date()
    stmt = insert(URLDailyStat).values(
        url_id=url_id,
        day=visit_day,
        count=1
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=['url_id', 'day'],
        set_={'count': URLDailyStat.count + 1}
    )
    await session.execute(stmt)
    
    # Update URL totals
    stmt = (
        update(URL)
        .where(URL.id == url_id)
        .values(
            visit_count=URL.visit_count + 1,
            last_visited_at=visited_at_dt
        )
    )
    await session.execute(stmt)


async def get_stats(
    session: AsyncSession,
    short_code: str,
    days: Optional[int] = None
) -> tuple[Optional[URL], list[URLDailyStat]]:
    """
    Get URL statistics including optional daily breakdown.
    
    Args:
        session: Async database session
        short_code: The short code to get stats for
        days: Optional number of days of daily stats to retrieve (most recent)
        
    Returns:
        Tuple of (URL object, list of URLDailyStat objects)
        If URL not found, returns (None, [])
    """
    # Get the URL
    url = await get_by_code(session, short_code)
    if not url:
        return None, []
    
    # Get daily stats if requested
    daily_stats = []
    if days is not None and days > 0:
        today = datetime.now(timezone.utc).date()
        start_day = today - timedelta(days=days - 1)
        stmt = (
            select(URLDailyStat)
            .where(URLDailyStat.url_id == url.id)
            .where(URLDailyStat.day >= start_day)
            .where(URLDailyStat.day <= today)
            .order_by(URLDailyStat.day.desc())
            .limit(days)
        )
        result = await session.execute(stmt)
        daily_stats = list(result.scalars().all())
    
    return url, daily_stats

import secrets
import string
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.db.models import URL
from app.repositories import url_repo
from app.schemas.url import StatsResponse, DailyStat


class URLNotFound(Exception):
    def __init__(self, short_code: str):
        self.short_code = short_code
        super().__init__(f"URL '{short_code}' not found")


class CodeAlreadyExists(Exception):
    def __init__(self, short_code: str):
        self.short_code = short_code
        super().__init__(f"Code '{short_code}' already taken")


class InvalidCustomCode(Exception):
    """Raised when a custom code does not meet validation requirements."""
    
    def __init__(self, message: str):
        super().__init__(message)


def generate_code(length: int = 6) -> str:
    """
    Generate a random short code.
    
    Uses alphanumeric characters (a-z, A-Z, 0-9) for the code.
    This is a simple implementation; in production, consider:
    - Base62 encoding of sequential IDs
    - Collision detection and retry logic
    - Configurable character sets
    
    Args:
        length: Length of the code to generate (default: 6)
        
    Returns:
        A random alphanumeric string
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


async def shorten_url(
    session: AsyncSession,
    original_url: str,
    custom_code: Optional[str],
    base_url: str
) -> dict:
    """
    Create a shortened URL.
    
    Args:
        session: Async database session
        original_url: The URL to shorten
        custom_code: Optional custom short code
        base_url: Base URL for constructing the short URL
        
    Returns:
        Dictionary with URL details (short_code, short_url, original_url, created_at)
        
    Raises:
        CodeAlreadyExists: If the custom code is already in use
        InvalidCustomCode: If the custom code is invalid
    """
    # Determine the short code
    if custom_code:
        short_code = custom_code
        # Check if code already exists
        existing = await url_repo.get_by_code(session, short_code)
        if existing:
            raise CodeAlreadyExists(short_code)
        
        # Try to create with custom code
        try:
            url = await url_repo.create_url(session, original_url, short_code)
            await session.commit()
        except IntegrityError as e:
            await session.rollback()
            # Race condition: code was taken between check and insert
            raise CodeAlreadyExists(short_code) from e
    else:
        # Generate a code and retry on collision
        max_attempts = 5
        url = None
        
        for attempt in range(max_attempts):
            short_code = generate_code()
            try:
                url = await url_repo.create_url(session, original_url, short_code)
                await session.commit()
                break  # Success!
            except IntegrityError:
                await session.rollback()
                # Collision, try again with new code
                if attempt == max_attempts - 1:
                    # Last attempt failed, raise error
                    raise CodeAlreadyExists(short_code)
                # Continue to next attempt
        
        if url is None:
            # Should not reach here, but safety check
            raise CodeAlreadyExists(short_code)
    
    # Build response
    short_url = f"{base_url.rstrip('/')}/{short_code}"
    
    return {
        "short_code": url.short_code,
        "short_url": short_url,
        "original_url": url.original_url,
        "created_at": url.created_at,
    }


async def resolve_only(
    session: AsyncSession,
    short_code: str
) -> URL:
    """
    Resolve a short code to its URL WITHOUT tracking the visit.
    
    Used for HEAD requests to avoid double-counting when clients
    probe with HEAD before making the actual GET request.
    
    Args:
        session: Async database session
        short_code: The short code to resolve
        
    Returns:
        The URL object
        
    Raises:
        URLNotFound: If the short code doesn't exist
    """
    url = await url_repo.get_by_code(session, short_code)
    if not url:
        raise URLNotFound(short_code)
    
    return url


async def resolve_and_track(
    session: AsyncSession,
    short_code: str,
    client_ip: str
) -> URL:
    """
    Resolve a short code to its URL and track the visit.
    
    Args:
        session: Async database session
        short_code: The short code to resolve
        client_ip: Client IP address for tracking
        
    Returns:
        The URL object
        
    Raises:
        URLNotFound: If the short code doesn't exist
    """
    # Get the URL
    url = await url_repo.get_by_code(session, short_code)
    if not url:
        raise URLNotFound(short_code)
    
    visited_at = datetime.now(timezone.utc)
    await url_repo.increment_counters(session, url.id, visited_at, client_ip)
    await session.commit()
    
    return url


async def fetch_stats(
    session: AsyncSession,
    short_code: str,
    days: Optional[int] = None
) -> StatsResponse:
    """
    Fetch statistics for a short URL.
    
    Args:
        session: Async database session
        short_code: The short code to get stats for
        days: Optional number of days of daily stats to include
        
    Returns:
        StatsResponse object with URL statistics
        
    Raises:
        URLNotFound: If the short code doesn't exist
    """
    url, daily_stats = await url_repo.get_stats(session, short_code, days)
    
    if not url:
        raise URLNotFound(short_code)
    
    # Reverse to ascending order for API response
    daily = None
    if daily_stats:
        daily = [
            DailyStat(day=stat.day, count=stat.count)
            for stat in reversed(daily_stats)
        ]
    
    return StatsResponse(
        short_code=url.short_code,
        original_url=url.original_url,
        created_at=url.created_at,
        visit_count=url.visit_count,
        last_visited_at=url.last_visited_at,
        daily=daily
    )

import logging
from datetime import datetime, timezone

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("url_shortener.redirect")

# Paths that are NOT short code redirects
SKIP_PREFIXES = ("/shorten", "/stats", "/health", "/ready", "/docs", "/openapi", "/redoc")


class RedirectLoggingMiddleware(BaseHTTPMiddleware):
    """Logs IP and timestamp when a short URL is accessed."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        path = request.url.path
        
        # Log only successful redirects (307) to short code paths
        if response.status_code == 307 and not path.startswith(SKIP_PREFIXES):
            ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            if not ip:
                ip = request.client.host if request.client else "unknown"
            
            logger.info(f"{path[1:]} | {ip} | {datetime.now(timezone.utc).isoformat()}")
        
        return response


def add_logging_middleware(app):
    app.add_middleware(RedirectLoggingMiddleware)


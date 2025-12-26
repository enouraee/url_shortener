from fastapi import FastAPI

from app.api import endpoints, health
from app.middleware.logging import add_logging_middleware


app = FastAPI(
    title="URL Shortener API",
    description="URL shortening service",
    version="0.1.0"
)

# Register routers
app.include_router(health.router, tags=["health"])
app.include_router(endpoints.router, tags=["urls"])

# Add middleware
add_logging_middleware(app)

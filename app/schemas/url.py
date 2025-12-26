from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field, AnyUrl, field_validator


class ShortenRequest(BaseModel):
    """Request body for creating short URLs."""
    
    original_url: AnyUrl = Field(
        ...,
        description="The original URL to be shortened",
        examples=["https://example.com/very-long-url"]
    )
    custom_code: Optional[str] = Field(
        None,
        min_length=3,
        max_length=20,
        pattern="^[a-zA-Z0-9_-]+$",
        description="Optional custom short code (alphanumeric, dash, underscore only)",
        examples=["my-link"]
    )
    
    @field_validator('custom_code')
    @classmethod
    def validate_custom_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.lower() in {'healthz', 'readyz', 'stats', 'api', 'admin', 'shorten'}:
            raise ValueError('Custom code conflicts with reserved endpoints')
        return v


class ShortenResponse(BaseModel):
    """Response for shortened URL."""
    
    short_code: str = Field(
        ...,
        description="The generated or custom short code",
        examples=["abc123"]
    )
    short_url: str = Field(
        ...,
        description="The complete shortened URL",
        examples=["http://localhost:8000/abc123"]
    )
    original_url: str = Field(
        ...,
        description="The original URL that was shortened",
        examples=["https://example.com/very-long-url"]
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the short URL was created"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "short_code": "abc123",
                "short_url": "http://localhost:8000/abc123",
                "original_url": "https://example.com/very-long-url",
                "created_at": "2025-12-26T10:30:00Z"
            }
        }
    }


class DailyStat(BaseModel):
    """Visit count for a day."""
    
    day: date = Field(
        ...,
        description="The date of the statistics"
    )
    count: int = Field(
        ...,
        ge=0,
        description="Number of visits on this day"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "day": "2025-12-26",
                "count": 42
            }
        }
    }


class StatsResponse(BaseModel):
    """Stats response with visit counts."""
    
    short_code: str = Field(
        ...,
        description="The short code",
        examples=["abc123"]
    )
    original_url: str = Field(
        ...,
        description="The original URL",
        examples=["https://example.com/very-long-url"]
    )
    created_at: datetime = Field(
        ...,
        description="When the short URL was created"
    )
    visit_count: int = Field(
        ...,
        ge=0,
        description="Total number of visits"
    )
    last_visited_at: Optional[datetime] = Field(
        None,
        description="Timestamp of the most recent visit"
    )
    daily: Optional[list[DailyStat]] = Field(
        None,
        description="Daily visit statistics (last N days if requested)"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "short_code": "abc123",
                "original_url": "https://example.com/very-long-url",
                "created_at": "2025-12-26T10:30:00Z",
                "visit_count": 150,
                "last_visited_at": "2025-12-26T15:45:00Z",
                "daily": [
                    {"day": "2025-12-26", "count": 42},
                    {"day": "2025-12-25", "count": 38}
                ]
            }
        }
    }

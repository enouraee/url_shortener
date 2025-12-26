"""Database models for URL Shortener."""

from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    Text,
    DateTime,
    Date,
    String,
    Index,
    UniqueConstraint,
    ForeignKey,
    func,
    text,
)
from sqlmodel import SQLModel, Field


class URL(SQLModel, table=True):
    """Main URL table storing original URLs and their short codes."""

    __tablename__ = "urls"

    id: Optional[int] = Field(default=None, primary_key=True)
    original_url: str = Field(sa_column=Column(Text, nullable=False))
    short_code: str = Field(sa_column=Column(String(20), nullable=False, unique=True, index=True))
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    )
    visit_count: int = Field(default=0, sa_column=Column(BigInteger, nullable=False, server_default=text("0")))
    last_visited_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    __table_args__ = (
        Index("ix_urls_created_at", "created_at"),
    )


class URLVisit(SQLModel, table=True):
    """Individual visit tracking for URLs."""

    __tablename__ = "url_visits"

    id: Optional[int] = Field(default=None, primary_key=True)
    url_id: int = Field(sa_column=Column(Integer, ForeignKey("urls.id", ondelete="CASCADE"), nullable=False))
    ip: str = Field(sa_column=Column(String(45), nullable=False))  # IPv6 max length is 45
    visited_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    )

    __table_args__ = (
        Index("ix_url_visits_url_id_visited_at", "url_id", "visited_at"),
    )


class URLDailyStat(SQLModel, table=True):
    """Daily aggregated visit statistics per URL."""

    __tablename__ = "url_daily_stats"

    id: Optional[int] = Field(default=None, primary_key=True)
    url_id: int = Field(sa_column=Column(Integer, ForeignKey("urls.id", ondelete="CASCADE"), nullable=False))
    day: date = Field(sa_column=Column(Date, nullable=False))
    count: int = Field(default=0, sa_column=Column(BigInteger, nullable=False, server_default=text("0")))

    __table_args__ = (
        UniqueConstraint("url_id", "day", name="uq_url_daily_stats_url_id_day"),
        Index("ix_url_daily_stats_url_id_day", "url_id", "day"),
    )


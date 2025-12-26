import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from app.db.models import URL, URLDailyStat


@pytest.mark.asyncio
async def test_stats_no_daily_by_default(client: AsyncClient):
    """Stats without days param shouldn't have daily breakdown."""
    create_response = await client.post(
        "/shorten",
        json={"original_url": "https://example.com/stats-test"}
    )
    assert create_response.status_code == 201
    short_code = create_response.json()["short_code"]
    
    stats_response = await client.get(f"/stats/{short_code}")
    assert stats_response.status_code == 200
    
    stats_data = stats_response.json()
    assert stats_data["short_code"] == short_code
    assert stats_data["original_url"] == "https://example.com/stats-test"
    assert stats_data["visit_count"] == 0
    assert stats_data["last_visited_at"] is None
    assert stats_data.get("daily") is None


@pytest.mark.asyncio
async def test_stats_with_days_includes_daily_ascending_order(client: AsyncClient):
    """Days param should return daily stats in asc order."""
    create_response = await client.post(
        "/shorten",
        json={"original_url": "https://example.com/daily-test"}
    )
    assert create_response.status_code == 201
    short_code = create_response.json()["short_code"]
    
    for _ in range(3):
        redirect_response = await client.get(
            f"/{short_code}",
            follow_redirects=False
        )
        assert redirect_response.status_code == 307
    
    stats_response = await client.get(f"/stats/{short_code}?days=7")
    assert stats_response.status_code == 200
    
    stats_data = stats_response.json()
    assert stats_data["visit_count"] == 3
    assert stats_data["last_visited_at"] is not None
    
    assert "daily" in stats_data
    assert stats_data["daily"] is not None
    assert len(stats_data["daily"]) >= 1
    
    if len(stats_data["daily"]) > 1:
        days = [entry["day"] for entry in stats_data["daily"]]
        assert days == sorted(days)
    
    for entry in stats_data["daily"]:
        assert "day" in entry
        assert "count" in entry
        assert isinstance(entry["count"], int)
        assert entry["count"] >= 0


@pytest.mark.asyncio
async def test_stats_days_validation_too_low(client: AsyncClient):
    """days=0 should fail."""
    create_response = await client.post(
        "/shorten",
        json={"original_url": "https://example.com/validation-test"}
    )
    assert create_response.status_code == 201
    short_code = create_response.json()["short_code"]
    
    stats_response = await client.get(f"/stats/{short_code}?days=0")
    assert stats_response.status_code == 422


@pytest.mark.asyncio
async def test_stats_days_validation_too_high(client: AsyncClient):
    """days=31 should fail."""
    create_response = await client.post(
        "/shorten",
        json={"original_url": "https://example.com/validation-test2"}
    )
    assert create_response.status_code == 201
    short_code = create_response.json()["short_code"]
    
    stats_response = await client.get(f"/stats/{short_code}?days=31")
    assert stats_response.status_code == 422


@pytest.mark.asyncio
async def test_stats_not_found(client: AsyncClient):
    """Missing code should 404."""
    stats_response = await client.get("/stats/nonexistent123")
    
    assert stats_response.status_code == 404
    assert "detail" in stats_response.json()


@pytest.mark.asyncio
async def test_stats_with_valid_days_range(client: AsyncClient):
    """Valid days 1-30 should work."""
    create_response = await client.post(
        "/shorten",
        json={"original_url": "https://example.com/range-test"}
    )
    assert create_response.status_code == 201
    short_code = create_response.json()["short_code"]
    
    for days_value in [1, 7, 15, 30]:
        stats_response = await client.get(f"/stats/{short_code}?days={days_value}")
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert "daily" in stats_data
        assert stats_data["daily"] is None or isinstance(stats_data["daily"], list)


@pytest.mark.asyncio
async def test_stats_days_filters_sparse_history(db_session, client: AsyncClient):
    """Should only return stats within the N days window."""
    url = URL(original_url="https://example.com/sparse", short_code="sparse1")
    db_session.add(url)
    await db_session.flush()
    await db_session.refresh(url)

    today = datetime.now(timezone.utc).date()
    old_day = today - timedelta(days=20)
    recent_day = today - timedelta(days=2)

    db_session.add_all([
        URLDailyStat(url_id=url.id, day=old_day, count=5),
        URLDailyStat(url_id=url.id, day=recent_day, count=3),
        URLDailyStat(url_id=url.id, day=today, count=2),
    ])
    url.visit_count = 10
    url.last_visited_at = datetime.now(timezone.utc)
    await db_session.commit()

    stats_response = await client.get(f"/stats/{url.short_code}?days=7")
    assert stats_response.status_code == 200
    stats = stats_response.json()

    assert stats["daily"] is not None
    returned_days = [entry["day"] for entry in stats["daily"]]
    assert old_day.isoformat() not in returned_days
    assert recent_day.isoformat() in returned_days
    assert today.isoformat() in returned_days
    assert returned_days == sorted(returned_days)

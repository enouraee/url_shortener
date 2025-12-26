import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_redirect_tracks_visit(client: AsyncClient):
    """GET should redirect and track visit."""
    create_response = await client.post(
        "/shorten",
        json={"original_url": "https://example.com/target"}
    )
    assert create_response.status_code == 201
    short_code = create_response.json()["short_code"]
    
    redirect_response = await client.get(
        f"/{short_code}",
        follow_redirects=False
    )
    
    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == "https://example.com/target"
    
    stats_response = await client.get(f"/stats/{short_code}")
    assert stats_response.status_code == 200
    stats_data = stats_response.json()
    
    assert stats_data["visit_count"] == 1
    assert stats_data["last_visited_at"] is not None


@pytest.mark.asyncio
async def test_head_redirect_does_not_track(client: AsyncClient):
    """HEAD should redirect but not track."""
    create_response = await client.post(
        "/shorten",
        json={"original_url": "https://example.com/headtest"}
    )
    assert create_response.status_code == 201
    short_code = create_response.json()["short_code"]
    
    head_response = await client.head(
        f"/{short_code}",
        follow_redirects=False
    )
    
    assert head_response.status_code == 307
    assert head_response.headers["location"] == "https://example.com/headtest"
    
    stats_response = await client.get(f"/stats/{short_code}")
    assert stats_response.status_code == 200
    stats_data = stats_response.json()
    
    assert stats_data["visit_count"] == 0
    assert stats_data["last_visited_at"] is None


@pytest.mark.asyncio
async def test_get_redirect_not_found(client: AsyncClient):
    """Missing code should 404."""
    response = await client.get(
        "/nope123",
        follow_redirects=False
    )
    
    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_head_redirect_not_found(client: AsyncClient):
    """HEAD on missing code should 404."""
    response = await client.head(
        "/nope123",
        follow_redirects=False
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_redirect_multiple_visits(client: AsyncClient):
    """Visits should increment count."""
    create_response = await client.post(
        "/shorten",
        json={"original_url": "https://example.com/multi"}
    )
    assert create_response.status_code == 201
    short_code = create_response.json()["short_code"]
    
    for _ in range(3):
        redirect_response = await client.get(
            f"/{short_code}",
            follow_redirects=False
        )
        assert redirect_response.status_code == 307
    
    stats_response = await client.get(f"/stats/{short_code}")
    assert stats_response.status_code == 200
    stats_data = stats_response.json()
    
    assert stats_data["visit_count"] == 3
    assert stats_data["last_visited_at"] is not None

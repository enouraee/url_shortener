import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_shorten_url_auto_generated_code(client: AsyncClient):
    """Should return 201 with generated code."""
    response = await client.post(
        "/shorten",
        json={"original_url": "https://example.com/very-long-url"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify all required fields exist
    assert "short_code" in data
    assert "short_url" in data
    assert "original_url" in data
    assert "created_at" in data
    
    # Verify field values
    assert len(data["short_code"]) > 0
    assert data["short_url"].endswith(f"/{data['short_code']}")
    assert data["original_url"] == "https://example.com/very-long-url"


@pytest.mark.asyncio
async def test_shorten_url_custom_code_success(client: AsyncClient):
    """Custom code should work."""
    custom_code = "git123"
    response = await client.post(
        "/shorten",
        json={
            "original_url": "https://github.com/my-repo",
            "custom_code": custom_code
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["short_code"] == custom_code
    assert data["short_url"].endswith(f"/{custom_code}")
    assert data["original_url"] == "https://github.com/my-repo"


@pytest.mark.asyncio
async def test_shorten_url_duplicate_custom_code(client: AsyncClient):
    """Duplicate code should return 409."""
    custom_code = "dup123"
    
    response1 = await client.post(
        "/shorten",
        json={
            "original_url": "https://example.com/first",
            "custom_code": custom_code
        }
    )
    assert response1.status_code == 201
    
    response2 = await client.post(
        "/shorten",
        json={
            "original_url": "https://example.com/second",
            "custom_code": custom_code
        }
    )
    assert response2.status_code == 409
    assert "detail" in response2.json()


@pytest.mark.asyncio
async def test_shorten_url_invalid_custom_code_too_short(client: AsyncClient):
    """Code < 3 chars should fail."""
    response = await client.post(
        "/shorten",
        json={
            "original_url": "https://example.com/test",
            "custom_code": "ab"
        }
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_shorten_url_invalid_custom_code_pattern(client: AsyncClient):
    """Invalid chars should fail."""
    response = await client.post(
        "/shorten",
        json={
            "original_url": "https://example.com/test",
            "custom_code": "bad code"
        }
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_shorten_url_invalid_custom_code_reserved(client: AsyncClient):
    """Reserved words should fail."""
    response = await client.post(
        "/shorten",
        json={
            "original_url": "https://example.com/test",
            "custom_code": "healthz"
        }
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_shorten_url_invalid_custom_code_reserved_shorten(client: AsyncClient):
    """'shorten' as custom code should fail since it conflicts with the endpoint."""
    response = await client.post(
        "/shorten",
        json={
            "original_url": "https://example.com/test",
            "custom_code": "shorten"
        }
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_shorten_url_invalid_url_format(client: AsyncClient):
    """Bad URL should fail."""
    response = await client.post(
        "/shorten",
        json={
            "original_url": "not-a-valid-url"
        }
    )
    
    assert response.status_code == 422

from __future__ import annotations

import httpx
import pytest
from app.amo.client import AmoClient
from app.core.errors import ExternalServiceError


@pytest.mark.asyncio
async def test_amo_client_pagination() -> None:
    calls: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if len(calls) == 1:
            return httpx.Response(
                200,
                json={
                    "_embedded": {"users": [{"id": 1}]},
                    "_links": {"next": {"href": "https://example.amocrm.ru/api/v4/users?page=2"}},
                },
            )
        return httpx.Response(200, json={"_embedded": {"users": [{"id": 2}]}, "_links": {}})

    client = AmoClient("https://example.amocrm.ru", "token", transport=httpx.MockTransport(handler))
    try:
        users = await client.get_users()
    finally:
        await client.aclose()
    assert [item["id"] for item in users] == [1, 2]


@pytest.mark.asyncio
async def test_amo_client_api_error_is_safe() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="secret-token-leak")

    client = AmoClient("https://example.amocrm.ru", "token", transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ExternalServiceError):
            await client.get_users()
    finally:
        await client.aclose()

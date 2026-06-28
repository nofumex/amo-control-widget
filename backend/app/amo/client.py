from __future__ import annotations

import asyncio
from collections.abc import Iterable
from typing import Any

import httpx

from app.amo.rate_limit import AsyncRateLimiter
from app.core.errors import ExternalServiceError


class AmoClient:
    def __init__(
        self,
        base_url: str,
        access_token: str,
        *,
        rps_limit: float = 6.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.limiter = AsyncRateLimiter(rps_limit)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=35,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "User-Agent": "amo-control-widget/0.1",
            },
            transport=transport,
        )

    async def aclose(self) -> None:
        await self.client.aclose()

    async def get(self, path_or_url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = path_or_url if path_or_url.startswith("http") else path_or_url
        last_error: Exception | None = None
        for attempt in range(1, 4):
            await self.limiter.wait()
            try:
                response = await self.client.get(url, params=params)
                if response.status_code == 204:
                    return {}
                if response.status_code in {429, 500, 502, 503, 504}:
                    retry_after = response.headers.get("Retry-After")
                    delay = int(retry_after) if retry_after and retry_after.isdigit() else 2 * attempt
                    await asyncio.sleep(delay)
                    continue
                if response.status_code >= 400:
                    raise ExternalServiceError(
                        f"amoCRM GET {response.url} failed: {response.status_code}",
                        public_message="amoCRM РІРµСЂРЅСѓР»Р° РѕС€РёР±РєСѓ. РџСЂРѕРІРµСЂСЊС‚Рµ РїРѕРґРєР»СЋС‡РµРЅРёРµ OAuth.",
                    )
                return response.json()
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < 3:
                    await asyncio.sleep(2 * attempt)
                    continue
        raise ExternalServiceError(f"amoCRM GET {path_or_url} failed: {last_error}")

    async def paginate(
        self,
        path: str,
        collection_key: str,
        params: dict[str, Any] | None = None,
        *,
        limit: int = 250,
        max_pages: int = 500,
    ) -> list[dict[str, Any]]:
        current_params = dict(params or {})
        current_params.setdefault("limit", limit)
        current_params.setdefault("page", 1)
        url: str | None = path
        items: list[dict[str, Any]] = []
        for _ in range(max_pages):
            payload = await self.get(url or path, current_params if url == path else None)
            batch = payload.get("_embedded", {}).get(collection_key, [])
            items.extend(batch)
            next_href = payload.get("_links", {}).get("next", {}).get("href")
            if not next_href:
                break
            url = next_href
            current_params = {}
        else:
            raise ExternalServiceError(f"Pagination limit reached for {path}")
        return items

    async def get_account(self) -> dict[str, Any]:
        return await self.get("/api/v4/account", {"with": "datetime_settings,users_groups,task_types"})

    async def get_users(self) -> list[dict[str, Any]]:
        return await self.paginate("/api/v4/users", "users")

    async def get_event_types(self) -> list[dict[str, Any]]:
        payload = await self.get("/api/v4/events/types")
        return payload.get("_embedded", {}).get("events_types", [])

    async def get_events(
        self,
        created_at_from: int,
        created_at_to: int,
        event_types: Iterable[str],
        user_ids: Iterable[int],
    ) -> list[dict[str, Any]]:
        all_events: dict[str, dict[str, Any]] = {}
        users = list(user_ids)
        for user_chunk in _chunks(users, 5):
            params: dict[str, Any] = {
                "filter[created_at][from]": created_at_from,
                "filter[created_at][to]": created_at_to,
            }
            for index, event_type in enumerate(event_types):
                params[f"filter[type][{index}]"] = event_type
            for index, user_id in enumerate(user_chunk):
                params[f"filter[created_by][{index}]"] = user_id
            for event in await self.paginate("/api/v4/events", "events", params=params, limit=100):
                all_events[str(event["id"])] = event
        return sorted(all_events.values(), key=lambda item: (item.get("created_at", 0), str(item.get("id"))))

    async def get_note(self, entity_type: str, entity_id: int, note_id: int) -> dict[str, Any]:
        plural = {
            "lead": "leads",
            "leads": "leads",
            "contact": "contacts",
            "contacts": "contacts",
            "company": "companies",
            "companies": "companies",
            "customer": "customers",
            "customers": "customers",
        }.get(entity_type, f"{entity_type}s")
        return await self.get(f"/api/v4/{plural}/{entity_id}/notes/{note_id}")

    async def get_incomplete_tasks_due_to(self, responsible_user_id: int, complete_till_to: int) -> list[dict[str, Any]]:
        params = {
            "filter[responsible_user_id][0]": responsible_user_id,
            "filter[is_completed]": 0,
            "filter[complete_till][to]": complete_till_to,
        }
        return await self.paginate("/api/v4/tasks", "tasks", params=params)

    async def get_pipelines(self) -> list[dict[str, Any]]:
        return await self.paginate("/api/v4/leads/pipelines", "pipelines")

    async def get_custom_fields(self, entity_type: str) -> list[dict[str, Any]]:
        plural = entity_type.strip("/").lower()
        return await self.paginate(f"/api/v4/{plural}/custom_fields", "custom_fields")


def _chunks(items: list[int], size: int) -> Iterable[list[int]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]

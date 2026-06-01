from typing import Any

import httpx

from app.config import settings


class OdooApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class OdooClient:
    def __init__(self) -> None:
        self.base_url = settings.odoo_url.rstrip("/")
        self.api_key = settings.odoo_api_key

    def _headers(self) -> dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method,
                url,
                headers=self._headers(),
                params=params,
                json=json_body,
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise OdooApiError(
                f"Odoo returned non-JSON response ({response.status_code})",
                status_code=response.status_code,
            ) from exc

        if response.status_code >= 400 or payload.get("status") == "error":
            message = payload.get("message") or response.text
            raise OdooApiError(str(message), status_code=response.status_code)

        return payload.get("data", payload)

    async def get_cargo_line(self, reference: str) -> dict[str, Any]:
        return await self._request(
            "GET",
            "/api/chatbot/cargo/line",
            params={"reference": reference},
        )

    async def search_cargo_lines(
        self,
        query: str,
        search_type: str = "reference",
        limit: int = 5,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/chatbot/cargo/search",
            json_body={"query": query, "search_type": search_type, "limit": limit},
        )

    async def get_cargo_order(self, name: str) -> dict[str, Any]:
        return await self._request(
            "GET",
            "/api/chatbot/cargo/order",
            params={"name": name},
        )

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/api/chatbot/health")
        response.raise_for_status()
        return response.json()

from typing import Any

import httpx

from app.config import settings


class OdooApiError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        *,
        error_type: str | None = None,
        raw: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.error_type = error_type
        self.raw = raw or {}


class OdooClient:
    @property
    def base_url(self) -> str:
        return settings.odoo_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "X-API-Key": settings.odoo_api_key,
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
            message = payload.get("message") or payload.get("detail") or response.text
            raise OdooApiError(
                str(message),
                status_code=response.status_code,
                error_type=payload.get("type"),
                raw=payload if isinstance(payload, dict) else {},
            )

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

    async def chatbot_login(self, login: str, password: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/chatbot/auth/login",
            json_body={"login": login, "password": password},
        )

    async def get_chatbot_defaults(self) -> dict[str, Any]:
        return await self._request("GET", "/api/chatbot/defaults")

    async def list_vehicles(
        self,
        *,
        user_id: int | None = None,
        partner_id: int | None = None,
        customer_mobile: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if user_id is not None:
            params["user_id"] = user_id
        if partner_id is not None:
            params["partner_id"] = partner_id
        if customer_mobile:
            params["customer_mobile"] = customer_mobile
        return await self._request("GET", "/api/chatbot/vehicles", params=params)

    async def get_vehicle_form_options(self) -> dict[str, Any]:
        return await self._request("GET", "/api/chatbot/vehicle/form-options")

    async def create_vehicle(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/api/chatbot/vehicle", json_body=payload)

    async def search_waypoints(self, query: str, limit: int = 10) -> dict[str, Any]:
        return await self._request(
            "GET",
            "/api/chatbot/waypoints/search",
            params={"query": query, "limit": limit},
        )

    async def search_car_makes(self, query: str = "", limit: int = 10) -> dict[str, Any]:
        return await self._request(
            "GET",
            "/api/chatbot/car-makes",
            params={"query": query, "limit": limit},
        )

    async def search_car_models(
        self, car_make_id: int, query: str = "", limit: int = 10
    ) -> dict[str, Any]:
        return await self._request(
            "GET",
            "/api/chatbot/car-models",
            params={"car_make_id": car_make_id, "query": query, "limit": limit},
        )

    async def create_cargo_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/chatbot/cargo/order/create",
            json_body=payload,
        )

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/api/chatbot/health")
        response.raise_for_status()
        return response.json()

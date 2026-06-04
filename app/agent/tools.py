import json
from typing import Any

from langchain_core.tools import tool

from app.agent.errors import record_tool_error
from app.services.odoo_client import OdooApiError, OdooClient

_odoo = OdooClient()


def _dump(data: object) -> str:
    return json.dumps(data, default=str)


def _handle_odoo_error(
    tool: str,
    exc: OdooApiError,
    *,
    details: dict[str, Any] | None = None,
) -> str:
    merged = dict(details or {})
    if exc.error_type:
        merged["error_type"] = exc.error_type
    if exc.raw:
        merged["odoo_response"] = exc.raw
    entry = record_tool_error(
        tool,
        str(exc),
        details=merged or None,
        http_status=exc.status_code,
    )
    return _dump(entry)


@tool
async def search_locations(query: str, limit: int = 10) -> str:
    """Search route waypoints for from/to locations."""
    try:
        return _dump(await _odoo.search_waypoints(query, limit=min(limit, 20)))
    except OdooApiError as exc:
        return _handle_odoo_error("search_locations", exc, details={"query": query})


@tool
async def search_car_makes(query: str = "", limit: int = 10) -> str:
    """Search car makes/manufacturers by name. Returns ids and names; use the id when requesting a quote."""
    try:
        return _dump(await _odoo.search_car_makes(query=query, limit=min(limit, 50)))
    except OdooApiError as exc:
        return _handle_odoo_error("search_car_makes", exc, details={"query": query})


@tool
async def search_car_models(car_make_id: int, query: str = "", limit: int = 10) -> str:
    """Search car models for a given car_make_id. Returns ids and names; use the id when requesting a quote."""
    try:
        return _dump(
            await _odoo.search_car_models(car_make_id, query=query, limit=min(limit, 50))
        )
    except OdooApiError as exc:
        return _handle_odoo_error(
            "search_car_models",
            exc,
            details={"car_make_id": car_make_id, "query": query},
        )


@tool
async def get_shipment_quote(
    loc_from_id: int,
    loc_to_id: int,
    car_make_id: int,
    car_model_id: int,
    agreement_type: str = "oneway",
) -> str:
    """Calculate and rank shipment price options (Normal vs Express variants) for a route and car.

    agreement_type: oneway or return. Returns ranked options with price, tax, total,
    and estimated delivery days. If required inputs are missing the result lists them
    under "missing" so you can ask the user.
    """
    payload: dict[str, Any] = {
        "loc_from_id": loc_from_id,
        "loc_to_id": loc_to_id,
        "car_make_id": car_make_id,
        "car_model_id": car_model_id,
        "agreement_type": agreement_type,
    }
    try:
        return _dump(await _odoo.get_cargo_quote(payload))
    except OdooApiError as exc:
        return _handle_odoo_error("get_shipment_quote", exc, details=payload)


def get_cargo_tools():
    return [
        search_locations,
        search_car_makes,
        search_car_models,
        get_shipment_quote,
    ]

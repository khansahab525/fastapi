import json
from typing import Any

from langchain_core.tools import tool

from app.agent.errors import get_recorded_errors, record_tool_error
from app.auth.context import get_current_user, get_pending_vehicle
from app.services.odoo_client import OdooApiError, OdooClient

_odoo = OdooClient()


def _dump(data: object) -> str:
    return json.dumps(data, default=str)


def _logged_in_kwargs() -> dict[str, Any]:
    user = get_current_user() or {}
    kwargs: dict[str, Any] = {}
    if user.get("user_id"):
        kwargs["user_id"] = int(user["user_id"])
    if user.get("partner_id"):
        kwargs["partner_id"] = int(user["partner_id"])
    if user.get("mobile"):
        kwargs["customer_mobile"] = user["mobile"]
    return kwargs


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


def _tool_fail(tool: str, message: str, *, details: dict[str, Any] | None = None) -> str:
    return _dump(record_tool_error(tool, message, details=details))


@tool
async def get_cargo_line(reference: str) -> str:
    """Get one cargo sale order line by reference (sale_line_rec_name)."""
    try:
        return _dump(await _odoo.get_cargo_line(reference))
    except OdooApiError as exc:
        return _handle_odoo_error("get_cargo_line", exc, details={"reference": reference})


@tool
async def search_cargo_lines(query: str, search_type: str = "reference", limit: int = 5) -> str:
    """Search cargo sale lines."""
    try:
        return _dump(
            await _odoo.search_cargo_lines(query, search_type=search_type, limit=min(limit, 20))
        )
    except OdooApiError as exc:
        return _handle_odoo_error(
            "search_cargo_lines",
            exc,
            details={"query": query, "search_type": search_type},
        )


@tool
async def get_cargo_order(name: str) -> str:
    """Get a cargo sale order by name."""
    try:
        return _dump(await _odoo.get_cargo_order(name))
    except OdooApiError as exc:
        return _handle_odoo_error("get_cargo_order", exc, details={"name": name})


@tool
async def get_order_creation_defaults() -> str:
    """Get defaults for new orders."""
    try:
        return _dump(await _odoo.get_chatbot_defaults())
    except OdooApiError as exc:
        return _handle_odoo_error("get_order_creation_defaults", exc)


@tool
async def list_customer_vehicles() -> str:
    """List saved vehicles for the logged-in user."""
    try:
        return _dump(await _odoo.list_vehicles(**_logged_in_kwargs()))
    except OdooApiError as exc:
        return _handle_odoo_error("list_customer_vehicles", exc)


@tool
async def get_vehicle_form_link() -> str:
    """Return the URL path for the add-vehicle form (use when user wants a new vehicle)."""
    pending = get_pending_vehicle()
    if pending:
        return _dump({
            "form_path": "/vehicle/add",
            "already_saved_vehicle": pending,
            "message": "User already saved a vehicle in this session.",
        })
    return _dump({
        "form_path": "/vehicle/add",
        "message": "Direct the user to open /vehicle/add in the browser to add a new vehicle.",
    })


@tool
async def search_locations(query: str, limit: int = 10) -> str:
    """Search route waypoints for from/to locations."""
    try:
        return _dump(await _odoo.search_waypoints(query, limit=min(limit, 20)))
    except OdooApiError as exc:
        return _handle_odoo_error("search_locations", exc, details={"query": query})


@tool
async def create_cargo_sale_order(
    vehicle_id: int,
    loc_from_id: int,
    loc_to_id: int,
    agreement_type: str,
) -> str:
    """Create cargo sale order. agreement_type: oneway or return."""
    user = get_current_user() or {}
    payload: dict[str, Any] = {
        "vehicle_id": vehicle_id,
        "loc_from_id": loc_from_id,
        "loc_to_id": loc_to_id,
        "agreement_type": agreement_type,
    }
    if user.get("partner_id"):
        payload["customer_id"] = int(user["partner_id"])
        payload["partner_id"] = int(user["partner_id"])
    if user.get("mobile"):
        payload["customer_mobile"] = user["mobile"]

    if loc_from_id == loc_to_id:
        return _tool_fail(
            "create_cargo_sale_order",
            "From and To locations cannot be the same. Please choose different route waypoints.",
            details={"submitted": payload},
        )

    try:
        return _dump(await _odoo.create_cargo_order(payload))
    except OdooApiError as exc:
        return _handle_odoo_error("create_cargo_sale_order", exc, details={"submitted": payload})


@tool
async def get_last_operation_errors() -> str:
    """Return the last Odoo/API errors from this chat request (use when the user asks what went wrong)."""
    errors = get_recorded_errors()
    if not errors:
        return _dump({
            "success": True,
            "message": "No recorded errors in this request. If a tool failed earlier, its error was already returned in that tool result.",
        })
    return _dump({"success": True, "errors": errors})


def get_cargo_tools():
    return [
        get_cargo_line,
        search_cargo_lines,
        get_cargo_order,
        get_order_creation_defaults,
        list_customer_vehicles,
        get_vehicle_form_link,
        search_locations,
        create_cargo_sale_order,
        get_last_operation_errors,
    ]

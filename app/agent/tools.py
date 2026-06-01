import json

from langchain_core.tools import tool

from app.services.odoo_client import OdooApiError, OdooClient

_odoo = OdooClient()


def _dump(data: object) -> str:
    return json.dumps(data, default=str)


@tool
async def get_cargo_line(reference: str) -> str:
    """Get one cargo sale order line by reference (sale_line_rec_name, e.g. P123...).

    Returns status, residual amount, customer, route, vehicle, trip, and payment info.
    """
    try:
        return _dump(await _odoo.get_cargo_line(reference))
    except OdooApiError as exc:
        return _dump({"error": str(exc)})


@tool
async def search_cargo_lines(query: str, search_type: str = "reference", limit: int = 5) -> str:
    """Search cargo sale lines in Odoo.

    search_type must be one of: reference, chassis, plate, mobile, customer, order.
    """
    try:
        return _dump(
            await _odoo.search_cargo_lines(
                query,
                search_type=search_type,
                limit=min(limit, 20),
            )
        )
    except OdooApiError as exc:
        return _dump({"error": str(exc)})


@tool
async def get_cargo_order(name: str) -> str:
    """Get a cargo sale order by name/number, including all order lines and residual totals."""
    try:
        return _dump(await _odoo.get_cargo_order(name))
    except OdooApiError as exc:
        return _dump({"error": str(exc)})


def get_cargo_tools():
    return [get_cargo_line, search_cargo_lines, get_cargo_order]

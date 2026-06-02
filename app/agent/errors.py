from contextvars import ContextVar
from typing import Any

_errors_ctx: ContextVar[list[dict[str, Any]] | None] = ContextVar("tool_errors", default=None)


def init_error_log() -> None:
    _errors_ctx.set([])


def clear_error_log() -> None:
    _errors_ctx.set(None)


def record_tool_error(
    tool: str,
    message: str,
    *,
    details: dict[str, Any] | None = None,
    http_status: int | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "success": False,
        "tool": tool,
        "error_message": message,
    }
    if http_status is not None:
        entry["http_status"] = http_status
    if details:
        entry["details"] = details

    errors = _errors_ctx.get()
    if errors is None:
        errors = []
    errors.append(entry)
    _errors_ctx.set(errors)
    return entry


def get_recorded_errors() -> list[dict[str, Any]]:
    return list(_errors_ctx.get() or [])

from contextvars import ContextVar
from typing import Any

_user_ctx: ContextVar[dict[str, Any] | None] = ContextVar("chat_user", default=None)
_pending_vehicle_ctx: ContextVar[dict[str, Any] | None] = ContextVar("pending_vehicle", default=None)


def set_current_user(user: dict[str, Any] | None) -> None:
    _user_ctx.set(user)


def get_current_user() -> dict[str, Any] | None:
    return _user_ctx.get()


def set_pending_vehicle(vehicle: dict[str, Any] | None) -> None:
    _pending_vehicle_ctx.set(vehicle)


def get_pending_vehicle() -> dict[str, Any] | None:
    return _pending_vehicle_ctx.get()

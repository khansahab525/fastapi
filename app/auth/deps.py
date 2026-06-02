from typing import Any

from fastapi import HTTPException, Request


def require_user(request: Request) -> dict[str, Any]:
    user = request.session.get("user")
    if not user or not user.get("user_id"):
        raise HTTPException(status_code=401, detail="Not authenticated. Please log in.")
    return user

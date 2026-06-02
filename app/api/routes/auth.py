from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.auth.deps import require_user
from app.services.odoo_client import OdooApiError, OdooClient

router = APIRouter(prefix="/auth", tags=["auth"])
_odoo = OdooClient()


class LoginRequest(BaseModel):
    login: str = Field(..., description="Odoo user email / login")
    password: str = Field(..., description="app_password_verify value")


class LoginResponse(BaseModel):
    user_id: int
    login: str
    name: str
    email: str
    partner_id: int | bool
    partner_name: str
    mobile: str


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, request: Request) -> LoginResponse:
    try:
        data = await _odoo.chatbot_login(body.login.strip(), body.password)
    except OdooApiError as exc:
        status = exc.status_code if exc.status_code in (401, 403) else 401
        raise HTTPException(status_code=status, detail=str(exc)) from exc

    partner_id = data.get("partner_id")
    if not partner_id or partner_id is False:
        partner_id = 0
    data["partner_id"] = int(partner_id)
    request.session["user"] = data
    return LoginResponse(**data)


@router.post("/logout")
async def logout(request: Request) -> dict[str, str]:
    request.session.clear()
    return {"message": "Logged out"}


@router.get("/me", response_model=LoginResponse)
async def me(user: dict = Depends(require_user)) -> LoginResponse:
    u = dict(user)
    pid = u.get("partner_id")
    if not pid or pid is False:
        u["partner_id"] = 0
    else:
        u["partner_id"] = int(pid)
    return LoginResponse(**u)

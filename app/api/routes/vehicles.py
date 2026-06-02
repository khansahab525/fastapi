from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.auth.deps import require_user
from app.services.odoo_client import OdooApiError, OdooClient

router = APIRouter(prefix="/vehicles", tags=["vehicles"])
_odoo = OdooClient()


class VehicleCreateBody(BaseModel):
    car_make: int
    car_model: int
    year: int
    plate_registration: str = "saudi"
    car_color: int | None = None
    plate_no: str = ""
    chassis_no: str = ""
    non_saudi_plate_no: str = ""
    plate_one: str = ""
    plate_second: str = ""
    plate_third: str = ""
    plate_type: int | None = None
    owner_name: str = ""
    mobile_no: str = ""


@router.get("/form-options")
async def form_options(_user: dict = Depends(require_user)) -> dict[str, Any]:
    try:
        return await _odoo.get_vehicle_form_options()
    except OdooApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/models")
async def car_models(
    car_make_id: int,
    query: str = "",
    _user: dict = Depends(require_user),
) -> dict[str, Any]:
    try:
        return await _odoo.search_car_models(car_make_id, query, limit=100)
    except OdooApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/create")
async def create_vehicle(
    body: VehicleCreateBody,
    request: Request,
    user: dict = Depends(require_user),
) -> dict[str, Any]:
    payload = body.model_dump(exclude_none=True)
    payload["user_id"] = user["user_id"]
    if user.get("partner_id"):
        payload["partner_id"] = int(user["partner_id"])
    if user.get("mobile") and not payload.get("mobile_no"):
        payload["mobile_no"] = user["mobile"]
    if user.get("name") and not payload.get("owner_name"):
        payload["owner_name"] = user["name"]

    try:
        vehicle = await _odoo.create_vehicle(payload)
    except OdooApiError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    request.session["pending_vehicle"] = vehicle
    return {"status": "success", "vehicle": vehicle}

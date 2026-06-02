from fastapi import APIRouter, Depends, HTTPException, Request
from langchain_core.exceptions import LangChainException

from app.agent.errors import clear_error_log, init_error_log
from app.auth.context import set_current_user, set_pending_vehicle
from app.auth.deps import require_user
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatConfigurationError, ChatService
from app.services.odoo_client import OdooApiError

router = APIRouter(prefix="/chat", tags=["chat"])
_chat_service = ChatService()


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Request,
    user: dict = Depends(require_user),
) -> ChatResponse:
    set_current_user(user)
    pending = request.session.pop("pending_vehicle", None)
    set_pending_vehicle(pending)
    init_error_log()
    try:
        result = await _chat_service.chat(body.message, body.session_id)
        return ChatResponse(**result)
    except ChatConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OdooApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except LangChainException as exc:
        raise HTTPException(status_code=502, detail=f"AI agent error: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI agent error: {exc}") from exc
    finally:
        set_current_user(None)
        set_pending_vehicle(None)
        clear_error_log()


@router.get("/odoo-health")
async def odoo_health() -> dict:
    try:
        data = await _chat_service.odoo.health()
        return {"ok": True, "odoo": data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

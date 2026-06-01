from fastapi import APIRouter, HTTPException
from langchain_core.exceptions import LangChainException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatConfigurationError, ChatService
from app.services.odoo_client import OdooApiError

router = APIRouter(prefix="/chat", tags=["chat"])
_chat_service = ChatService()


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = await _chat_service.chat(request.message, request.session_id)
        return ChatResponse(**result)
    except ChatConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OdooApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except LangChainException as exc:
        raise HTTPException(status_code=502, detail=f"AI agent error: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI agent error: {exc}") from exc


@router.get("/odoo-health")
async def odoo_health() -> dict:
    try:
        data = await _chat_service.odoo.health()
        return {"ok": True, "odoo": data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

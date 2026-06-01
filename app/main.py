from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse

from app.api.routes import api_router
from app.config import settings

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
CHAT_HTML = STATIC_DIR / "chat.html"

app = FastAPI(
    title=settings.app_name,
    description="Cargo sale chatbot — LangGraph agent with Odoo tools.",
    debug=settings.debug,
)

app.include_router(api_router)


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def chat_ui() -> HTMLResponse:
    return HTMLResponse(CHAT_HTML.read_text(encoding="utf-8"))


@app.get("/api")
def api_info() -> dict[str, str]:
    return {
        "message": "AlbassamiChat API",
        "chat_ui": "/",
        "chat_api": "POST /chat",
        "docs": "/docs",
    }

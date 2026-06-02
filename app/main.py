from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import api_router
from app.config import settings

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
CHAT_HTML = STATIC_DIR / "chat.html"
LOGIN_HTML = STATIC_DIR / "login.html"
VEHICLE_FORM_HTML = STATIC_DIR / "vehicle-form.html"

app = FastAPI(
    title=settings.app_name,
    description="Cargo sale chatbot — LangGraph agent with Odoo tools.",
    debug=settings.debug,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie="albassami_chat_session",
    max_age=60 * 60 * 24 * 7,
    same_site="lax",
    https_only=False,
)

app.include_router(api_router)


def _is_logged_in(request: Request) -> bool:
    user = request.session.get("user")
    return bool(user and user.get("user_id"))


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")


@app.get("/login", response_class=HTMLResponse, include_in_schema=False, response_model=None)
def login_page(request: Request):
    if _is_logged_in(request):
        return RedirectResponse(url="/", status_code=302)
    return HTMLResponse(LOGIN_HTML.read_text(encoding="utf-8"))


@app.get("/vehicle/add", response_class=HTMLResponse, include_in_schema=False, response_model=None)
def vehicle_add_form(request: Request):
    if not _is_logged_in(request):
        return RedirectResponse(url="/login", status_code=302)
    return HTMLResponse(VEHICLE_FORM_HTML.read_text(encoding="utf-8"))


@app.get("/", response_class=HTMLResponse, include_in_schema=False, response_model=None)
def chat_ui(request: Request):
    if not _is_logged_in(request):
        return RedirectResponse(url="/login", status_code=302)
    return HTMLResponse(CHAT_HTML.read_text(encoding="utf-8"))


@app.get("/api")
def api_info() -> dict[str, str]:
    return {
        "message": "AlbassamiChat API",
        "login": "/login",
        "chat_ui": "/",
        "chat_api": "POST /chat",
        "docs": "/docs",
    }

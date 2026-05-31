from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.routes import api_router
from app.config import settings

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.include_router(api_router)


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Welcome to AlbassamiChat API"}

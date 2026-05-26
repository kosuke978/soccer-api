from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.core.config import APP_TITLE, BASE_DIR
from app.web.views import router as web_router

app = FastAPI(title=APP_TITLE)
app.include_router(api_router)
app.include_router(web_router)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "app" / "web" / "static")),
    name="static",
)

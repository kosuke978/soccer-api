from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import router as api_router
from app.core.config import APP_TITLE, BASE_DIR, DATA_DIR
from app.data.repository import get_repository

app = FastAPI(title=APP_TITLE)
app.include_router(api_router)

templates = Jinja2Templates(
    directory=str(BASE_DIR / "app" / "web" / "templates")
)
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "app" / "web" / "static")),
    name="static",
)


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    repository = get_repository(DATA_DIR)
    tournament = repository.get_tournament()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "tournament": tournament,
        },
    )

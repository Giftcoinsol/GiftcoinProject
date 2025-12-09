from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import Base, engine
from .routes import participants as participants_routes
from .routes import winners as winners_routes
from .config import settings

# Create tables on startup (for local/dev)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Raffle Backend")

# Static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# API routers
app.include_router(participants_routes.router)
app.include_router(winners_routes.router)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "token_mint": settings.TOKEN_MINT,
            "recaptcha_site_key": settings.RECAPTCHA_SITE_KEY,
        },
    )


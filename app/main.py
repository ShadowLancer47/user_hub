from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .database import engine, Base
from . import models
from .routers import auth, dashboard

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include routers (to be created)
app.include_router(auth.router)
app.include_router(dashboard.router)

from .tools.notes_tool import router as notes_router
app.include_router(notes_router.router)

from .tools.converter_tool import router as converter_router
app.include_router(converter_router.router)

from .tools.lol_tool import router as lol_router
app.include_router(lol_router.router)

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

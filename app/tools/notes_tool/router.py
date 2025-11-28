from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from ...database import get_db
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/tools/notes",
    tags=["notes"]
)

templates = Jinja2Templates(directory=["app/templates", "app/tools/notes_tool/templates"])

# In-memory storage for demo purposes (replace with DB later)
NOTES_DB = {}

@router.get("/")
def notes_home(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?error=Please login first")
    
    user_notes = NOTES_DB.get(user_id, [])
    return templates.TemplateResponse("notes.html", {"request": request, "notes": user_notes})

@router.post("/add")
def add_note(request: Request, content: str = Form(...)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?error=Please login first")
    
    if user_id not in NOTES_DB:
        NOTES_DB[user_id] = []
    
    NOTES_DB[user_id].append(content)
    return RedirectResponse(url="/tools/notes", status_code=303)

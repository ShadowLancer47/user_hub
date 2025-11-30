from fastapi import APIRouter, Request, Depends, Body, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
import uuid
from pydantic import BaseModel
from typing import Optional

router = APIRouter(
    prefix="/tools/notes",
    tags=["notes"]
)

templates = Jinja2Templates(directory=["app/templates", "app/tools/notes_tool/templates"])

# Structure: {user_id: [{"id": str, "content": str, "width": int, "height": int, "color": str, "x": int, "y": int}]}
NOTES_DB = {}

class NoteUpdate(BaseModel):
    content: Optional[str] = None
    width: Optional[str] = None
    height: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None

@router.get("/")
def notes_home(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?error=Please login first")
    
    user_notes = NOTES_DB.get(user_id, [])
    return templates.TemplateResponse("notes.html", {"request": request, "notes": user_notes})

@router.post("/add")
def add_note(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user_id not in NOTES_DB:
        NOTES_DB[user_id] = []
    
    import random
    new_note = {
        "id": str(uuid.uuid4()),
        "content": "",
        "width": "250px",
        "height": "250px",
        "color": "#ffeb3b", # Default yellow
        "x": random.randint(50, 300),
        "y": random.randint(50, 300)
    }
    NOTES_DB[user_id].append(new_note)
    return JSONResponse(content=new_note)

@router.put("/update/{note_id}")
def update_note(note_id: str, update: NoteUpdate, request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_notes = NOTES_DB.get(user_id, [])
    for note in user_notes:
        if note["id"] == note_id:
            if update.content is not None:
                note["content"] = update.content
            if update.width is not None:
                note["width"] = update.width
            if update.height is not None:
                note["height"] = update.height
            if update.x is not None:
                note["x"] = update.x
            if update.y is not None:
                note["y"] = update.y
            return JSONResponse(content={"status": "success"})
            
    raise HTTPException(status_code=404, detail="Note not found")

@router.delete("/delete/{note_id}")
def delete_note(note_id: str, request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user_id in NOTES_DB:
        NOTES_DB[user_id] = [n for n in NOTES_DB[user_id] if n["id"] != note_id]
        
    return JSONResponse(content={"status": "success"})

from fastapi import APIRouter, Request, Depends, Body, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
import uuid
from pydantic import BaseModel
from typing import Optional
import random
from datetime import datetime
import json

router = APIRouter(
    prefix="/tools/notes",
    tags=["notes"]
)

templates = Jinja2Templates(directory=["app/templates", "app/tools/notes_tool/templates"])

# Structure: {user_id: [{"id": str, "content": str, "width": int, "height": int, "color": str, "x": int, "y": int, "type": str, "updated_at": str}]}
NOTES_DB = {}

class NoteUpdate(BaseModel):
    content: Optional[str] = None
    width: Optional[str] = None
    height: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    type: Optional[str] = None
    title: Optional[str] = None
    deadline: Optional[str] = None

@router.get("/")
def notes_dashboard(request: Request):
    """Render the main dashboard for selecting note types."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?error=Please login first")
    return templates.TemplateResponse("notes_dashboard.html", {"request": request})

@router.get("/sticky")
def notes_sticky(request: Request):
    """Render the sticky notes canvas."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?error=Please login first")
    
    all_notes = NOTES_DB.get(user_id, [])
    # Filter for sticky notes only
    sticky_notes = [n for n in all_notes if n.get("type", "sticky") == "sticky"]
    return templates.TemplateResponse("notes.html", {"request": request, "notes": sticky_notes})

@router.get("/list/{note_type}")
def notes_list(request: Request, note_type: str):
    """Render a list of notes of a specific type (doc or todo)."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?error=Please login first")
    
    if note_type not in ['doc', 'todo']:
        return RedirectResponse(url="/tools/notes")

    all_notes = NOTES_DB.get(user_id, [])
    filtered_notes = []
    
    for n in all_notes:
        if n.get("type") == note_type:
            note_copy = n.copy()
            
            # Calculate item count for todos
            if note_type == 'todo':
                try:
                    items = json.loads(n.get("content", "[]"))
                    note_copy["item_count"] = len(items)
                    if items and all(item.get("done", False) for item in items):
                        note_copy["all_completed"] = True
                    else:
                        note_copy["all_completed"] = False
                except:
                    note_copy["item_count"] = 0
                    note_copy["all_completed"] = False
            
            # Format date
            updated_at = n.get("updated_at")
            if updated_at:
                try:
                    dt = datetime.fromisoformat(updated_at)
                    note_copy["formatted_date"] = dt.strftime("%b %d, %Y %H:%M")
                except:
                    note_copy["formatted_date"] = "Unknown"
            else:
                note_copy["formatted_date"] = "Just now"
                
            filtered_notes.append(note_copy)
    
    # Sort by updated_at desc
    filtered_notes.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    
    return templates.TemplateResponse("notes_list.html", {
        "request": request, 
        "notes": filtered_notes, 
        "type": note_type,
        "type_name": "Documents" if note_type == 'doc' else "To-Do Lists"
    })

@router.get("/edit/{note_type}/{note_id}")
def edit_note(request: Request, note_type: str, note_id: str):
    """Render the dedicated editor for a note."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?error=Please login first")

    all_notes = NOTES_DB.get(user_id, [])
    note = next((n for n in all_notes if n["id"] == note_id), None)
    
    if not note:
        return RedirectResponse(url=f"/tools/notes/list/{note_type}?error=Note not found")

    template_name = "doc_editor.html" if note_type == 'doc' else "todo_editor.html"
    return templates.TemplateResponse(template_name, {"request": request, "note": note})

@router.post("/add")
def add_note(request: Request, note_type: str = Body(..., embed=True)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user_id not in NOTES_DB:
        NOTES_DB[user_id] = []
    
    new_note = {
        "id": str(uuid.uuid4()),
        "content": "",
        "width": "250px",
        "height": "250px",
        "color": "#ffeb3b",
        "x": random.randint(50, 300),
        "y": random.randint(50, 300),
        "type": note_type,
        "title": "Untitled",
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    
    if note_type == 'todo':
        new_note['color'] = '#e1f5fe'
        new_note['content'] = '[]'
        new_note['title'] = 'New To-Do List'
    elif note_type == 'doc':
        new_note['color'] = '#f3e5f5'
        new_note['content'] = ''
        new_note['title'] = 'New Document'

    NOTES_DB[user_id].append(new_note)
    return JSONResponse(content=new_note)

@router.put("/update/{note_id}")
async def update_note(note_id: str, update: NoteUpdate, request: Request):
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
            if update.title is not None:
                note["title"] = update.title
            if update.deadline is not None:
                note["deadline"] = update.deadline
            
            note["updated_at"] = datetime.utcnow().isoformat() + "Z"
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

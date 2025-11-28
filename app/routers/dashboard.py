from fastapi import APIRouter, Depends, Request, Cookie
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .. import models, database
from ..database import get_db

router = APIRouter(
    tags=["dashboard"]
)

templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
async def dashboard(request: Request, user_id: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if not user_id:
        return RedirectResponse(url="/?error=Please login first")
    
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/?error=User not found")
        
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

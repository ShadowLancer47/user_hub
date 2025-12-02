from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from .scraper import scrape_champion

router = APIRouter(
    prefix="/tools/lol",
    tags=["lol"]
)

templates = Jinja2Templates(directory=["app/templates", "app/tools/lol_tool/templates"])

@router.get("/")
def lol_dashboard(request: Request):
    """Render the LoL tool dashboard."""
    return templates.TemplateResponse("lol_dashboard.html", {"request": request})

@router.get("/search")
def search_champion(champion: str = Query(...)):
    """Search for champion data."""
    try:
        data = scrape_champion(champion)
        if not data:
            return JSONResponse(content={"error": "Champion not found or data unavailable"}, status_code=404)
        return JSONResponse(content=data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(content={"error": f"Internal Server Error: {str(e)}"}, status_code=500)

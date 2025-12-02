from fastapi import APIRouter, Request, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import yt_dlp
import os
import uuid
import asyncio

router = APIRouter()
templates = Jinja2Templates(directory=["app/templates", "app/tools/youtube_tool/templates"])

# Temporary storage for downloads
DOWNLOAD_DIR = "app/static/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def cleanup_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

@router.get("/tools/youtube", response_class=HTMLResponse)
async def youtube_page(request: Request):
    return templates.TemplateResponse("youtube.html", {"request": request})

@router.post("/tools/youtube/info")
async def get_video_info(url: str = Form(...)):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Extract relevant info
            video_info = {
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration'),
                "formats": []
            }
            
            # Simplify formats for the UI
            # We'll just offer generic quality options in the UI and let yt-dlp pick the best match
            # But we can return some metadata if needed.
            # For now, just returning basic info is enough as we'll use format strings for downloading.
            
            return JSONResponse(content=video_info)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/tools/youtube/download")
async def download_video(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    type: str = Form(...), # 'video' or 'audio'
    quality: str = Form(...), # 'best', '1080p', '720p', 'audio_best'
    title: str = Form(None)
):
    try:
        file_id = str(uuid.uuid4())
        output_template = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")
        
        # Base options
        ydl_opts = {
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
        }

        if type == 'audio':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
            # Audio download
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: _download(ydl_opts, url))
            
        else:
            # Video download with fallback
            # Try preferred format first (H.264/AAC for compatibility)
            preferred_format = None
            if quality == 'best':
                preferred_format = 'bestvideo[ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            elif quality == '1080p':
                preferred_format = 'bestvideo[height<=1080][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best'
            elif quality == '720p':
                preferred_format = 'bestvideo[height<=720][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
            elif quality == '480p':
                preferred_format = 'bestvideo[height<=480][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'
            else:
                preferred_format = 'bestvideo[ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            
            ydl_opts['format'] = preferred_format
            ydl_opts['merge_output_format'] = 'mp4'

            loop = asyncio.get_running_loop()
            try:
                await loop.run_in_executor(None, lambda: _download(ydl_opts, url))
            except Exception as e:
                print(f"Preferred format download failed: {e}. Retrying with standard format...")
                # Fallback to standard best format if preferred fails
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
                # We still try to merge to mp4 if possible, but let yt-dlp decide if it needs to
                # If ffmpeg is missing, this might still fail on merge, but at least we tried.
                await loop.run_in_executor(None, lambda: _download(ydl_opts, url))

        # Find the downloaded file
        downloaded_file = None
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(file_id):
                downloaded_file = os.path.join(DOWNLOAD_DIR, f)
                break
        
        if not downloaded_file:
            raise Exception("Download failed: File not found on server")

        # Determine filename
        if title:
            # Sanitize title
            import re
            safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
            safe_title = safe_title.strip()
            ext = os.path.splitext(downloaded_file)[1]
            filename = f"{safe_title}{ext}"
        else:
            filename = os.path.basename(downloaded_file)
        
        background_tasks.add_task(cleanup_file, downloaded_file)

        return FileResponse(
            downloaded_file, 
            filename=filename, 
            media_type="application/octet-stream"
        )

    except Exception as e:
        print(f"Download Error: {str(e)}") # Log to console
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

def _download(opts, url):
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

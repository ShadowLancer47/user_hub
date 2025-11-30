from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import shutil
import os
import uuid
import mammoth
from weasyprint import HTML
from moviepy import VideoFileClip, AudioFileClip, ColorClip
from pdf2docx import Converter

router = APIRouter()
templates = Jinja2Templates(directory=["app/templates", "app/tools/converter_tool/templates"])

# Temporary storage for uploaded files
UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/tools/converter", response_class=HTMLResponse)
async def converter_page(request: Request):
    return templates.TemplateResponse("converter.html", {"request": request})

@router.post("/tools/converter/upload")
async def upload_file(file: UploadFile = File(...)):
    file_ext = file.filename.split('.')[-1].lower()
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{file_ext}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    options = []
    if file_ext in ['png', 'jpg', 'jpeg', 'webp', 'bmp']:
        options = [fmt for fmt in ['png', 'jpg', 'webp', 'bmp'] if fmt != file_ext]
    elif file_ext == 'csv':
        options = ['json']
    elif file_ext == 'json':
        options = ['csv']
    elif file_ext == 'docx':
        options = ['pdf']
    elif file_ext == 'pdf':
        options = ['docx']
    elif file_ext == 'mp4':
        options = ['mp3']
    elif file_ext == 'mp3':
        options = ['mp4']
    
    return JSONResponse(content={
        "file_id": file_id,
        "file_ext": file_ext,
        "options": options
    })

@router.post("/tools/converter/convert")
async def convert_file(
    file_id: str = Form(...), 
    target_format: str = Form(...), 
    original_ext: str = Form(...),
    original_filename: str = Form(...)
):
    input_path = os.path.join(UPLOAD_DIR, f"{file_id}.{original_ext}")
    output_filename = f"{file_id}.{target_format}"
    output_path = os.path.join(UPLOAD_DIR, output_filename)
    
    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Image Conversion
        if original_ext in ['png', 'jpg', 'jpeg', 'webp', 'bmp']:
            from PIL import Image
            with Image.open(input_path) as img:
                save_format = target_format.upper()
                if save_format == 'JPG':
                    save_format = 'JPEG'
                
                if save_format == 'JPEG':
                    img = img.convert('RGB')
                
                img.save(output_path, save_format)
        
        # CSV to JSON
        elif original_ext == 'csv' and target_format == 'json':
            import csv
            import json
            data = []
            with open(input_path, 'r', encoding='utf-8') as csvf:
                reader = csv.DictReader(csvf)
                for row in reader:
                    data.append(row)
            with open(output_path, 'w', encoding='utf-8') as jsonf:
                json.dump(data, jsonf, indent=4)
        
        # JSON to CSV
        elif original_ext == 'json' and target_format == 'csv':
            import csv
            import json
            with open(input_path, 'r', encoding='utf-8') as jsonf:
                data = json.load(jsonf)
            
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                headers = data[0].keys()
                with open(output_path, 'w', newline='', encoding='utf-8') as csvf:
                    writer = csv.DictWriter(csvf, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(data)
            else:
                raise HTTPException(status_code=400, detail="Invalid JSON structure for CSV conversion")
        
        # DOCX -> PDF
        elif original_ext == 'docx' and target_format == 'pdf':
            with open(input_path, "rb") as docx_file:
                result = mammoth.convert_to_html(docx_file)
                html = result.value
                HTML(string=html).write_pdf(output_path)

        # PDF -> DOCX
        elif original_ext == 'pdf' and target_format == 'docx':
            cv = Converter(input_path)
            cv.convert(output_path)
            cv.close()

        # MP4 -> MP3
        elif original_ext == 'mp4' and target_format == 'mp3':
            video = VideoFileClip(input_path)
            video.audio.write_audiofile(output_path)
            video.close()

        # MP3 -> MP4
        elif original_ext == 'mp3' and target_format == 'mp4':
            audio = AudioFileClip(input_path)
            # Create a black background video with the same duration as the audio
            # Size 640x480 is arbitrary but standard
            video = ColorClip(size=(640, 480), color=(0, 0, 0), duration=audio.duration)
            video = video.set_audio(audio)
            video.write_videofile(output_path, fps=24)
            audio.close()
            video.close()
        
        else:
             raise HTTPException(status_code=400, detail="Unsupported conversion")
             
        # Construct new filename: [original_name]_converted.[target_format]
        base_name = os.path.splitext(original_filename)[0]
        download_filename = f"{base_name}_converted.{target_format}"
        
        return FileResponse(output_path, filename=download_filename)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

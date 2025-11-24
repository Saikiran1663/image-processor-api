from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse, JSONResponse
from PIL import Image
from io import BytesIO
from typing import Optional

app = FastAPI()

# Available size options
SIZE_OPTIONS = {
    "512": 512,
    "768": 768,
    "1024": 1024,  # Default
    "1536": 1536,
    "2048": 2048,
    "original": None  # Keep original size
}


def process_image_bytes(image_bytes: bytes, max_dimension: Optional[int] = 1024) -> bytes:
    with Image.open(BytesIO(image_bytes)) as img:
        width, height = img.size
        
        # Resize if max_dimension is specified and image is larger
        if max_dimension and (width > max_dimension or height > max_dimension):
            if width > height:
                ratio = max_dimension / float(width)
                new_width = max_dimension
                new_height = int(height * ratio)
            else:
                ratio = max_dimension / float(height)
                new_width = int(width * ratio)
                new_height = max_dimension
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        img = img.convert("L")

        output = BytesIO()
        img.save(output, format="JPEG", quality=85)
        return output.getvalue()


@app.get("/size-options")
async def get_size_options():
    """Returns available size options for image transformation"""
    options = []
    for key, value in SIZE_OPTIONS.items():
        if value is None:
            options.append({
                "value": key,
                "label": "Original Size",
                "dimension": None,
                "is_default": False
            })
        else:
            options.append({
                "value": key,
                "label": f"{value}px",
                "dimension": value,
                "is_default": (key == "1024")
            })
    return JSONResponse(content={
        "size_options": options,
        "default": "1024"
    })


@app.post("/process-image")
async def process_image(
    file: UploadFile = File(...),
    size: str = Form(default="1024")
):
    try:
        # Validate size option
        if size not in SIZE_OPTIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid size option. Available options: {', '.join(SIZE_OPTIONS.keys())}"
            )
        
        max_dimension = SIZE_OPTIONS[size]
        image_bytes = await file.read()
        processed_image = process_image_bytes(image_bytes, max_dimension)
        output = BytesIO(processed_image)

        headers = {"Content-Disposition": f"attachment; filename=processed_{file.filename or 'image.jpg'}"}

        return StreamingResponse(output, media_type="image/jpeg", headers=headers)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



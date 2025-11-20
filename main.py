from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image
from io import BytesIO

app = FastAPI()


def process_image_bytes(image_bytes: bytes) -> bytes:
    with Image.open(BytesIO(image_bytes)) as img:
        width, height = img.size
        if width > 1080:
            ratio = 1080 / float(width)
            img = img.resize((1080, int(height * ratio)), Image.Resampling.LANCZOS)
        img = img.convert("L")

        output = BytesIO()
        img.save(output, format="JPEG", quality=85)
        return output.getvalue()


@app.post("/process-image")
async def process_image(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        processed_image = process_image_bytes(image_bytes)
        output = BytesIO(processed_image)

        headers = {"Content-Disposition": f"attachment; filename=processed_{file.filename or 'image.jpg'}"}

        return StreamingResponse(output, media_type="image/jpeg", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



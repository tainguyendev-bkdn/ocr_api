from fastapi import FastAPI, UploadFile, File
import uuid, os

from input_loader import load_input_file
from ocr_pipeline import ocr_image_pipeline

app = FastAPI()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/ocr")
async def unified_ocr(file: UploadFile = File(...)):
    # Lưu file tạm
    ext = file.filename.split(".")[-1]
    save_path = f"{UPLOAD_DIR}/{uuid.uuid4()}.{ext}"

    with open(save_path, "wb") as f:
        f.write(await file.read())

    # Convert input -> list ảnh PNG
    images = load_input_file(save_path)

    # OCR tất cả ảnh (PDF nhiều trang)
    results = []
    for idx, img_path in enumerate(images):
        text_blocks = ocr_image_pipeline(img_path)
        results.append({
            "page": idx + 1,
            "results": text_blocks
        })

    return {
        "filename": file.filename,
        "pages": results
    }

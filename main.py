import os
import shutil
import uuid
from tempfile import SpooledTemporaryFile

from fastapi import FastAPI, File, HTTPException, UploadFile

from input_loaded import load_input_file
from ocr_pipline import ocr_image_pipeline

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_UPLOAD_SIZE_MB = 25
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
MAX_PDF_PAGES = 25
CHUNK_SIZE = 1 * 1024 * 1024  # 1MB
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/bmp",
    "image/tiff",
    "image/heif",
    "image/heic",
}


def validate_upload(file: UploadFile):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File không hợp lệ")

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Định dạng '{file.content_type}' không được hỗ trợ",
        )


def _safe_remove(path: str):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


async def stream_upload_to_disk(file: UploadFile, destination: str) -> int:
    """Đọc file theo từng chunk và ghi ra đĩa qua SpooledTemporaryFile."""
    total_bytes = 0
    await file.seek(0)

    with SpooledTemporaryFile(max_size=MAX_UPLOAD_SIZE_BYTES) as spool:
        while True:
            chunk = await file.read(CHUNK_SIZE)
            if not chunk:
                break

            total_bytes += len(chunk)
            if total_bytes > MAX_UPLOAD_SIZE_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"Kích thước vượt {MAX_UPLOAD_SIZE_MB}MB",
                )

            spool.write(chunk)

        spool.seek(0)
        with open(destination, "wb") as out_file:
            shutil.copyfileobj(spool, out_file)

    await file.close()
    return total_bytes


@app.post("/ocr")
async def unified_ocr(file: UploadFile = File(...)):
    validate_upload(file)

    ext = file.filename.split(".")[-1]
    save_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.{ext}")
    image_bundle = None

    try:
        await stream_upload_to_disk(file, save_path)
        try:
            image_bundle = load_input_file(
                save_path,
                upload_dir=UPLOAD_DIR,
                max_pdf_pages=MAX_PDF_PAGES
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        pages = []

        for idx, img_path in enumerate(image_bundle):
            try:
                results, full_text = ocr_image_pipeline(img_path)

                pages.append({
                    "page": idx + 1,
                    "results": results,
                    "full_text": full_text
                })

            except Exception as e:
                pages.append({
                    "page": idx + 1,
                    "results": [],
                    "full_text": "",
                    "error": f"Lỗi OCR trang {idx+1}: {str(e)}"
                })

        return {
            "filename": file.filename,
            "pages": pages
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if image_bundle:
            image_bundle.cleanup()
        _safe_remove(save_path)

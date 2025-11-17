import os
import uuid
from typing import List, Optional

import fitz                 # PDF
import pillow_heif          # đọc HEIC/HEIF
from PIL import Image, UnidentifiedImageError


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class LoadedImages(list):
    """Danh sách đường dẫn ảnh tạm có kèm cleanup()."""

    def cleanup(self):
        for path in list(self):
            try:
                os.remove(path)
            except FileNotFoundError:
                continue


def _ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def _cleanup_paths(paths: List[str]):
    for path in paths:
        try:
            os.remove(path)
        except FileNotFoundError:
            continue


def save_temp_image(image: Image.Image, upload_dir: str):
    """Lưu ảnh PIL thành PNG 24bit."""
    _ensure_dir(upload_dir)
    path = os.path.join(upload_dir, f"{uuid.uuid4()}.png")
    image.convert("RGB").save(path, format="PNG")
    return path


def handle_pdf(path: str, upload_dir: str, max_pages: Optional[int] = None):
    """Tách PDF thành danh sách các ảnh PNG."""
    output_images: List[str] = []

    try:
        with fitz.open(path) as pdf:
            total_pages = len(pdf)
            if max_pages is not None and total_pages > max_pages:
                raise Exception(
                    f"PDF có {total_pages} trang, vượt giới hạn {max_pages} trang"
                )

            for page in pdf:
                pix = page.get_pixmap(dpi=200)
                img_path = os.path.join(upload_dir, f"{uuid.uuid4()}.png")
                pix.save(img_path)
                output_images.append(img_path)

        return output_images

    except Exception as e:
        _cleanup_paths(output_images)
        raise Exception(f"Không thể xử lý PDF: {e}")


def handle_heic(path: str, upload_dir: str):
    """Chuyển HEIC → PNG"""
    try:
        heif_file = pillow_heif.read_heif(path)
        image = Image.frombytes(
            heif_file.mode,
            heif_file.size,
            heif_file.data
        )
        image = image.convert("RGB")
        return [save_temp_image(image, upload_dir)]

    except Exception as e:
        raise Exception(f"Lỗi đọc HEIC/HEIF: {e}")


def handle_normal_image(path: str, upload_dir: str):
    """PNG, JPG, JPEG, BMP, WEBP, TIFF…"""
    try:
        img = Image.open(path)
        img = img.convert("RGB")
        return [save_temp_image(img, upload_dir)]

    except UnidentifiedImageError:
        raise Exception(f"Không thể nhận dạng định dạng ảnh: {path}")

    except Exception as e:
        raise Exception(f"Lỗi đọc ảnh: {e}")


def load_input_file(
    path: str,
    upload_dir: Optional[str] = None,
    max_pdf_pages: Optional[int] = None
):
    """
    Trả về danh sách ảnh PNG để đưa vào OCR.
    PDF -> nhiều ảnh
    HEIC -> 1 ảnh PNG
    PNG/JPG/etc -> 1 ảnh PNG
    """

    target_dir = _ensure_dir(upload_dir or UPLOAD_DIR)
    ext = os.path.splitext(path)[1].lower().strip()

    if ext == ".pdf":
        return LoadedImages(handle_pdf(path, target_dir, max_pages=max_pdf_pages))

    if ext in [".heic", ".heif"]:
        return LoadedImages(handle_heic(path, target_dir))

    # Bao quát mọi định dạng ảnh còn lại
    return LoadedImages(handle_normal_image(path, target_dir))

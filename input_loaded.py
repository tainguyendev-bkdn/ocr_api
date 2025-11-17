import os
import uuid
import fitz                 # PDF
from PIL import Image
import pillow_heif          # đọc HEIC/HEIF


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_temp_image(image: Image.Image):
    """Lưu ảnh PIL thành đường dẫn file PNG."""
    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.png")
    image.save(path, format="PNG")
    return path


def handle_pdf(path):
    """Tách PDF thành danh sách các ảnh PNG."""
    pdf = fitz.open(path)
    output_images = []

    for i in range(len(pdf)):
        page = pdf[i]
        pix = page.get_pixmap(dpi=200)
        img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.png")
        pix.save(img_path)
        output_images.append(img_path)

    return output_images


def handle_heic(path):
    """Chuyển HEIC → PNG"""
    heif_file = pillow_heif.read_heif(path)
    image = Image.frombytes(
        heif_file.mode,
        heif_file.size,
        heif_file.data
    )
    return [save_temp_image(image)]


def handle_normal_image(path):
    """PNG, JPG, JPEG, BMP, WEBP, TIFF…"""
    img = Image.open(path).convert("RGB")
    return [save_temp_image(img)]


def load_input_file(path):
    """
    Trả về danh sách ảnh PNG để đưa vào OCR.
    PDF -> nhiều ảnh
    HEIC -> 1 ảnh PNG
    PNG/JPG/etc -> 1 ảnh PNG
    """

    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        return handle_pdf(path)

    if ext in [".heic", ".heif"]:
        return handle_heic(path)

    # Bao quát mọi ảnh còn lại
    return handle_normal_image(path)

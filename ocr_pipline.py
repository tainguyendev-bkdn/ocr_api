import cv2
import torch
from paddleocr import PaddleOCR
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg
from PIL import Image


# ----------------------------
#   Runtime device selection
# ----------------------------
USE_GPU = torch.cuda.is_available()


# ----------------------------
#   PaddleOCR detect-only
# ----------------------------
paddle_det = PaddleOCR(
    lang="vi",
    use_angle_cls=True,
    det=True,
    rec=False,
    use_gpu=USE_GPU
)

# ----------------------------
#   VietOCR rec-only
# ----------------------------
cfg = Cfg.load_config_from_name("vgg_transformer")
cfg["device"] = "cuda" if USE_GPU else "cpu"
cfg["cnn"]["pretrained"] = False
vietocr = Predictor(cfg)


# ----------------------------
#   Merge BBOX -> thành full text
# ----------------------------
def merge_full_text(results):
    """
    Gộp text theo vị trí bbox.
    Sort theo Y trước, X sau.
    """

    def sort_key(item):
        bbox = item["bbox"]
        return (bbox[0][1], bbox[0][0])   # (y, x)

    if not results:
        return ""

    sorted_items = sorted(results, key=sort_key)
    lines = [item["text"] for item in sorted_items if item["text"].strip()]

    return "\n".join(lines)


# ----------------------------
#   Full OCR Pipeline
# ----------------------------
def ocr_image_pipeline(image_path):
    """
    Detect text = PaddleOCR
    Recognize text = VietOCR
    Trả về:
    - results: list {bbox, text}
    - full_text: text gộp
    """

    # Load ảnh bằng OpenCV
    img = cv2.imread(image_path)

    if img is None:
        raise Exception(f"Không đọc được ảnh: {image_path}")

    # Detect
    det = paddle_det.ocr(image_path)

    results = []

    for box in det:
        pts = box[0]    # tọa độ 4 điểm

        x1, y1 = int(pts[0][0]), int(pts[0][1])
        x2, y2 = int(pts[2][0]), int(pts[2][1])

        # Validate trước khi crop
        if x1 >= x2 or y1 >= y2:
            continue

        crop = img[y1:y2, x1:x2]

        if crop is None or crop.size == 0:
            continue

        # Convert sang PIL
        crop_pil = Image.fromarray(crop)

        # VietOCR
        try:
            text = vietocr.predict(crop_pil)
        except Exception:
            text = ""

        results.append({
            "bbox": pts,
            "text": text
        })

    # -------------------
    # Gộp text
    # -------------------
    full_text = merge_full_text(results)

    return results, full_text

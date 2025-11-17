import cv2
import numpy as np
from paddleocr import PaddleOCR
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg
from PIL import Image


# --- PaddleOCR detect-only ---
paddle_det = PaddleOCR(
    lang='vi',
    use_angle_cls=True,
    det=True,
    rec=False
)

# --- VietOCR rec-only ---
cfg = Cfg.load_config_from_name('vgg_transformer')
cfg['device'] = 'cpu'      # hoặc "cuda:0"
cfg['cnn']['pretrained'] = False
vietocr = Predictor(cfg)


def ocr_image_pipeline(image_path):
    """Detect text box bằng Paddle -> Recognize bằng VietOCR"""

    # Load image
    img = cv2.imread(image_path)

    # Detect (PaddleOCR)
    det = paddle_det.ocr(image_path)

    results = []

    for box in det:
        pts = box[0]  # bbox 4 điểm

        # Crop box
        x1, y1 = int(pts[0][0]), int(pts[0][1])
        x2, y2 = int(pts[2][0]), int(pts[2][1])

        crop = img[y1:y2, x1:x2]
        if crop.size == 0:
            continue

        crop_pil = Image.fromarray(crop)

        # Recognize (VietOCR)
        text = vietocr.predict(crop_pil)

        results.append({
            "bbox": pts,
            "text": text
        })

    return results

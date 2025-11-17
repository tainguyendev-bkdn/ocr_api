# OCR API

FastAPI service chạy OCR bằng PaddleOCR (detect) và VietOCR (recognize). Hỗ trợ upload PDF/ảnh nhiều định dạng, tự chia trang, chạy trên GPU nếu có.

## Yêu cầu hệ thống
- Python 3.10–3.13 (khuyến nghị 3.10/3.11 để dễ cài PaddlePaddle)
- Pip + virtualenv
- Visual C++ Build Tools (Windows) hoặc build essentials (Linux) để cài PyMuPDF
- GPU CUDA (tuỳ chọn) nếu muốn chạy nhanh hơn

## Cài đặt
```bash
python -m venv .venv
.venv\Scripts\activate            # Windows PowerShell/CMD
# source .venv/bin/activate       # Linux/macOS

pip install --upgrade pip
pip install -r requirements.txt
```

> ⚠️ Trên Windows, PaddlePaddle chỉ có sẵn bản CPU `pip install paddlepaddle==3.0.0` hoặc bản GPU qua wheel riêng. Nếu dòng `paddlepaddle==2.6.0` không cài được, chọn phiên bản tương thích theo [docs](https://www.paddlepaddle.org.cn/).

## Chạy server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Endpoint thử: `POST http://localhost:8000/ocr` (multipart form field `file`).

### Ví dụ gọi API
```bash
curl -X POST http://localhost:8000/ocr ^
  -H "accept: application/json" ^
  -H "Content-Type: multipart/form-data" ^
  -F "file=@sample.pdf"
```

Postman: tạo request `POST /ocr`, tab Body → `form-data`, key `file` kiểu File và chọn tài liệu cần OCR, gửi và xem JSON trả về.

Giới hạn mặc định:
- Kích thước file ≤ 25 MB
- PDF tối đa 25 trang
- Chỉ nhận MIME type khai báo trong `ALLOWED_CONTENT_TYPES`

Các file tạm được lưu tại `uploads/` và tự xoá sau mỗi request.

## Chạy test
```bash
pytest
```

Test hiện tại tập trung vào `load_input_file` (convert ảnh/PDF và cleanup). Thêm test mới tại `tests/`.

## Chạy bằng Docker (tuỳ chọn)
```bash
docker build -t ocr-api .
docker run --rm -p 8000:8000 ocr-api
```

Ví dụ Dockerfile cơ bản:
```Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Nếu dùng GPU cần base image hỗ trợ CUDA và cài paddlepaddle-gpu tương ứng.

## Cấu trúc thư mục
```
ocr_api/
├── main.py              # FastAPI endpoint & upload guard
├── ocr_pipline.py       # Paddle detect + VietOCR recog
├── input_loaded.py      # Chuyển PDF/HEIC/ảnh → PNG, cleanup
├── utils_pdf.py         # (tuỳ chọn) helper PDF
├── tests/               # Pytest
├── requirements.txt
└── uploads/             # Thư mục file tạm (tự tạo)
```

## Ghi chú triển khai
- Đặt biến môi trường `PADDLEOCR_HOME` nếu cần cache model ở thư mục riêng.
- Với GPU, đảm bảo driver + CUDA phù hợp và cài paddlepaddle-gpu tương ứng.
- Có thể chỉnh `MAX_UPLOAD_SIZE_MB` hoặc `MAX_PDF_PAGES` trong `main.py` cho phù hợp workload.


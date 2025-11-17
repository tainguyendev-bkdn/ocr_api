import os
from pathlib import Path

import fitz
import pytest
from PIL import Image

from input_loaded import load_input_file


def test_load_input_file_converts_image_and_cleanup(tmp_path):
    upload_dir = tmp_path / "uploads"
    source_image = tmp_path / "sample.jpg"
    Image.new("RGB", (32, 32), color="red").save(source_image, format="JPEG")

    loaded = load_input_file(str(source_image), upload_dir=str(upload_dir))

    assert len(loaded) == 1
    png_path = Path(loaded[0])
    assert png_path.suffix == ".png"
    assert png_path.exists()

    loaded.cleanup()
    assert not list(upload_dir.glob("*.png"))


def test_load_input_file_enforces_pdf_page_limit(tmp_path):
    upload_dir = tmp_path / "uploads"
    pdf_path = tmp_path / "sample.pdf"

    doc = fitz.open()
    for _ in range(3):
        doc.new_page()
    doc.save(pdf_path)
    doc.close()

    with pytest.raises(Exception):
        load_input_file(
            str(pdf_path),
            upload_dir=str(upload_dir),
            max_pdf_pages=1
        )

    assert not list(Path(upload_dir).glob("*.png"))


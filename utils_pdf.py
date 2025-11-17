import fitz
import uuid
import os

def pdf_to_images(pdf_path, output_folder="uploads"):
    pdf = fitz.open(pdf_path)
    image_paths = []

    for i in range(len(pdf)):
        page = pdf[i]
        pix = page.get_pixmap(dpi=200)
        img_path = os.path.join(output_folder, f"{uuid.uuid4()}.png")
        pix.save(img_path)
        image_paths.append(img_path)

    return image_paths

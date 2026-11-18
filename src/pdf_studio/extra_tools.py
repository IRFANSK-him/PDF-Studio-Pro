"""Additional non-destructive educational PDF utilities."""
from pathlib import Path
import fitz
from .page_tools import _open_pdf, _output_path

def images_to_pdf(images, output):
    sources = [Path(p) for p in images]
    if not sources:
        raise ValueError("Select at least one image")
    destination = _output_path(output, sources)
    doc = fitz.open()
    try:
        for path in sources:
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}:
                raise ValueError("Unsupported image format")
            image = fitz.open(str(path))
            try:
                pdf = fitz.open("pdf", image.convert_to_pdf())
                try:
                    doc.insert_pdf(pdf)
                finally:
                    pdf.close()
            finally:
                image.close()
        doc.save(str(destination), garbage=4, deflate=True)
    finally:
        doc.close()
    return destination

def compress_pdf(path, output):
    destination = _output_path(output, [path])
    doc = _open_pdf(path)
    try:
        doc.save(str(destination), garbage=4, deflate=True, deflate_images=True, deflate_fonts=True)
    finally:
        doc.close()
    return destination

def crop_pages(path, page_indices, margins, output):
    destination = _output_path(output, [path])
    doc = _open_pdf(path)
    try:
        indices = set(page_indices)
        if not indices or any(i < 0 or i >= doc.page_count for i in indices):
            raise ValueError("Invalid pages")
        left, top, right, bottom = margins
        if min(margins) < 0:
            raise ValueError("Margins cannot be negative")
        for i in indices:
            page = doc[i]
            box = page.cropbox
            rect = fitz.Rect(box.x0 + left, box.y0 + top, box.x1 - right, box.y1 - bottom)
            if rect.is_empty or rect.is_infinite:
                raise ValueError("Cropping removes the entire page")
            page.set_cropbox(rect)
        doc.save(str(destination), garbage=4, deflate=True)
    finally:
        doc.close()
    return destination

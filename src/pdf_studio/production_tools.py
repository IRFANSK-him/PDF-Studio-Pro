"""PDF export, watermark, image insertion, and metadata tools.

Every PDF mutation saves to a new path. Raster exports are not editable PDFs.
"""
from pathlib import Path
import fitz
from .page_tools import _open_pdf, _output_path


def export_page_images(path, folder, dpi=150):
    if not 72 <= dpi <= 300:
        raise ValueError("DPI must be between 72 and 300")
    target = Path(folder).expanduser().resolve()
    if not target.is_dir():
        raise ValueError("Output folder must exist")
    doc = _open_pdf(path)
    try:
        outputs = [target / f"{Path(path).stem}_{i + 1:03}.png"
                   for i in range(doc.page_count)]
        if any(p.exists() for p in outputs):
            raise FileExistsError("An exported page image already exists")
        for page, output in zip(doc, outputs):
            page.get_pixmap(dpi=dpi, alpha=False).save(str(output))
        return outputs
    finally:
        doc.close()


def watermark_pdf(path, output, text, opacity=0.2):
    if not text.strip():
        raise ValueError("Watermark cannot be empty")
    if not 0 < opacity <= 1:
        raise ValueError("Opacity must be in (0, 1]")
    destination = _output_path(output, [path])
    doc = _open_pdf(path)
    try:
        for page in doc:
            rect = page.rect
            length = max(12, min(44, rect.width / max(len(text), 1) * 1.5))
            page.insert_text(
                (rect.width * 0.15, rect.height * 0.5), text,
                fontsize=length, color=(0.55, 0.55, 0.55),
                fill_opacity=opacity, overlay=True
            )
        doc.save(str(destination), garbage=4, deflate=True)
    finally:
        doc.close()
    return destination


def insert_image(path, page_index, image_path, output, x=72, y=72, width=180):
    if width <= 0:
        raise ValueError("Image width must be positive")
    image = Path(image_path)
    if image.suffix.lower() not in (".png", ".jpg", ".jpeg"):
        raise ValueError("Select a PNG or JPEG image")
    destination = _output_path(output, [path])
    doc = _open_pdf(path)
    try:
        if not 0 <= page_index < doc.page_count:
            raise ValueError("Page out of range")
        page = doc[page_index]
        pix = fitz.Pixmap(str(image))
        try:
            height = width * pix.height / pix.width
        finally:
            pix = None
        rect = fitz.Rect(x, y, x + width, y + height)
        if not page.rect.contains(rect):
            raise ValueError("Image must fit inside the page")
        page.insert_image(rect, filename=str(image))
        doc.save(str(destination), garbage=4, deflate=True)
    finally:
        doc.close()
    return destination


def set_metadata(path, output, title="", author="", subject=""):
    destination = _output_path(output, [path])
    doc = _open_pdf(path)
    try:
        metadata = dict(doc.metadata)
        metadata.update({"title": title, "author": author, "subject": subject})
        doc.set_metadata(metadata)
        doc.save(str(destination), garbage=4, deflate=True)
    finally:
        doc.close()
    return destination

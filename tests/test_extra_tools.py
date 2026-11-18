import sys
from pathlib import Path
import fitz
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pdf_studio.extra_tools import images_to_pdf, compress_pdf, crop_pages

def test_image_conversion(tmp_path):
    image = tmp_path / "image.png"
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 20, 30), False)
    pix.clear_with(200)
    pix.save(image)
    output = tmp_path / "converted.pdf"
    images_to_pdf([image], output)
    with fitz.open(output) as doc:
        assert doc.page_count == 1

def test_compress_and_crop(tmp_path):
    original = tmp_path / "input.pdf"
    doc = fitz.open()
    doc.new_page(width=400, height=500)
    doc.save(original)
    doc.close()
    compressed = tmp_path / "compressed.pdf"
    compress_pdf(original, compressed)
    with fitz.open(compressed) as result:
        assert result.page_count == 1
    cropped = tmp_path / "cropped.pdf"
    crop_pages(original, [0], (10, 20, 10, 20), cropped)
    with fitz.open(cropped) as result:
        assert result[0].rect.width == pytest.approx(380)
        assert result[0].rect.height == pytest.approx(460)

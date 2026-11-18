import sys
from pathlib import Path
import fitz
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pdf_studio.production_tools import (
    export_page_images, watermark_pdf, insert_image, set_metadata
)


@pytest.fixture
def sample(tmp_path):
    path = tmp_path / "sample.pdf"
    doc = fitz.open()
    doc.new_page(width=500, height=700)
    doc.save(path)
    doc.close()
    return path


def test_png_export(sample, tmp_path):
    paths = export_page_images(sample, tmp_path)
    assert len(paths) == 1
    assert paths[0].read_bytes()[:8] == b"\\x89PNG\\r\\n\\x1a\\n"


def test_watermark(sample, tmp_path):
    output = tmp_path / "watermarked.pdf"
    watermark_pdf(sample, output, "INTERNAL")
    with fitz.open(output) as doc:
        assert "INTERNAL" in doc[0].get_text()


def test_insert_image(sample, tmp_path):
    image_path = tmp_path / "test.png"
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 10, 10), False)
    pix.clear_with(180)
    pix.save(image_path)
    output = tmp_path / "image.pdf"
    insert_image(sample, 0, image_path, output)
    with fitz.open(output) as doc:
        assert len(doc[0].get_images()) == 1


def test_metadata(sample, tmp_path):
    output = tmp_path / "metadata.pdf"
    set_metadata(sample, output, title="Studio", author="Owner")
    with fitz.open(output) as doc:
        assert doc.metadata["title"] == "Studio"
        assert doc.metadata["author"] == "Owner"


def test_refuse_overwrite(sample):
    with pytest.raises(ValueError):
        watermark_pdf(sample, sample, "NO")

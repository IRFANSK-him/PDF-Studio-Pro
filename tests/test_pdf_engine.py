import sys
from pathlib import Path
import fitz
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pdf_studio.pdf_engine import PDFDocument


def test_open_render_and_close(tmp_path):
    path = tmp_path / "sample.pdf"
    pdf = fitz.open()
    pdf.new_page(width=200, height=300)
    pdf.save(path)
    pdf.close()
    document = PDFDocument()
    document.open(path)
    assert document.page_count == 1
    pix = document.render(0)
    assert pix.width == 200
    assert pix.height == 300
    with pytest.raises(IndexError):
        document.render(1)
    document.close()
    assert document.page_count == 0

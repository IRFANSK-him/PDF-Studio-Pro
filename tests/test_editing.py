import sys
from pathlib import Path
import fitz
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pdf_studio.editing import add_text, highlight_text, redact_text, encrypt_pdf


@pytest.fixture
def pdf(tmp_path):
    path = tmp_path / "source.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "CONFIDENTIAL TEST CONTENT")
    doc.save(path)
    doc.close()
    return path


def test_add_text(pdf, tmp_path):
    output = tmp_path / "annotated.pdf"
    add_text(pdf, 0, "REVIEWED", 72, 120, output)
    with fitz.open(output) as doc:
        assert "REVIEWED" in doc[0].get_text()
    with fitz.open(pdf) as doc:
        assert "REVIEWED" not in doc[0].get_text()


def test_highlight(pdf, tmp_path):
    output = tmp_path / "highlight.pdf"
    highlight_text(pdf, 0, "TEST", output)
    with fitz.open(output) as doc:
        assert doc[0].first_annot is not None


def test_redaction_removes_text(pdf, tmp_path):
    output = tmp_path / "redacted.pdf"
    redact_text(pdf, 0, "CONFIDENTIAL", output)
    with fitz.open(output) as doc:
        assert "CONFIDENTIAL" not in doc[0].get_text()


def test_encrypt(pdf, tmp_path):
    output = tmp_path / "encrypted.pdf"
    encrypt_pdf(pdf, output, "reader-password", "owner-password")
    with fitz.open(output) as doc:
        assert doc.needs_pass
        assert doc.authenticate("reader-password")


def test_reject_invalid_text(pdf, tmp_path):
    with pytest.raises(ValueError):
        add_text(pdf, 0, "", 72, 72, tmp_path / "invalid.pdf")

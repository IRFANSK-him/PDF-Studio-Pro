from pathlib import Path
import sys
import fitz
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pdf_studio.page_tools import (
    merge_pdfs, extract_pages, split_pdf, rotate_pages, delete_pages, reorder_pages
)


@pytest.fixture
def samples(tmp_path):
    paths = []
    for name, count in (("a.pdf", 3), ("b.pdf", 2)):
        path = tmp_path / name
        doc = fitz.open()
        for _ in range(count):
            doc.new_page(width=200, height=300)
        doc.save(path)
        doc.close()
        paths.append(path)
    return paths


def count(path):
    with fitz.open(path) as doc:
        return doc.page_count


def test_merge(samples, tmp_path):
    output = tmp_path / "merged.pdf"
    merge_pdfs(samples, output)
    assert count(output) == 5
    assert count(samples[0]) == 3


def test_extract(samples, tmp_path):
    output = tmp_path / "extracted.pdf"
    extract_pages(samples[0], [2, 0], output)
    assert count(output) == 2


def test_split(samples, tmp_path):
    folder = tmp_path / "parts"
    folder.mkdir()
    outputs = split_pdf(samples[0], folder)
    assert len(outputs) == 3
    assert all(count(path) == 1 for path in outputs)


def test_rotate(samples, tmp_path):
    output = tmp_path / "rotated.pdf"
    rotate_pages(samples[0], [0], 90, output)
    with fitz.open(output) as doc:
        assert doc[0].rotation == 90
        assert doc[1].rotation == 0


def test_delete(samples, tmp_path):
    output = tmp_path / "deleted.pdf"
    delete_pages(samples[0], [1], output)
    assert count(output) == 2


def test_refuse_overwrite(samples, tmp_path):
    with pytest.raises(ValueError):
        rotate_pages(samples[0], [0], 90, samples[0])
    output = tmp_path / "existing.pdf"
    output.write_bytes(b"existing")
    with pytest.raises(FileExistsError):
        merge_pdfs(samples, output)


def test_reject_delete_all(samples, tmp_path):
    with pytest.raises(ValueError):
        delete_pages(samples[0], [0, 1, 2], tmp_path / "invalid.pdf")


def test_reorder(samples, tmp_path):
    output = tmp_path / "reordered.pdf"
    reorder_pages(samples[0], [2, 0, 1], output)
    assert count(output) == 3


def test_reorder_rejects_invalid_order(samples, tmp_path):
    with pytest.raises(ValueError):
        reorder_pages(samples[0], [0, 0, 2], tmp_path / "invalid_order.pdf")

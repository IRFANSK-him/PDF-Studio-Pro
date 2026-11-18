import sys
from pathlib import Path
import fitz
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pdf_studio.history import PageOrderHistory
from pdf_studio.search import find_text


def test_undo_redo_and_branching():
    history = PageOrderHistory()
    history.reset([0, 1, 2])
    assert not history.can_undo
    assert history.record([2, 0, 1])
    assert history.can_undo
    assert history.undo() == [0, 1, 2]
    assert history.redo() == [2, 0, 1]
    history.undo()
    history.record([1, 0, 2])
    assert not history.can_redo
    with pytest.raises(ValueError):
        history.record([0, 0, 2])


def test_search_text_layer(tmp_path):
    path = tmp_path / "search.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Dairy PDF Studio")
    doc.save(path)
    doc.close()
    hits = find_text(path, "PDF")
    assert len(hits) == 1
    assert hits[0][0] == 0
    assert find_text(path, "missing") == []

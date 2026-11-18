"""Document operations backed by PyMuPDF."""
from pathlib import Path
import fitz


class PDFDocument:
    def __init__(self):
        self._doc = None
        self.path = None

    @property
    def page_count(self):
        return len(self._doc) if self._doc is not None else 0

    def open(self, path):
        candidate = fitz.open(str(path))
        if not candidate.is_pdf:
            candidate.close()
            raise ValueError("Only PDF documents are supported")
        if candidate.needs_pass:
            candidate.close()
            raise ValueError("Password-protected PDFs are not yet supported")
        self.close()
        self._doc = candidate
        self.path = Path(path)

    def render(self, index, zoom=1.0):
        if self._doc is None:
            raise RuntimeError("No document open")
        if not 0 <= index < self.page_count:
            raise IndexError("Page index out of range")
        if not 0.25 <= zoom <= 4:
            raise ValueError("Zoom must be between 0.25 and 4")
        return self._doc[index].get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)

    def close(self):
        if self._doc is not None:
            self._doc.close()
        self._doc = None
        self.path = None

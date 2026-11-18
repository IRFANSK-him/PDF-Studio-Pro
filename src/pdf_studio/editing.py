"""Safe, non-destructive PDF annotation and security operations."""
from pathlib import Path
import fitz
from .page_tools import _open_pdf, _output_path


def add_text(path, page_index, text, x, y, output, fontsize=12):
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    if not 6 <= fontsize <= 72:
        raise ValueError("Font size must be between 6 and 72")
    destination = _output_path(output, [path])
    doc = _open_pdf(path)
    try:
        if not 0 <= page_index < doc.page_count:
            raise ValueError("Page out of range")
        if not (0 <= x <= doc[page_index].rect.width and 0 <= y <= doc[page_index].rect.height):
            raise ValueError("Text position is outside the page")
        remainder = doc[page_index].insert_text(
            (x, y), text, fontsize=fontsize, color=(0.8, 0.1, 0.1)
        )
        if remainder < 0:
            raise ValueError("Text could not fit on the page")
        doc.save(str(destination), garbage=4, deflate=True)
    finally:
        doc.close()
    return destination


def highlight_text(path, page_index, query, output):
    if not query.strip():
        raise ValueError("Search text cannot be empty")
    destination = _output_path(output, [path])
    doc = _open_pdf(path)
    try:
        if not 0 <= page_index < doc.page_count:
            raise ValueError("Page out of range")
        page = doc[page_index]
        hits = page.search_for(query)
        if not hits:
            raise ValueError("No matching text on selected page")
        for rectangle in hits:
            annotation = page.add_highlight_annot(rectangle)
            annotation.update()
        doc.save(str(destination), garbage=4, deflate=True)
    finally:
        doc.close()
    return destination


def redact_text(path, page_index, query, output):
    """Permanently remove matching text content; not a visual-only black box."""
    if not query.strip():
        raise ValueError("Search text cannot be empty")
    destination = _output_path(output, [path])
    doc = _open_pdf(path)
    try:
        if not 0 <= page_index < doc.page_count:
            raise ValueError("Page out of range")
        page = doc[page_index]
        hits = page.search_for(query)
        if not hits:
            raise ValueError("No matching text on selected page")
        for rectangle in hits:
            page.add_redact_annot(rectangle, fill=(0, 0, 0))
        page.apply_redactions()
        doc.save(str(destination), garbage=4, deflate=True)
    finally:
        doc.close()
    return destination


def encrypt_pdf(path, output, user_password, owner_password):
    if not user_password or not owner_password:
        raise ValueError("Both passwords are required")
    destination = _output_path(output, [path])
    doc = _open_pdf(path)
    try:
        doc.save(
            str(destination),
            encryption=fitz.PDF_ENCRYPT_AES_256,
            user_pw=user_password,
            owner_pw=owner_password,
            permissions=fitz.PDF_PERM_PRINT,
        )
    finally:
        doc.close()
    return destination

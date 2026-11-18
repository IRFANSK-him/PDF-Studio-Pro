"""Non-destructive PDF page operations.

All operations write to a separate output file. Existing inputs are never overwritten.
Page numbers in this module are zero-based.
"""
from pathlib import Path
import fitz


def _output_path(output, inputs):
    destination = Path(output).expanduser().resolve()
    if destination.suffix.lower() != ".pdf":
        raise ValueError("Output filename must end with .pdf")
    if any(destination == Path(p).expanduser().resolve() for p in inputs):
        raise ValueError("Choose a new output filename; source files cannot be overwritten")
    if destination.exists():
        raise FileExistsError(f"Output already exists: {destination}")
    return destination


def _open_pdf(path):
    doc = fitz.open(str(path))
    if not doc.is_pdf or doc.needs_pass:
        doc.close()
        raise ValueError(f"Unsupported or encrypted PDF: {path}")
    return doc


def _save(doc, destination):
    doc.save(str(destination), garbage=4, deflate=True)


def merge_pdfs(paths, output):
    sources = list(paths)
    if len(sources) < 2:
        raise ValueError("Select at least two PDFs")
    destination = _output_path(output, sources)
    combined = fitz.open()
    try:
        for path in sources:
            source = _open_pdf(path)
            try:
                if source.page_count == 0:
                    raise ValueError(f"PDF has no pages: {path}")
                combined.insert_pdf(source)
            finally:
                source.close()
        _save(combined, destination)
    finally:
        combined.close()
    return destination


def extract_pages(path, page_indices, output):
    indices = list(page_indices)
    if not indices or len(indices) != len(set(indices)):
        raise ValueError("Select unique pages to extract")
    destination = _output_path(output, [path])
    source = _open_pdf(path)
    extracted = fitz.open()
    try:
        if any(not isinstance(i, int) or i < 0 or i >= source.page_count for i in indices):
            raise ValueError("Page index out of range")
        for index in indices:
            extracted.insert_pdf(source, from_page=index, to_page=index)
        _save(extracted, destination)
    finally:
        extracted.close()
        source.close()
    return destination


def split_pdf(path, output_directory):
    source = _open_pdf(path)
    target = Path(output_directory).expanduser().resolve()
    try:
        if not target.is_dir():
            raise ValueError("Choose an existing output folder")
        outputs = [target / f"{Path(path).stem}_page_{i + 1:03}.pdf"
                   for i in range(source.page_count)]
        for output in outputs:
            _output_path(output, [path])
        for i, output in enumerate(outputs):
            single = fitz.open()
            try:
                single.insert_pdf(source, from_page=i, to_page=i)
                _save(single, output)
            finally:
                single.close()
        return outputs
    finally:
        source.close()


def rotate_pages(path, page_indices, degrees, output):
    indices = list(page_indices)
    if degrees not in (90, 180, 270):
        raise ValueError("Rotation must be 90, 180, or 270 degrees")
    destination = _output_path(output, [path])
    source = _open_pdf(path)
    try:
        if not indices or any(not isinstance(i, int) or i < 0 or i >= source.page_count for i in indices):
            raise ValueError("Select valid pages")
        for index in set(indices):
            page = source[index]
            page.set_rotation((page.rotation + degrees) % 360)
        _save(source, destination)
    finally:
        source.close()
    return destination


def delete_pages(path, page_indices, output):
    indices = set(page_indices)
    destination = _output_path(output, [path])
    source = _open_pdf(path)
    try:
        if not indices or any(not isinstance(i, int) or i < 0 or i >= source.page_count for i in indices):
            raise ValueError("Select valid pages")
        if len(indices) >= source.page_count:
            raise ValueError("Cannot delete every page")
        source.delete_pages(sorted(indices, reverse=True))
        _save(source, destination)
    finally:
        source.close()
    return destination


def reorder_pages(path, page_order, output):
    """Save a PDF with pages in the specified zero-based order."""
    order = list(page_order)
    destination = _output_path(output, [path])
    source = _open_pdf(path)
    reordered = fitz.open()
    try:
        if len(order) != source.page_count or sorted(order) != list(range(source.page_count)):
            raise ValueError("Order must contain each page exactly once")
        for index in order:
            reordered.insert_pdf(source, from_page=index, to_page=index)
        _save(reordered, destination)
    finally:
        reordered.close()
        source.close()
    return destination

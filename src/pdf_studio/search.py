"""Text search across selectable PDF text layers."""
import fitz


def find_text(path, query, max_results=500):
    if not query or not query.strip():
        return []
    if max_results < 1:
        raise ValueError("max_results must be positive")
    matches = []
    with fitz.open(str(path)) as doc:
        if not doc.is_pdf or doc.needs_pass:
            raise ValueError("Unsupported or encrypted PDF")
        for page_index, page in enumerate(doc):
            for rectangle in page.search_for(query):
                matches.append((page_index, tuple(rectangle)))
                if len(matches) >= max_results:
                    return matches
    return matches

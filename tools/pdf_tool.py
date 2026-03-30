"""PDF-to-text extraction tool."""
from __future__ import annotations


def _parse_page_range(pages: str, total: int) -> list[int]:
    """Parse a page range string like '1-5' or '3' into 0-based page indices."""
    pages = pages.strip()
    if '-' in pages:
        start, end = pages.split('-', 1)
        start = max(1, int(start.strip()))
        end = min(total, int(end.strip()))
        return list(range(start - 1, end))
    else:
        n = int(pages)
        if 1 <= n <= total:
            return [n - 1]
        return []


def pdf_to_text(path: str, pages: str | None = None) -> str:
    """Extract text from a PDF file.

    Args:
        path: Path to the PDF file.
        pages: Optional page range string, e.g. '1-5' or '3'. Defaults to all pages.

    Returns:
        Extracted text as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    import os
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF file not found: {path}")
    text = _extract_with_pypdf(path, pages)
    if not text or not text.strip():
        text = _extract_with_pdfminer(path, pages)
    return text


def _extract_with_pypdf(path: str, pages: str | None) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""

    reader = PdfReader(path)
    total = len(reader.pages)
    indices = _parse_page_range(pages, total) if pages else list(range(total))

    parts = []
    for i in indices:
        page_text = reader.pages[i].extract_text() or ""
        parts.append(page_text)
    return "\n".join(parts)


def _extract_with_pdfminer(path: str, pages: str | None) -> str:
    try:
        from pdfminer.high_level import extract_text_to_fp, extract_pages
        from pdfminer.layout import LAParams
        import io
    except ImportError:
        return ""

    try:
        from pypdf import PdfReader
        total = len(PdfReader(path).pages)
    except Exception:
        total = 9999

    if pages:
        indices = _parse_page_range(pages, total)
        page_numbers = set(i + 1 for i in indices)  # pdfminer uses 1-based
    else:
        page_numbers = None

    buf = io.StringIO()
    with open(path, "rb") as f:
        from pdfminer.high_level import extract_text_to_fp
        extract_text_to_fp(
            f,
            buf,
            laparams=LAParams(),
            page_numbers=({p - 1 for p in page_numbers} if page_numbers else None),
            output_type="text",
            codec="utf-8",
        )
    return buf.getvalue()

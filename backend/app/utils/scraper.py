"""
Web scraping utilities — trafilatura for HTML, PyPDF2 for PDFs.
All fetches are wrapped with httpx timeout.
"""
import logging
import httpx
import trafilatura
from io import BytesIO

logger = logging.getLogger(__name__)

_TIMEOUT = 30


def fetch_and_extract(url: str) -> str:
    """Fetch a URL and extract clean text content.

    Uses trafilatura for HTML boilerplate removal.
    Falls back to raw text on failure.
    Returns empty string if the page cannot be fetched.
    """
    try:
        if url.lower().endswith(".pdf"):
            return extract_pdf(url)

        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            logger.warning("trafilatura could not fetch: %s", url)
            return ""

        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            deduplicate=True,
        )
        return text or ""

    except Exception as exc:
        logger.error("Failed to extract content from %s: %s", url, exc)
        return ""


def extract_pdf(url: str) -> str:
    """Download a PDF from *url* and extract text via PyPDF2."""
    try:
        from PyPDF2 import PdfReader

        response = httpx.get(url, timeout=_TIMEOUT, follow_redirects=True)
        response.raise_for_status()

        reader = PdfReader(BytesIO(response.content))
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
        return "\n\n".join(pages_text)

    except Exception as exc:
        logger.error("Failed to extract PDF from %s: %s", url, exc)
        return ""


def chunk_text(text: str, chunk_size: int = 600,
               overlap: int = 100) -> list[str]:
    """Split *text* into overlapping word-based chunks.

    Parameters
    ----------
    chunk_size : int
        Target number of words per chunk.
    overlap : int
        Number of overlapping words between consecutive chunks.
    """
    words = text.split()
    if len(words) <= chunk_size:
        return [text] if text.strip() else []

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap
        if start >= len(words):
            break
    return chunks

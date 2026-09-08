"""
Node 3: Extraction — Fetch pages, strip boilerplate, chunk text.

Optimized: No LLM call per chunk. Trafilatura already cleans the text.
We use the first N words of each chunk as its summary (fast, deterministic).
LLM summarization was the bottleneck — 50+ calls at ~30s each = 25+ minutes.
"""
import uuid
import logging
from typing import Dict, Any

from app.state import GraphState
from app.models import SourceChunk
from app.utils.scraper import fetch_and_extract, chunk_text
from app.job_store import job_store

logger = logging.getLogger(__name__)

MAX_URLS = 12
MAX_CHUNKS_PER_URL = 3
MAX_TOTAL_CHUNKS = 25


def _make_summary(text: str, max_words: int = 80) -> str:
    """Create a summary by taking the first N words (no LLM needed)."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


def extraction_node(state: GraphState) -> Dict[str, Any]:
    job_id = state.get("job_id")
    search_results = state.get("search_results", [])
    existing_chunks = state.get("chunks", []) or []

    job_store.set_status(job_id, "running", "extraction", 30, None)

    urls_to_process = search_results[:MAX_URLS]
    logger.info("Extraction: processing %d URLs (capped from %d)",
                len(urls_to_process), len(search_results))

    new_chunks: list[SourceChunk] = []

    for i, result in enumerate(urls_to_process):
        if len(new_chunks) >= MAX_TOTAL_CHUNKS:
            logger.info("Hit MAX_TOTAL_CHUNKS=%d, stopping extraction", MAX_TOTAL_CHUNKS)
            break

        url = result.get("url", "")
        title = result.get("title", "")

        pct = 30 + int((i / len(urls_to_process)) * 10)
        job_store.set_status(job_id, "running", "extraction", pct, None)

        try:
            text = fetch_and_extract(url)
            if not text or len(text.split()) < 50:
                logger.debug("Skipping %s — too short or empty", url)
                continue

            text_chunks = chunk_text(text, chunk_size=500, overlap=50)

            for tc in text_chunks[:MAX_CHUNKS_PER_URL]:
                if len(new_chunks) >= MAX_TOTAL_CHUNKS:
                    break

                chunk_obj = SourceChunk(
                    id=uuid.uuid4().hex[:8],
                    url=url,
                    title=title,
                    text=tc,
                    summary=_make_summary(tc),
                    relevance_score=None,
                    relevance_reason=None,
                    kept=False,
                )
                new_chunks.append(chunk_obj)

        except Exception as e:
            logger.error("Error extracting from '%s': %s", url, e)

    logger.info("Extraction complete: %d new chunks from %d URLs",
                len(new_chunks), len(urls_to_process))

    return {
        "status": "running",
        "nodes_completed": ["extraction"],
        "chunks": existing_chunks + new_chunks,
    }

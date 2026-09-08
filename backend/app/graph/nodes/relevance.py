"""
Node 4: Relevance Check — Score each chunk 0-1 against topic.

Optimized: batch multiple chunks into a single LLM call (up to 5 at a time)
instead of 1 call per chunk. With 25 chunks that's 5 calls instead of 25.
"""
import json
import logging
from typing import Dict, Any, List

from langchain_core.messages import SystemMessage, HumanMessage

from app.state import GraphState
from app.models import SourceChunk
from app.utils.ollama_client import invoke_llm_json
from app.config import settings
from app.job_store import job_store

logger = logging.getLogger(__name__)

BATCH_SIZE = 5


def _score_batch(topic: str, chunks: List[SourceChunk]) -> List[dict]:
    """Score a batch of chunks for relevance in a single LLM call."""
    chunk_summaries = []
    for i, c in enumerate(chunks):
        short_text = " ".join(c.text.split()[:150])
        chunk_summaries.append(f'  {{"id": "{c.id}", "text": "{short_text[:300]}"}}')

    chunks_json = ",\n".join(chunk_summaries)

    messages = [
        HumanMessage(content=(
            f'Score the relevance (0.0 to 1.0) of each text chunk to the research topic: "{topic}".\n\n'
            f'Chunks:\n[\n{chunks_json}\n]\n\n'
            f'Return a JSON array of objects, one per chunk:\n'
            f'[{{"id": "chunk_id", "score": 0.0-1.0, "reason": "brief reason", "keep": true/false}}]\n\n'
            f'A chunk is worth keeping (keep=true) if score >= 0.5.'
        ))
    ]

    try:
        response = invoke_llm_json(
            node_name="relevance", messages=messages,
            temperature=0.1, max_tokens=512,
        )
        start = response.find("[")
        end = response.rfind("]") + 1
        if start != -1 and end > start:
            return json.loads(response[start:end])
        return json.loads(response)
    except Exception as e:
        logger.error("Batch relevance scoring failed: %s", e)
        return []


def relevance_check_node(state: GraphState) -> Dict[str, Any]:
    job_id = state.get("job_id")
    topic = state.get("topic", "")
    chunks = state.get("chunks", [])

    job_store.set_status(job_id, "running", "relevance_check", 42, None)

    unscored = [c for c in chunks if c.relevance_score is None]
    scored = [c for c in chunks if c.relevance_score is not None]

    logger.info("Relevance check: %d unscored chunks, %d already scored",
                len(unscored), len(scored))

    if not unscored:
        current_retry = state.get("relevance_retry_count", 0)
        return {
            "status": "running",
            "nodes_completed": ["relevance_check"],
            "chunks": chunks,
            "relevance_retry_count": current_retry + 1,
        }

    results_map: dict[str, dict] = {}
    total_batches = (len(unscored) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx in range(0, len(unscored), BATCH_SIZE):
        batch = unscored[batch_idx : batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1

        pct = 42 + int((batch_num / total_batches) * 6)
        job_store.set_status(job_id, "running", "relevance_check", pct, None)

        logger.info("Scoring batch %d/%d (%d chunks)", batch_num, total_batches, len(batch))

        batch_results = _score_batch(topic, batch)
        for result in batch_results:
            if isinstance(result, dict) and "id" in result:
                results_map[result["id"]] = result

    updated_chunks = list(scored)
    for chunk in unscored:
        result = results_map.get(chunk.id)
        if result:
            try:
                chunk.relevance_score = float(result.get("score", 0.0))
                chunk.relevance_reason = str(result.get("reason", ""))
                chunk.kept = chunk.relevance_score >= settings.min_relevance_score
            except (ValueError, TypeError):
                chunk.relevance_score = 0.0
                chunk.relevance_reason = "Parse error"
                chunk.kept = False
        else:
            chunk.relevance_score = 0.4
            chunk.relevance_reason = "Not scored in batch"
            chunk.kept = False
        updated_chunks.append(chunk)

    kept_count = sum(1 for c in updated_chunks if c.kept)
    current_retry = state.get("relevance_retry_count", 0)

    logger.info("Relevance check done: %d/%d chunks kept (retry count: %d)",
                kept_count, len(updated_chunks), current_retry)

    return {
        "status": "running",
        "nodes_completed": ["relevance_check"],
        "chunks": updated_chunks,
        "relevance_retry_count": current_retry + 1,
    }

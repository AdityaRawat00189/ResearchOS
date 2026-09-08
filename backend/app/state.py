"""
LangGraph state schema for the research paper generation pipeline.
"""
from typing import TypedDict, Optional, Annotated
import operator

from app.models import SourceChunk, SectionDraft, OutlineSection


def _merge_dict(left: dict, right: dict) -> dict:
    """Reducer that merges two dicts (right overwrites left for same keys)."""
    merged = {**left}
    merged.update(right)
    return merged


class GraphState(TypedDict):
    """Shared state passed between all graph nodes."""
    job_id: str
    topic: str
    min_pages: int
    citation_style: str
    keywords: list[str]
    domain: str

    search_queries: list[str]
    search_results: list[dict]

    chunks: list[SourceChunk]

    relevance_retry_count: int

    outline: list[OutlineSection]

    sections: Annotated[dict[str, SectionDraft], _merge_dict]
    writing_retry_count: Annotated[dict[str, int], _merge_dict]

    validation_report: dict
    validation_retry_count: int

    final_doc_path: Optional[str]

    status: str
    nodes_completed: Annotated[list[str], operator.add]
    error: Optional[str]

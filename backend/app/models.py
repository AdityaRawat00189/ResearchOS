"""
Pydantic models for the research paper generation pipeline.
"""
from pydantic import BaseModel, Field
from typing import Optional


class SourceChunk(BaseModel):
    """A chunk of text extracted from a web source."""
    id: str
    url: str
    title: str = ""
    text: str
    summary: str = ""
    relevance_score: Optional[float] = None
    relevance_reason: Optional[str] = None
    kept: bool = False


class SectionDraft(BaseModel):
    """A single section of the research paper."""
    name: str
    target_words: int
    content: str = ""
    citations_used: list[str] = Field(default_factory=list)
    quality_score: Optional[float] = None
    quality_feedback: Optional[str] = None
    rewrite_count: int = 0


class OutlineSection(BaseModel):
    """A section in the paper outline."""
    name: str
    target_words: int
    key_claims: list[str] = Field(default_factory=list)
    assigned_chunk_ids: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Result of a single validation check."""
    check_name: str
    passed: bool
    message: str
    severity: str = "error"


class ValidationReport(BaseModel):
    """Aggregated validation report."""
    passed: bool = False
    fix_target: Optional[str] = None
    results: list[ValidationResult] = Field(default_factory=list)
    failures: list[str] = Field(default_factory=list)


class GenerateRequest(BaseModel):
    """Request to generate a research paper."""
    topic: str
    min_pages: int = 5
    citation_style: str = "APA"
    keywords: list[str] = Field(default_factory=list)
    domain: Optional[str] = None


class StatusResponse(BaseModel):
    """Response for job status polling."""
    job_id: str
    status: str
    current_node: str = ""
    progress_pct: int = 0
    error: Optional[str] = None
    nodes_completed: list[str] = Field(default_factory=list)

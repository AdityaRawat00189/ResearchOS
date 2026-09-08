"""
Node 6: Section Writing — Write each section from its assigned chunks + outline.

One LLM call per section (6 sections = 6 calls). This is the quality bottleneck
so we use the strongest available model and max tokens.
"""
import re
import logging
from typing import Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage

from app.state import GraphState
from app.models import SectionDraft
from app.utils.ollama_client import invoke_llm
from app.config import settings
from app.job_store import job_store

logger = logging.getLogger(__name__)


def section_writer_node(state: GraphState) -> Dict[str, Any]:
    job_id = state.get("job_id")
    topic = state.get("topic")
    outline = state.get("outline", [])
    all_chunks = state.get("chunks", [])
    chunk_map = {c.id: c for c in all_chunks}
    existing_sections = state.get("sections", {})
    writing_retry_count = dict(state.get("writing_retry_count", {}))

    job_store.set_status(job_id, "running", "section_writer", 56, None)

    val_report = state.get("validation_report", {})
    val_failed = isinstance(val_report, dict) and not val_report.get("passed", True)
    val_failures = val_report.get("failures", []) if val_failed else []

    new_sections = {}
    total = len(outline)

    for i, outline_sec in enumerate(outline):
        name = outline_sec.name

        pct = 56 + int(((i + 1) / total) * 16)
        job_store.set_status(job_id, "running", "section_writer", pct, None)

        existing = existing_sections.get(name)
        if existing:
            score = getattr(existing, "quality_score", None)
            if score is not None and score >= settings.min_quality_score and not val_failed:
                logger.info("Section '%s' already passes quality (%.2f), skipping", name, score)
                continue

        assigned = [chunk_map[cid] for cid in outline_sec.assigned_chunk_ids if cid in chunk_map]

        if not assigned:
            assigned = [c for c in all_chunks if getattr(c, "kept", False)]
            if not assigned:
                assigned = all_chunks[:5]
            else:
                assigned = assigned[:5]

        source_material = "\n".join(
            [f"[{c.id}] {c.summary or c.text[:200]}" for c in assigned]
        )
        claims = ", ".join(outline_sec.key_claims) if outline_sec.key_claims else "General coverage"

        feedback_part = ""
        rewrite_count = 0
        if existing:
            feedback = getattr(existing, "quality_feedback", "")
            if feedback:
                feedback_part = f"\n\nIMPORTANT — Previous reviewer feedback to address:\n{feedback}\n"
            rewrite_count = getattr(existing, "rewrite_count", 0) + 1

        if val_failed:
            if "word_count" in val_failures:
                feedback_part += f"\n\nIMPORTANT — Validation Failure: Total paper word count was too short. Write a detailed, comprehensive section aimed at {outline_sec.target_words} words."
            if "citation_count" in val_failures:
                feedback_part += "\n\nIMPORTANT — Validation Failure: Include more inline citations [chunk_id] referencing the provided source material."

        prompt = (
            f'Write the "{name}" section for a research paper on "{topic}".\n\n'
            f"Target length: approximately {outline_sec.target_words} words.\n"
            f"Key claims to cover: {claims}\n"
            f"Use inline citations like [chunk_id] when referencing source material.\n"
            f"{feedback_part}\n"
            f"Source material:\n{source_material}\n\n"
            f"Write in formal academic style. Be thorough and detailed."
        )

        messages = [
            SystemMessage(content="You are an expert academic writer. Write in formal, publication-quality prose."),
            HumanMessage(content=prompt),
        ]

        try:
            logger.info("Writing section '%s' (target: %d words, %d sources)",
                        name, outline_sec.target_words, len(assigned))

            content = invoke_llm(
                node_name="section_writer", messages=messages,
                temperature=0.5, max_tokens=4096,
            )

            citations_used = list(set(re.findall(r"\[([a-zA-Z0-9_-]{6,10})\]", content)))

            draft = SectionDraft(
                name=name,
                target_words=outline_sec.target_words,
                content=content,
                citations_used=citations_used,
                quality_score=None,
                quality_feedback="",
                rewrite_count=rewrite_count,
            )
            new_sections[name] = draft

            writing_retry_count[name] = rewrite_count

            logger.info("Section '%s' written: %d words, %d citations",
                        name, len(content.split()), len(citations_used))

        except Exception as e:
            logger.error("Error writing section '%s': %s", name, e)
            new_sections[name] = SectionDraft(
                name=name,
                target_words=outline_sec.target_words,
                content=f"[Content generation failed for {name}. Error: {e}]",
                citations_used=[],
                quality_score=None,
                quality_feedback="",
                rewrite_count=rewrite_count,
            )

    return {
        "status": "running",
        "nodes_completed": ["section_writer"],
        "sections": new_sections,
        "writing_retry_count": writing_retry_count,
    }

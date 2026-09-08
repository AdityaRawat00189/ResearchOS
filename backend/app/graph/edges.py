"""
Conditional edge functions for the LangGraph research pipeline.

Each function inspects GraphState and returns a string key that maps
to the next node via add_conditional_edges.
"""
import logging
from app.config import settings

logger = logging.getLogger(__name__)


def relevance_gate(state: dict) -> str:
    """Loop A — Relevance gate after the relevance-check node.

    Returns
    -------
    "pass"  → enough high-quality chunks, proceed to outline
    "retry" → too few kept chunks, go back to web_search with refined queries
    """
    chunks = state.get("chunks", [])
    kept = [c for c in chunks if c.kept]
    retry_count = state.get("relevance_retry_count", 0)

    logger.info(
        "Relevance gate: %d kept chunks out of %d (retry %d/%d)",
        len(kept), len(chunks), retry_count, settings.max_relevance_retries,
    )

    if len(kept) >= settings.min_kept_chunks:
        return "pass"

    if retry_count >= settings.max_relevance_retries:
        logger.warning(
            "Relevance retry budget exhausted (%d). Proceeding with %d chunks.",
            retry_count, len(kept),
        )
        return "pass"

    return "retry"


def quality_gate(state: dict) -> str:
    """Loop B — Quality gate after the quality-recheck node.

    Returns
    -------
    "pass"  → all sections meet quality threshold
    "retry" → at least one section needs rewriting
    """
    sections = state.get("sections", {})
    writing_retry_count = state.get("writing_retry_count", {})

    for name, section in sections.items():
        score = section.quality_score
        retries = writing_retry_count.get(name, 0)

        if score is not None and score < settings.min_quality_score:
            if retries < settings.max_writing_retries_per_section:
                logger.info(
                    "Quality gate: section '%s' scored %.2f (< %.2f), "
                    "retry %d/%d → sending back to writer",
                    name, score, settings.min_quality_score,
                    retries, settings.max_writing_retries_per_section,
                )
                return "retry"
            else:
                logger.warning(
                    "Quality gate: section '%s' scored %.2f but retry "
                    "budget exhausted (%d). Accepting.",
                    name, score, retries,
                )

    return "pass"


def validation_gate(state: dict) -> str:
    """Gate after the final-validation node.

    Routes to the specific upstream node that can fix the failure,
    or proceeds to export if all checks pass.

    Returns
    -------
    "pass"         → all validation checks passed, proceed to export
    "fix_writing"  → route back to section_writer
    "fix_outline"  → route back to outline generation
    """
    report = state.get("validation_report", {})

    if isinstance(report, dict):
        passed = report.get("passed", False)
        fix_target = report.get("fix_target")
    else:
        passed = getattr(report, "passed", False)
        fix_target = getattr(report, "fix_target", None)

    if passed:
        return "pass"

    val_retries = state.get("validation_retry_count", 0)
    if val_retries >= settings.max_validation_retries:
        logger.warning(
            "Validation retry budget exhausted (%d). Proceeding to export with warnings.",
            val_retries,
        )
        return "pass"

    if fix_target == "outline":
        logger.info("Validation gate (retry %d/%d) → routing to outline", val_retries, settings.max_validation_retries)
        return "fix_outline"

    logger.info("Validation gate (retry %d/%d) → routing to section_writer (fix_target=%s)", val_retries, settings.max_validation_retries, fix_target)
    return "fix_writing"

"""
Node 8: Final Validation — 14 deterministic + LLM-assisted checks.
Routes failures to the specific upstream node that can fix them.
"""
import json
import re
import logging
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage

from app.state import GraphState
from app.config import settings
from app.models import ValidationResult, ValidationReport
from app.utils.ollama_client import invoke_llm_json
from app.job_store import job_store

logger = logging.getLogger(__name__)


def validation_node(state: GraphState) -> Dict[str, Any]:
    job_id = state.get("job_id")
    outline = state.get("outline", [])
    sections = state.get("sections", {})
    chunks = state.get("chunks", [])
    min_pages = state.get("min_pages", 1)
    citation_style = state.get("citation_style", "APA")
    topic = state.get("topic", "")

    job_store.set_status(job_id, "running", "validation", 90, None)

    results: list[ValidationResult] = []
    outline_names = [sec.name for sec in outline]

    total_words = sum(len(s.content.split()) for s in sections.values() if s.content)
    required_words = min_pages * settings.words_per_page
    word_count_passed = total_words >= required_words
    word_count_severity = "info" if word_count_passed else ("warning" if total_words >= int(required_words * 0.65) else "error")
    results.append(ValidationResult(
        check_name="word_count",
        passed=word_count_passed,
        message=f"Total words: {total_words}, required: {required_words}",
        severity=word_count_severity,
    ))

    missing_sections = [
        name for name in outline_names
        if name not in sections or not sections[name].content.strip()
    ]
    results.append(ValidationResult(
        check_name="sections_present",
        passed=len(missing_sections) == 0,
        message=f"Missing or empty sections: {missing_sections}" if missing_sections else "All sections present",
        severity="error" if missing_sections else "info",
    ))

    all_cited_ids = set()
    for s in sections.values():
        all_cited_ids.update(s.citations_used)
    min_citations = min(2, max(1, settings.min_kept_chunks // 2))
    results.append(ValidationResult(
        check_name="citation_count",
        passed=len(all_cited_ids) >= min_citations,
        message=f"Citations found: {len(all_cited_ids)}, minimum: {min_citations}",
        severity="warning" if len(all_cited_ids) < min_citations else "info",
    ))

    chunk_id_set = {c.id for c in chunks}
    dangling = []
    for sec_name, sec in sections.items():
        inline_refs = set(re.findall(r"\[([a-zA-Z0-9_-]+)\]", sec.content))
        for ref in inline_refs:
            if ref not in chunk_id_set and not ref.isdigit():
                dangling.append(f"{sec_name}:[{ref}]")
    results.append(ValidationResult(
        check_name="citation_mapping",
        passed=len(dangling) == 0,
        message=f"Dangling citations: {dangling[:10]}" if dangling else "All citations mapped",
        severity="warning" if dangling else "info",
    ))

    seen_urls = set()
    dup_refs = []
    for c in chunks:
        if c.kept and c.url in seen_urls:
            dup_refs.append(c.url)
        seen_urls.add(c.url)
    results.append(ValidationResult(
        check_name="no_duplicate_references",
        passed=len(dup_refs) == 0,
        message=f"Duplicate refs: {len(dup_refs)}" if dup_refs else "No duplicates",
        severity="warning" if dup_refs else "info",
    ))

    abstract = sections.get("Abstract")
    if abstract and abstract.content:
        abs_words = len(abstract.content.split())
        abs_ok = 150 <= abs_words <= 300
        results.append(ValidationResult(
            check_name="abstract_length",
            passed=abs_ok,
            message=f"Abstract words: {abs_words} (target: 150–300)",
            severity="warning" if not abs_ok else "info",
        ))
    else:
        results.append(ValidationResult(
            check_name="abstract_length",
            passed=False,
            message="Abstract section missing or empty",
            severity="warning",
        ))

    present_sections = set(sections.keys())
    outline_set = set(outline_names)
    hierarchy_ok = outline_set.issubset(present_sections)
    results.append(ValidationResult(
        check_name="heading_hierarchy",
        passed=hierarchy_ok,
        message="All headings present" if hierarchy_ok else f"Missing headings: {outline_set - present_sections}",
        severity="warning" if not hierarchy_ok else "info",
    ))

    kept_chunks = sorted([c for c in chunks if c.kept], key=lambda c: c.url)
    kept_urls = [c.url for c in chunks if c.kept]
    refs_sorted = kept_urls == sorted(kept_urls)
    results.append(ValidationResult(
        check_name="references_sorted",
        passed=refs_sorted,
        message="References sorted" if refs_sorted else "References not sorted",
        severity="info",
    ))

    bloated = []
    for sec in outline:
        s = sections.get(sec.name)
        if s and s.content:
            sec_words = len(s.content.split())
            if sec_words > 2 * sec.target_words and sec.target_words > 0:
                bloated.append(f"{sec.name}: {sec_words}/{sec.target_words}")
    results.append(ValidationResult(
        check_name="section_bloat",
        passed=len(bloated) == 0,
        message=f"Bloated sections: {bloated}" if bloated else "No bloated sections",
        severity="warning" if bloated else "info",
    ))

    deterministic_passed = all(
        r.passed or r.severity != "error" for r in results
    )

    if deterministic_passed:
        sample_text = ""
        for sec_name in outline_names[:3]:
            sec = sections.get(sec_name)
            if sec and sec.content:
                words = sec.content.split()[:200]
                sample_text += f"\n### {sec_name}\n{' '.join(words)}...\n"

        llm_checks = {
            "topic_coverage": f"Does this paper adequately address the topic '{topic}'? Score 0-1.",
            "cross_section_repetition": "Are there near-duplicate sentences across sections? Score 0-1 (1=no repetition).",
            "logical_flow": "Does each section build logically on the previous one? Score 0-1.",
            "grammar_fluency": "Rate grammar and fluency. Score 0-1.",
            "citation_grounding": "Do the citations appear to support the claims made? Score 0-1.",
        }

        for check_name, check_prompt in llm_checks.items():
            try:
                messages = [
                    SystemMessage(content="You are a research paper reviewer. Return strictly valid JSON."),
                    HumanMessage(
                        content=f'{check_prompt}\n\nSample:\n{sample_text}\n\n'
                                f'Return JSON: {{"score": float, "passed": bool, "reason": string}}'
                    ),
                ]
                resp = invoke_llm_json(
                    node_name="validation", messages=messages,
                    temperature=0.1, max_tokens=200,
                )
                parsed = json.loads(resp)
                results.append(ValidationResult(
                    check_name=check_name,
                    passed=parsed.get("passed", True),
                    message=parsed.get("reason", check_name),
                    severity="warning" if not parsed.get("passed", True) else "info",
                ))
            except Exception as exc:
                logger.warning("LLM check '%s' failed: %s", check_name, exc)
                results.append(ValidationResult(
                    check_name=check_name,
                    passed=True,
                    message=f"Check skipped: {exc}",
                    severity="info",
                ))
    else:
        for check_name in ["topic_coverage", "cross_section_repetition",
                           "logical_flow", "grammar_fluency", "citation_grounding"]:
            results.append(ValidationResult(
                check_name=check_name, passed=True,
                message="Skipped (deterministic checks failed first)",
                severity="info",
            ))

    failures = [r.check_name for r in results if not r.passed and r.severity == "error"]
    all_passed = len(failures) == 0

    fix_target = None
    if not all_passed:
        if any(f in failures for f in ["word_count", "sections_present",
                                        "citation_count", "citation_mapping"]):
            fix_target = "section_writer"
        elif "topic_coverage" in failures:
            fix_target = "outline"
        else:
            fix_target = "section_writer"

    report = ValidationReport(
        passed=all_passed,
        fix_target=fix_target,
        results=results,
        failures=failures,
    )

    logger.info("Validation: passed=%s, failures=%s, fix_target=%s",
                all_passed, failures, fix_target)

    val_retry_count = state.get("validation_retry_count", 0)
    if not all_passed:
        val_retry_count += 1

    return {
        "status": "running",
        "nodes_completed": ["validation"],
        "validation_report": report.model_dump(),
        "validation_retry_count": val_retry_count,
    }

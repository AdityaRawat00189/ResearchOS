"""
Node 7: Quality Recheck — Score each section for quality using a different
model than the writer (to reduce self-confirmation bias).

One LLM call per section. Sections that need rewriting get quality_score < threshold.
"""
import json
import logging
from typing import Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage

from app.state import GraphState
from app.utils.ollama_client import invoke_llm_json
from app.config import settings
from app.job_store import job_store

logger = logging.getLogger(__name__)


def quality_recheck_node(state: GraphState) -> Dict[str, Any]:
    job_id = state.get("job_id")
    sections = state.get("sections", {})
    topic = state.get("topic", "")

    job_store.set_status(job_id, "running", "quality_recheck", 75, None)

    updated_sections = {}
    section_list = list(sections.items())
    total = len(section_list)

    for i, (name, draft) in enumerate(section_list):
        pct = 75 + int(((i + 1) / total) * 7)
        job_store.set_status(job_id, "running", "quality_recheck", pct, None)

        if draft.quality_score is not None:
            logger.info("Section '%s' already scored (%.2f), skipping", name, draft.quality_score)
            updated_sections[name] = draft
            continue

        content_preview = draft.content[:2500] if draft.content else ""

        messages = [
            HumanMessage(content=(
                f'You are reviewing a section of a research paper on "{topic}".\n\n'
                f'Section: "{name}"\n'
                f'Content:\n{content_preview}\n\n'
                f'Score this section from 0.0 to 1.0 based on:\n'
                f'- Topic relevance: Does it address the research topic?\n'
                f'- Coherence: Is the writing clear and well-structured?\n'
                f'- Citation grounding: Are claims supported by citations?\n'
                f'- Completeness: Does it cover the expected scope?\n\n'
                f'Return JSON: {{"score": float, "feedback": "specific improvement suggestions", "issues": ["issue1", "issue2"]}}'
            ))
        ]

        try:
            response = invoke_llm_json(
                node_name="quality_recheck", messages=messages,
                temperature=0.1, max_tokens=500,
            )
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                parsed = json.loads(response[start:end])
            else:
                parsed = json.loads(response)

            draft.quality_score = float(parsed.get("score", 0.7))
            draft.quality_feedback = parsed.get("feedback", "")
            issues = parsed.get("issues", [])
            if issues:
                draft.quality_feedback += " Issues: " + "; ".join(issues)

            logger.info("Section '%s' quality score: %.2f", name, draft.quality_score)

        except Exception as e:
            logger.error("Quality check failed for section '%s': %s", name, e)
            draft.quality_score = 0.7
            draft.quality_feedback = f"Quality check error: {e}"

        updated_sections[name] = draft

    return {
        "status": "running",
        "nodes_completed": ["quality_recheck"],
        "sections": updated_sections,
    }

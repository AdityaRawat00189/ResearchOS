import os
import logging
from typing import Dict, Any
from app.state import GraphState
from app.config import settings
from app.utils.doc_builder import build_docx, convert_to_pdf
from app.job_store import job_store

logger = logging.getLogger(__name__)

def export_node(state: GraphState) -> Dict[str, Any]:
    job_id = state.get("job_id")
    topic = state.get("topic")
    sections = state.get("sections", {})
    chunks = state.get("chunks", [])
    citation_style = state.get("citation_style", "APA")
    outline = state.get("outline", [])
    
    job_store.set_status(job_id, "running", "export", 95, None)
    
    out_dir = os.path.join(settings.output_dir, job_id)
    os.makedirs(out_dir, exist_ok=True)
    
    docx_path = os.path.join(out_dir, "paper.docx")
    outline_order = [sec.name for sec in outline]
    
    try:
        final_path = build_docx(topic, sections, chunks, citation_style, outline_order, docx_path)
        pdf_path = convert_to_pdf(final_path)
        if pdf_path:
            final_path = pdf_path
            
        job_store.set_status(job_id, "completed", "export", 100, None)
    except Exception as e:
        logger.error(f"Export failed: {e}")
        job_store.set_status(job_id, "failed", "export", 100, str(e))
        return {
            "status": "failed",
            "nodes_completed": ["export"],
            "error": str(e)
        }
        
    return {
        "status": "completed",
        "nodes_completed": ["export"],
        "final_doc_path": final_path
    }

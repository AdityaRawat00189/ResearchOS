import json
import logging
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from app.state import GraphState
from app.config import settings
from app.models import OutlineSection
from app.utils.ollama_client import invoke_llm
from app.job_store import job_store

logger = logging.getLogger(__name__)

def outline_node(state: GraphState) -> Dict[str, Any]:
    job_id = state.get("job_id")
    topic = state.get("topic")
    min_pages = state.get("min_pages", 1)
    chunks = state.get("chunks", [])
    
    job_store.set_status(job_id, "running", "outline", 55, None)
    
    total_words = min_pages * settings.words_per_page
    
    messages = [
        SystemMessage(content="You are a research paper outliner. Output structured JSON."),
        HumanMessage(content=f'''Generate an outline for a research paper on: {topic}
Standard sections: Abstract, Introduction, Literature Review, Methodology, Results and Discussion, Conclusion.
Target words per section (total {total_words}): Abstract ~200, Intro 15%, Lit Review 25%, Methodology 20%, Results 25%, Conclusion 15%.
Return JSON format: {{"sections": [{{"name": string, "target_words": int, "key_claims": [string]}}]}}''')
    ]
    
    outline = []
    try:
        response = invoke_llm(node_name="outline", messages=messages, temperature=0.3, max_tokens=1000)
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end != 0:
            parsed = json.loads(response[start:end])
        else:
            parsed = json.loads(response)
            
        sections_data = parsed.get("sections", [])
        kept_chunks = [c for c in chunks if getattr(c, "kept", False)]
        
        for sec in sections_data:
            name = sec.get("name", "Unnamed")
            target_words = sec.get("target_words", 0)
            key_claims = sec.get("key_claims", [])
            
            assigned = []
            claims_text = " ".join(key_claims).lower()
            for chunk in kept_chunks:
                if any(word.lower() in chunk.text.lower() for word in claims_text.split() if len(word) > 4):
                    assigned.append(chunk.id)
            
            outline_sec = OutlineSection(
                name=name,
                target_words=target_words,
                key_claims=key_claims,
                assigned_chunk_ids=list(set(assigned))
            )
            outline.append(outline_sec)
            
    except Exception as e:
        logger.error(f"Error generating outline: {e}")
        outline = [OutlineSection(name="Introduction", target_words=total_words, key_claims=["Introduce topic"], assigned_chunk_ids=[c.id for c in chunks if getattr(c, "kept", False)])]
        
    return {
        "status": "running",
        "nodes_completed": ["outline"],
        "outline": outline
    }

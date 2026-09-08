import json
import logging
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from app.state import GraphState
from app.utils.ollama_client import invoke_llm
from app.job_store import job_store

logger = logging.getLogger(__name__)

def input_init_node(state: GraphState) -> Dict[str, Any]:
    job_id = state.get("job_id")
    topic = state.get("topic")
    min_pages = state.get("min_pages", 1)
    
    job_store.set_status(job_id, "running", "input_init", 10, None)
    
    if not topic:
        raise ValueError("Topic cannot be empty")
    if min_pages < 1:
        raise ValueError("min_pages must be at least 1")
        
    messages = [
        SystemMessage(content="You are an expert research assistant."),
        HumanMessage(content=f"Given the research topic: {topic}. Generate 4-6 specific search queries to find high-quality information. Return a JSON array of strings.")
    ]
    
    try:
        response = invoke_llm(node_name="input_init", messages=messages, temperature=0.3, max_tokens=200)
        start = response.find('[')
        end = response.rfind(']') + 1
        if start != -1 and end != 0:
            search_queries = json.loads(response[start:end])
        else:
            search_queries = json.loads(response)
        
        if not isinstance(search_queries, list):
            search_queries = [topic]
    except Exception as e:
        logger.error(f"Failed to parse search queries: {e}")
        search_queries = [topic]
        
    return {
        "status": "running",
        "nodes_completed": ["input_init"],
        "search_queries": search_queries[:6],
        "relevance_retry_count": 0,
        "validation_retry_count": 0,
        "writing_retry_count": {},
        "sections": {}
    }

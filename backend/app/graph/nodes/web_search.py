import logging
from typing import Dict, Any
from duckduckgo_search import DDGS
from app.state import GraphState
from app.config import settings
from app.job_store import job_store

logger = logging.getLogger(__name__)

def web_search_node(state: GraphState) -> Dict[str, Any]:
    job_id = state.get("job_id")
    search_queries = state.get("search_queries", [])
    
    job_store.set_status(job_id, "running", "web_search", 20, None)
    
    results_map = {}
    
    for query in search_queries:
        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=settings.max_search_results_per_query)
                for r in results:
                    url = r.get("href")
                    if url and url not in results_map:
                        results_map[url] = {
                            "url": url,
                            "title": r.get("title", ""),
                            "snippet": r.get("body", "")
                        }
        except Exception as e:
            logger.error(f"Error searching for query '{query}': {e}")
            
    return {
        "status": "running",
        "nodes_completed": ["web_search"],
        "search_results": list(results_map.values())
    }

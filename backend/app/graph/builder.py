"""
LangGraph StateGraph builder — assembles the 9-node research pipeline
with two conditional-edge retry loops and a validation gate.
"""
import logging
from langgraph.graph import StateGraph, END

from app.state import GraphState
from app.config import settings

from app.graph.nodes.input_init import input_init_node
from app.graph.nodes.web_search import web_search_node
from app.graph.nodes.extraction import extraction_node
from app.graph.nodes.relevance import relevance_check_node
from app.graph.nodes.outline import outline_node
from app.graph.nodes.section_writer import section_writer_node
from app.graph.nodes.quality_recheck import quality_recheck_node
from app.graph.nodes.validation import validation_node
from app.graph.nodes.export import export_node

from app.graph.edges import relevance_gate, quality_gate, validation_gate

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    """Construct and compile the research paper generation graph.

    Returns a compiled LangGraph application ready to be invoked.
    """
    graph = StateGraph(GraphState)

    graph.add_node("input_init", input_init_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("extraction", extraction_node)
    graph.add_node("relevance_check", relevance_check_node)
    graph.add_node("outline", outline_node)
    graph.add_node("section_writer", section_writer_node)
    graph.add_node("quality_recheck", quality_recheck_node)
    graph.add_node("validation", validation_node)
    graph.add_node("export", export_node)

    graph.add_edge("input_init", "web_search")
    graph.add_edge("web_search", "extraction")
    graph.add_edge("extraction", "relevance_check")
    graph.add_edge("outline", "section_writer")
    graph.add_edge("section_writer", "quality_recheck")
    graph.add_edge("export", END)

    graph.add_conditional_edges(
        "relevance_check",
        relevance_gate,
        {
            "pass": "outline",
            "retry": "web_search",
        },
    )

    graph.add_conditional_edges(
        "quality_recheck",
        quality_gate,
        {
            "pass": "validation",
            "retry": "section_writer",
        },
    )

    graph.add_conditional_edges(
        "validation",
        validation_gate,
        {
            "pass": "export",
            "fix_writing": "section_writer",
            "fix_outline": "outline",
        },
    )

    graph.set_entry_point("input_init")

    compiled = graph.compile()
    logger.info("Research pipeline graph compiled successfully")
    return compiled


research_graph = build_graph()

from typing import Any, Dict, Optional

from langgraph.graph import END, StateGraph

from src.documents.documents_state import DocumentsState
from src.documents.nodes.aggregate_documents_recommendations import (
    aggregate_documents_recommendations,
)
from src.documents.nodes.create_micro_verdicts import create_micro_verdicts
from src.documents.nodes.extract_document_info import extract_document_info
from src.documents.nodes.generate_file_focus import generate_file_focus
from src.documents.nodes.initialize_state import initialize_state
from src.documents.nodes.save_documents_result import save_documents_result

workflow = StateGraph(DocumentsState)

# Add all nodes
workflow.add_node("initialize_state", initialize_state)
workflow.add_node("generate_file_focus", generate_file_focus)
workflow.add_node("extract_document_info", extract_document_info)
workflow.add_node("create_micro_verdicts", create_micro_verdicts)
workflow.add_node("aggregate_documents_recommendations", aggregate_documents_recommendations)
workflow.add_node("save_documents_result", save_documents_result)

# Set entry point - initialize default values first
workflow.set_entry_point("initialize_state")

# Connect nodes in sequence
workflow.add_edge("initialize_state", "generate_file_focus")
workflow.add_edge("generate_file_focus", "extract_document_info")
workflow.add_edge("extract_document_info", "create_micro_verdicts")
workflow.add_edge("create_micro_verdicts", "aggregate_documents_recommendations")
workflow.add_edge("aggregate_documents_recommendations", "save_documents_result")
workflow.add_edge("save_documents_result", END)

graph = workflow.compile()


async def ainvoke_documents_workflow(
    state: DocumentsState, *, config: Optional[Dict[str, Any]] = None
) -> DocumentsState:
    """Async helper so callers can await the workflow directly."""
    return await graph.ainvoke(state, config=config)


def invoke_documents_workflow(
    state: DocumentsState, *, config: Optional[Dict[str, Any]] = None
) -> DocumentsState:
    """
    Sync helper retained for backwards compatibility.
    Prefers the async node implementations under the hood.
    """
    return graph.invoke(state, config=config)

from typing import Any, Dict, Optional

from langgraph.graph import StateGraph, END

from src.case_law.case_law_state import CaseLawState
from src.case_law.nodes.initialize_state import initialize_state
from src.case_law.nodes.generate_keywords import generate_keywords
from src.case_law.nodes.load_court_issue import load_court_issue
from src.case_law.nodes.search_case_law import search_caselaw
from src.case_law.nodes.fetch_case_document import fetch_case_document
from src.case_law.nodes.analyze_precedents import analyze_precedents
from src.case_law.nodes.judgement_focus import judgement_focus
from src.case_law.nodes.create_issue_guidelines import create_issue_guidelines
from src.case_law.nodes.micro_verdicts import micro_verdicts
from src.case_law.nodes.aggregate_recommendations import aggregate_recommendations
from src.case_law.nodes.save_result import save_result

workflow = StateGraph(CaseLawState)

# Add all nodes
workflow.add_node("initialize_state", initialize_state)
workflow.add_node("load_court_issue", load_court_issue)

# Pipeline A: Keyword-based case law search
workflow.add_node("generate_keywords", generate_keywords)
workflow.add_node("search_caselaw", search_caselaw)
workflow.add_node("fetch_case_document", fetch_case_document)
workflow.add_node("analyze_precedents", analyze_precedents)

# Pipeline B: Judgement focus analysis (runs in parallel)
workflow.add_node("judgement_focus", judgement_focus)

# Join point: Process judgement notes using both pipelines
workflow.add_node("create_issue_guidelines", create_issue_guidelines)

# Sequential post-processing
workflow.add_node("micro_verdicts", micro_verdicts)
workflow.add_node("aggregate_recommendations", aggregate_recommendations)

# Save results to disk
workflow.add_node("save_result", save_result)

# Set entry point - initialize default values first
workflow.set_entry_point("initialize_state")

# Connect initialization to load_court_issue
workflow.add_edge("initialize_state", "load_court_issue")

# Pipeline A edges (keyword search path)
workflow.add_edge("load_court_issue", "generate_keywords")
workflow.add_edge("generate_keywords", "search_caselaw")
workflow.add_edge("search_caselaw", "fetch_case_document")
workflow.add_edge("fetch_case_document", "analyze_precedents")

# Pipeline B edges (judgement focus path - runs in parallel)
workflow.add_edge("load_court_issue", "judgement_focus")

# Join both pipelines at create_issue_guidelines
workflow.add_edge("analyze_precedents", "create_issue_guidelines")
workflow.add_edge("judgement_focus", "create_issue_guidelines")

# Sequential processing after join
workflow.add_edge("create_issue_guidelines", "micro_verdicts")
workflow.add_edge("micro_verdicts", "aggregate_recommendations")

# Save results before ending
workflow.add_edge("aggregate_recommendations", "save_result")
workflow.add_edge("save_result", END)

graph = workflow.compile()


async def ainvoke_case_law_workflow(
    state: CaseLawState, *, config: Optional[Dict[str, Any]] = None
) -> CaseLawState:
    """Async helper mirroring the documents workflow ergonomic API."""
    return await graph.ainvoke(state, config=config)


def invoke_case_law_workflow(
    state: CaseLawState, *, config: Optional[Dict[str, Any]] = None
) -> CaseLawState:
    """Sync helper retained for backwards compatibility with existing callers."""
    return graph.invoke(state, config=config)


from typing import Any, Dict, Optional

from langgraph.graph import END, StateGraph

from src.judgement.judgement_state import JudgementState
from src.judgement.nodes.initialize_state import initialize_state
from src.judgement.nodes.draft_judgement import draft_judgement
from src.judgement.nodes.save_judgement import save_judgement

workflow = StateGraph(JudgementState)

workflow.add_node("initialize_state", initialize_state)
workflow.add_node("draft_judgement", draft_judgement)
workflow.add_node("save_judgement", save_judgement)

workflow.set_entry_point("initialize_state")
workflow.add_edge("initialize_state", "draft_judgement")
workflow.add_edge("draft_judgement", "save_judgement")
workflow.add_edge("save_judgement", END)

graph = workflow.compile()


async def ainvoke_judgement_workflow(
    state: JudgementState, *, config: Optional[Dict[str, Any]] = None
) -> JudgementState:
    return await graph.ainvoke(state, config=config)


def invoke_judgement_workflow(
    state: JudgementState, *, config: Optional[Dict[str, Any]] = None
) -> JudgementState:
    return graph.invoke(state, config=config)


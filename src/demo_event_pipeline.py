from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph


class DemoEventState(TypedDict, total=False):
    """Minimal state object for the demo graph."""

    topic: str
    outline: List[str]
    summary: str
    logs: List[str]


def _append_log(state: DemoEventState, message: str) -> List[str]:
    logs = list(state.get("logs", []))
    logs.append(message)
    return logs


def generate_outline(state: DemoEventState) -> DemoEventState:
    """Create a deterministic outline for the requested topic."""

    topic = state.get("topic") or "demo topic"
    outline = [
        f"Why {topic} matters",
        "Signal we observed",
        "Recommended next move",
    ]

    return {
        "outline": outline,
        "logs": _append_log(
            state,
            f"Generated outline with {len(outline)} bullets for `{topic}`.",
        ),
    }


def write_summary(state: DemoEventState) -> DemoEventState:
    """Transform the outline into a short narrative summary."""

    topic = state.get("topic") or "demo topic"
    outline = state.get("outline") or []
    summary = (
        f"For {topic}, we highlight {len(outline)} talking points: "
        + "; ".join(outline)
        + "."
    )

    return {
        "summary": summary,
        "logs": _append_log(
            state,
            f"Authored summary for `{topic}` with {len(outline)} sections.",
        ),
    }


workflow = StateGraph(DemoEventState)
workflow.add_node("generate_outline", generate_outline)
workflow.add_node("write_summary", write_summary)
workflow.set_entry_point("generate_outline")
workflow.add_edge("generate_outline", "write_summary")
workflow.add_edge("write_summary", END)

graph = workflow.compile()


async def ainvoke_demo_event_pipeline(
    state: Optional[DemoEventState] = None, *, config: Optional[Dict[str, Any]] = None
) -> DemoEventState:
    """Async helper mirroring other workflows in the repo."""

    initial_state = state or DemoEventState(topic="demo topic")
    return await graph.ainvoke(initial_state, config=config)


def invoke_demo_event_pipeline(
    state: Optional[DemoEventState] = None, *, config: Optional[Dict[str, Any]] = None
) -> DemoEventState:
    """Sync helper retained for parity with existing workflows."""

    initial_state = state or DemoEventState(topic="demo topic")
    return graph.invoke(initial_state, config=config)



from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from src.case_law.case_law_state import Issue

from .orchestrator_state import IssueWorkState, WorkflowSnapshot


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = PROJECT_ROOT / "dataset" / "orchestrator_state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

MAX_HISTORY = 5


def _issue_state_path(issue_index: int) -> Path:
    return STATE_DIR / f"issue_{issue_index}.json"


def _truncate_history(history: list[WorkflowSnapshot]) -> list[WorkflowSnapshot]:
    if len(history) <= MAX_HISTORY:
        return history
    return history[-MAX_HISTORY:]


def create_fresh_issue_state(issue: Issue, issue_index: int) -> IssueWorkState:
    """Initialize a brand-new issue state with sensible defaults."""
    return IssueWorkState(
        issue_index=issue_index,
        issue=issue,
        recommendation="",
        suggestion="",
        solved=False,
        documents=False,
        case_law=False,
        requires_documents=bool(issue.get("relevant_documents")),
        requires_case_law=True,
        seen_keywords=[],
        case_law_runs=[],
        document_runs=[],
    )


def save_issue_state(state: IssueWorkState) -> IssueWorkState:
    """Persist an issue state snapshot to local storage."""
    path = _issue_state_path(state["issue_index"])
    path.parent.mkdir(parents=True, exist_ok=True)
    serializable = dict(state)
    serializable["case_law_runs"] = _truncate_history(
        list(serializable.get("case_law_runs", []))
    )
    serializable["document_runs"] = _truncate_history(
        list(serializable.get("document_runs", []))
    )
    # Sets coming from CaseLawState need conversion
    seen_keywords = serializable.get("seen_keywords", [])
    if isinstance(seen_keywords, set):
        serializable["seen_keywords"] = sorted(seen_keywords)
    with path.open("w") as fp:
        json.dump(serializable, fp, indent=2)
    return state


def load_issue_state(issue_index: int) -> Optional[IssueWorkState]:
    """Load state if it exists; otherwise return None."""
    path = _issue_state_path(issue_index)
    if not path.exists():
        return None
    with path.open() as fp:
        data = json.load(fp)
    # Normalize types
    data["seen_keywords"] = data.get("seen_keywords", [])
    data["case_law_runs"] = data.get("case_law_runs", [])
    data["document_runs"] = data.get("document_runs", [])
    return IssueWorkState(**data)  # type: ignore[arg-type]


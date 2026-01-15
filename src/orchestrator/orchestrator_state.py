from __future__ import annotations

from typing import List, Literal, Optional, TypedDict

from src.case_law.case_law_state import Issue


class WorkflowSnapshot(TypedDict, total=False):
    """Minimal audit trail for any workflow run."""

    name: Literal["case_law", "documents"]
    recommendation: str
    suggestion: str
    solved: bool
    documents: bool
    case_law: bool


class IssueWorkState(TypedDict, total=False):
    """
    Persisted state for a single court issue while the deep agent hops
    between the case-law and documents workflows.
    """

    issue_index: int
    issue: Issue

    # Shared recommendation/suggestion that travels between workflows
    recommendation: str
    suggestion: str

    # Finalized signals
    solved: bool
    documents: bool
    case_law: bool

    # Routing hints
    requires_documents: bool
    requires_case_law: bool

    # Case-law memory to avoid repeated keyword searches
    seen_keywords: List[str]

    # Local workflow history for debugging + judgement context
    case_law_runs: List[WorkflowSnapshot]
    document_runs: List[WorkflowSnapshot]


class OrchestratorState(TypedDict, total=False):
    """State that powers the orchestrator deep agent loop."""

    issues: List[IssueWorkState]
    current_issue_index: int
    completed_issues: List[IssueWorkState]

    # Buffer that feeds the judgement workflow once everything is solved
    judgement_ready: bool
    judgement_payload: Optional[dict]


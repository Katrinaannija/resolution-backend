from __future__ import annotations

from typing import List, TypedDict

from src.orchestrator.orchestrator_state import IssueWorkState


class JudgementState(TypedDict, total=False):
    issues: List[IssueWorkState]

    issues_table: str
    case_citations: List[dict]  # All case law citations from all issues
    statement_of_claim: str
    statement_of_defence: str

    judgement: str

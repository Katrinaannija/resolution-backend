from __future__ import annotations

from typing import List

from src.judgement.judgement_state import JudgementState


def initialize_state(state: JudgementState) -> JudgementState:
    """Ensure the judgement workflow always has a table-friendly payload."""
    issues: List = state["issues"]

    rows = []

    for idx, issue in enumerate(issues, start=1):
        issue_data = issue["issue"]
        legal_issue = issue_data["legal_issue"]
        recommendation = issue["recommendation"].strip()
        claimant_position = issue_data["claimant_position"]
        defendant_position = issue_data["defendant_position"]
        date_event = issue_data["date_event"]

        rows.append(
            f"Issue {idx}: {date_event}\n"
            f"Legal Issue: {legal_issue}\n"
            f"Claimant Position: {claimant_position}\n"
            f"Defendant Position: {defendant_position}\n"
            f"Recommendation: {recommendation}"
        )

    return {
        "issues": issues,
        "issues_table": "\n\n---\n\n".join(rows),
        "statement_of_claim": state["statement_of_claim"],
        "statement_of_defence": state["statement_of_defence"],
    }


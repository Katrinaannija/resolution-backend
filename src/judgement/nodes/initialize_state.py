from __future__ import annotations

from typing import List

from src.judgement.judgement_state import JudgementState


def initialize_state(state: JudgementState) -> JudgementState:
    """Ensure the judgement workflow always has a table-friendly payload and compile case citations."""
    issues: List = state["issues"]

    rows = []
    all_case_citations = []

    for idx, issue in enumerate(issues, start=1):
        issue_data = issue["issue"]
        legal_issue = issue_data["legal_issue"]
        recommendation = issue["recommendation"].strip()
        claimant_position = issue_data.get("claimant_position", "")
        defendant_position = issue_data.get("defendant_position", "")
        date_event = issue_data.get("date_event", "")

        rows.append(
            f"Issue {idx}: {date_event}\n"
            f"Legal Issue: {legal_issue}\n"
            f"Claimant Position: {claimant_position}\n"
            f"Defendant Position: {defendant_position}\n"
            f"Recommendation: {recommendation}"
        )

        # Compile case citations from this issue
        supporting_cases = issue.get("supporting_cases", [])
        for case in supporting_cases:
            # Add issue context to the case citation
            case_with_context = dict(case)
            case_with_context["issue_index"] = idx
            case_with_context["legal_issue"] = legal_issue
            all_case_citations.append(case_with_context)

    return {
        "issues": issues,
        "issues_table": "\n\n---\n\n".join(rows),
        "case_citations": all_case_citations,
        "statement_of_claim": state["statement_of_claim"],
        "statement_of_defence": state["statement_of_defence"],
    }


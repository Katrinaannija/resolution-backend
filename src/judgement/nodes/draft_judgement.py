from __future__ import annotations

import json

from src.judgement.judgement_state import JudgementState
from src.utils.pull_prompt import pull_prompt
from src.utils.prompt_output import coerce_prompt_output


def draft_judgement(state: JudgementState) -> JudgementState:
    """Call the local prompt to summarize resolved issues with proper case citations."""
    prompt = pull_prompt("orchestrator_judgement_summary", include_model=True)

    # Format case citations for the prompt
    case_citations = state.get("case_citations", [])
    if case_citations:
        formatted_citations = "\n\n".join([
            f"Issue {case.get('issue_index')}: {case.get('legal_issue', 'N/A')}\n"
            f"Case: {case.get('case_name', 'Unknown')} {case.get('citation', 'N/A')}\n"
            f"Principle: {case.get('principle', 'N/A')}\n"
            f"Quote: \"{case.get('quote', 'N/A')}\"\n"
            f"Relevance: {case.get('relevance', 'N/A')}"
            for case in case_citations
        ])
    else:
        formatted_citations = "No case citations available."

    result = prompt.invoke(
        {
            "issues_table": state["issues_table"],
            "case_citations": formatted_citations,
            "claimant_statement": state.get("statement_of_claim", ""),
            "defendant_statement": state.get("statement_of_defence", ""),
        }
    )
    parsed = coerce_prompt_output(result)

    return {
        "judgement": parsed.get("judgement", "")
    }

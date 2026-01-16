import json

from src.case_law.case_law_state import CaseLawState
from src.utils.pull_prompt import pull_prompt_async
from src.utils.prompt_output import coerce_prompt_output


async def aggregate_recommendations(state: CaseLawState) -> CaseLawState:
    agg_prompt = await pull_prompt_async(
        "case_law_agg_recommendations",
        include_model=True,
    )

    issue = state["issue"]
    micro_verdicts = state.get("micro_verdicts", [])
    issue_guidelines = state.get("issue_guidelines", [])

    # Include issue guidelines in the formatted output so the LLM can see case citations
    formatted_verdicts = "\n\n".join(
        [
            f"Verdict {i + 1}:\n{json.dumps(verdict, indent=2)}"
            for i, verdict in enumerate(micro_verdicts)
        ]
    ) if micro_verdicts else "No micro verdicts available."

    # Also include the original guidelines which contain case citations
    formatted_guidelines = "\n\n---\n\n".join(
        [
            f"Guideline {i + 1}:\n{guideline}"
            for i, guideline in enumerate(issue_guidelines)
        ]
    ) if issue_guidelines else ""

    combined_input = f"{formatted_verdicts}\n\n=== ORIGINAL CASE LAW GUIDELINES (with citations) ===\n\n{formatted_guidelines}"

    result = await agg_prompt.ainvoke(
        {
            "date_event": issue.get("date_event", ""),
            "undisputed_facts": issue.get("undisputed_facts", ""),
            "claimant_position": issue.get("claimant_position", ""),
            "defendant_position": issue.get("defendant_position", ""),
            "legal_issue": issue.get("legal_issue", ""),
            "micro_verdicts": combined_input,
        }
    )

    parsed = coerce_prompt_output(result)
    print("[aggregate_recommendations] Output:", json.dumps(parsed, indent=2))

    # Extract supporting_cases if present
    supporting_cases = parsed.get("supporting_cases", [])

    return {
        "recommendation": parsed.get("recommendation", ""),
        "suggestion": parsed.get("suggestion", ""),
        "solved": parsed.get("solved", False),
        "documents": parsed.get("documents", False),
        "case_law": parsed.get("case_law", False),
        "supporting_cases": supporting_cases,  # NEW: Preserve cited cases
    }


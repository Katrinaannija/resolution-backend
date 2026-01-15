import json

from src.case_law.case_law_state import CaseLawState
from src.utils.pull_prompt import pull_prompt_async


async def aggregate_recommendations(state: CaseLawState) -> CaseLawState:
    agg_prompt = await pull_prompt_async(
        "case_law_agg_recommendations",
        include_model=True,
    )

    issue = state["issue"]
    micro_verdicts = state.get("micro_verdicts", [])

    formatted_verdicts = (
        "\n\n".join(
            [
                f"Verdict {i + 1}:\n{json.dumps(verdict, indent=2)}"
                for i, verdict in enumerate(micro_verdicts)
            ]
        )
        if micro_verdicts
        else "No micro verdicts available."
    )

    result = await agg_prompt.ainvoke(
        {
            "date_event": issue.get("date_event", ""),
            "undisputed_facts": issue.get("undisputed_facts", ""),
            "claimant_position": issue.get("claimant_position", ""),
            "defendant_position": issue.get("defendant_position", ""),
            "legal_issue": issue.get("legal_issue", ""),
            "micro_verdicts": formatted_verdicts,
        }
    )

    print(result)

    return {
        "recommendation": result.get("recommendation", ""),
        "suggestion": result.get("suggestion", ""),
        "solved": result.get("solved", False),
        "documents": result.get("documents", False),
        "case_law": result.get("case_law", False),
    }


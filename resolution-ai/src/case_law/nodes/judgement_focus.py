from src.case_law.case_law_state import CaseLawState
from src.utils.pull_prompt import pull_prompt_async


async def judgement_focus(state: CaseLawState) -> CaseLawState:
    """
    Analyzes the court judgment and extracts neutral, structured, citation-based information
    relevant to the legal issue. This runs in parallel with the keyword generation pipeline.
    """
    focus_prompt = await pull_prompt_async(
        "case_law_judgement_focus",
        include_model=True,
    )

    issue = state["issue"]
    output = await focus_prompt.ainvoke(
        {
            "date_event": issue.get("date_event", ""),
            "undisputed_facts": issue.get("undisputed_facts", ""),
            "claimant_position": issue.get("claimant_position", ""),
            "defendant_position": issue.get("defendant_position", ""),
            "legal_issue": issue.get("legal_issue", ""),
            "recommendation": state.get("recommendation", ""),
            "suggestions": state.get("suggestion", ""),
        }
    )

    return {
        "focus_area": output.content,
    }

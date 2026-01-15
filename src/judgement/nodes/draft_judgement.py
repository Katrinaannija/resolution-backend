from __future__ import annotations

from src.judgement.judgement_state import JudgementState
from src.utils.pull_prompt import pull_prompt
from src.utils.prompt_output import coerce_prompt_output


def draft_judgement(state: JudgementState) -> JudgementState:
    """Call the local prompt to summarize resolved issues."""
    prompt = pull_prompt("orchestrator_judgement_summary", include_model=True)
    result = prompt.invoke(
        {
            "issues_table": state["issues_table"],
            "claimant_statement": state.get("statement_of_claim", ""),
            "defendant_statement": state.get("statement_of_defence", ""),
        }
    )
    parsed = coerce_prompt_output(result)

    return {
        "judgement": parsed.get("judgement", "")
    }

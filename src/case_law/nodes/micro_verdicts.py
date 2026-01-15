from typing import Dict, List

from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough

from src.case_law.case_law_state import CaseLawState
from src.utils.pull_prompt import pull_prompt_async
from src.utils.prompt_output import coerce_prompt_output

async def micro_verdicts(state: CaseLawState) -> CaseLawState:
    micro_verdict_prompt = await pull_prompt_async(
        "case_law_micro_verdict",
        include_model=True,
    )    
    issue = state["issue"]
    issue_guidelines: List[str] = state["issue_guidelines"]

    base_context = {
        "date_event": issue.get("date_event", ""),
        "undisputed_facts": issue.get("undisputed_facts", ""),
        "claimant_position": issue.get("claimant_position", ""),
        "defendant_position": issue.get("defendant_position", ""),
        "legal_issue": issue.get("legal_issue", ""),
        "relevant_documents": "\n".join(issue.get("relevant_documents", []) or []),
        "recommendation": state.get("recommendation", ""),
    }

    payload_builder = (
        RunnableParallel(
            issue_guidelines=RunnablePassthrough(),
            context=RunnableLambda(lambda _: base_context),
        )
        | RunnableLambda(
            lambda payload: {
                **payload["context"],
                "issue_guidelines": payload["issue_guidelines"],
            }
        )
    )
    prompt_payloads = await payload_builder.abatch(issue_guidelines)
    results = await micro_verdict_prompt.abatch(
        prompt_payloads,
        config={"max_concurrency": len(prompt_payloads) or 1},
    )

    micro_verdicts = []

    for res in results:
        parsed = coerce_prompt_output(res)
        micro_verdicts.append({
            "recommendation": parsed.get("recommendation", ""),
            "suggestion": parsed.get("suggestion", ""),
            "solved": parsed.get("solved", False),
            "documents": parsed.get("documents", False),
            "case_law": parsed.get("case_law", False),
        })

    return {"micro_verdicts": micro_verdicts}


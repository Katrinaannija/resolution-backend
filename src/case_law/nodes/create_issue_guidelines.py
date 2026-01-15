from typing import List

from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough

from src.case_law.case_law_state import CaseLawState
from src.utils.local_prompts import pull_prompt_async


async def create_issue_guidelines(state: CaseLawState) -> CaseLawState:
    issue_guidelines_prompt = await pull_prompt_async(
        "case_law_issue_guidelines",
        include_model=True,
    )

    fetched_documents: List[str] = state.get("fetched_case_documents", []) or []
    focus_area = state.get("focus_area", "")

    if not fetched_documents:
        return {"issue_guidelines": []}

    payload_builder = RunnableParallel(
        court_judgment=RunnablePassthrough(),
        focus_area=RunnableLambda(lambda _: focus_area),
    )

    prompt_payloads = await payload_builder.abatch(fetched_documents)

    results = await issue_guidelines_prompt.abatch(
        prompt_payloads,
        config={"max_concurrency": len(prompt_payloads) or 1},
    )

    all_guidelines = [result.content for result in results]

    return {
        "issue_guidelines": all_guidelines,
    }


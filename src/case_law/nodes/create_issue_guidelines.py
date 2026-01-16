from typing import List

from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough

from src.case_law.case_law_state import CaseLawState
from src.utils.pull_prompt import pull_prompt_async


async def create_issue_guidelines(state: CaseLawState) -> CaseLawState:
    issue_guidelines_prompt = await pull_prompt_async(
        "case_law_issue_guidelines",
        include_model=True,
    )

    fetched_documents: List[str] = state.get("fetched_case_documents", []) or []
    case_metadata_list: List[dict] = state.get("case_metadata", []) or []
    focus_area = state.get("focus_area", "")

    if not fetched_documents:
        return {"issue_guidelines": []}

    # Zip documents with their metadata
    documents_with_metadata = []
    for i, doc in enumerate(fetched_documents):
        metadata = case_metadata_list[i] if i < len(case_metadata_list) else {}
        case_citation = f"{metadata.get('name', 'Unknown')} {metadata.get('citation', 'N/A')}"
        documents_with_metadata.append({
            "judgment_text": doc,
            "case_citation": case_citation,
            "case_name": metadata.get('name', 'Unknown Case'),
            "citation": metadata.get('citation', 'N/A'),
            "court": metadata.get('court', 'N/A'),
            "date": metadata.get('date', 'N/A')
        })

    payload_builder = RunnableParallel(
        court_judgment=RunnableLambda(lambda x: x["judgment_text"]),
        case_citation=RunnableLambda(lambda x: x["case_citation"]),
        case_name=RunnableLambda(lambda x: x["case_name"]),
        citation=RunnableLambda(lambda x: x["citation"]),
        court=RunnableLambda(lambda x: x["court"]),
        date=RunnableLambda(lambda x: x["date"]),
        focus_area=RunnableLambda(lambda _: focus_area),
    )

    prompt_payloads = await payload_builder.abatch(documents_with_metadata)

    results = await issue_guidelines_prompt.abatch(
        prompt_payloads,
        config={"max_concurrency": len(prompt_payloads) or 1},
    )

    all_guidelines = [result.content for result in results]

    return {
        "issue_guidelines": all_guidelines,
    }


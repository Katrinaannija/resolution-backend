from typing import List

from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)

from src.documents.documents_state import DocumentInfo, DocumentsState
from src.tools.document_store import retrieve_document
from src.utils.pull_prompt import pull_prompt_async


async def extract_document_info(state: DocumentsState) -> DocumentsState:
    """
    Parallel document extraction powered by LangChain runnables.
    Each filename fans out into (retrieve_document + extraction_prompt) branches
    that execute concurrently via `abatch`.
    """
    file_names: List[str] = state.get("file_names", []) or []
    if not file_names:
        return {"document_infos": []}

    focus_area = state.get("file_focus", "")
    extraction_prompt = await pull_prompt_async(
        "documents_extract_content",
        include_model=True,
    )

    # RunnableParallel duplicates the filename input so we can fetch the file
    # and keep metadata for the prompt simultaneously.
    prompt_input_builder = (
        RunnableParallel(
            filename=RunnablePassthrough(),
            document_content=RunnableLambda(lambda filename: {"filename": filename})
            | retrieve_document,
        )
        | RunnableLambda(lambda payload: {**payload, "focus_area": focus_area})
    )

    prompt_payloads = await prompt_input_builder.abatch(file_names)

    # Fan out across every filename with an async batch to get true concurrent LLM calls.
    extraction_results = await extraction_prompt.abatch(
        prompt_payloads,
        config={"max_concurrency": len(file_names) or 1},
    )

    document_infos: List[DocumentInfo] = []

    for filename, result in zip(file_names, extraction_results):
        document_content = result.content  # type: ignore[attr-defined]

        print(f"Extracted info from {filename}:\n{document_content}\n")

        document_infos.append(
            DocumentInfo(
                filename=filename,
                document_content=document_content,
            )
        )

    return {"document_infos": document_infos}


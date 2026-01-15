from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda, RunnableParallel

from src.case_law.case_law_state import CaseLawState
from src.case_law_workflow import ainvoke_case_law_workflow
from src.documents.documents_state import DocumentsState
from src.documents_workflow import ainvoke_documents_workflow

load_dotenv()


async def run_cos_agent(issue_index: int = 0) -> Dict[str, Any]:
    """
    Run the documents and case-law LangGraph workflows concurrently.

    Args:
        issue_index: Which issue from court_issues.json to analyze.

    Returns:
        Aggregated payload containing both workflow outputs plus combined advice.
    """
    case_law_state: CaseLawState = CaseLawState(issue_index=issue_index)
    documents_state: DocumentsState = DocumentsState(issue_index=issue_index)

    parallel = RunnableParallel(
        case_law=RunnableLambda(
            lambda payload: ainvoke_case_law_workflow(payload["case_law_state"])
        ),
        documents=RunnableLambda(
            lambda payload: ainvoke_documents_workflow(payload["documents_state"])
        ),
    )

    results = await parallel.ainvoke(
        {
            "case_law_state": case_law_state,
            "documents_state": documents_state,
        }
    )

    case_law_result = results["case_law"]
    documents_result = results["documents"]

    aggregated = {
        "issue_index": issue_index,
        "case_law": case_law_result,
        "documents": documents_result,
        "combined_recommendation": documents_result.get("final_recommendation")
        or case_law_result.get("recommendation")
        or "",
        "combined_suggestion": documents_result.get("final_suggestion")
        or case_law_result.get("suggestion")
        or "",
    }

    return aggregated


def run(issue_index: int = 0) -> Dict[str, Any]:
    """Synchronous helper for CLI usage."""
    return asyncio.run(run_cos_agent(issue_index=issue_index))


if __name__ == "__main__":
    outcome = run()
    print(json.dumps(outcome, indent=2, ensure_ascii=False))

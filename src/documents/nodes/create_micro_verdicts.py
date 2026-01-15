import asyncio
import json
from typing import List

from src.documents.documents_state import DocumentsState, MicroVerdict
from src.utils.pull_prompt import pull_prompt_async


async def create_micro_verdicts(state: DocumentsState) -> DocumentsState:
    """
    Step 3: Create micro verdicts from extracted document information.
    
    Each document info is processed concurrently via LangChain's `abatch`,
    ensuring we issue parallel LLM calls instead of looping sequentially.
    """
    issue = state["issue"]
    recommendation = state.get("recommendation", "")
    document_infos = state.get("document_infos", []) or []
    
    if not document_infos:
        return {"micro_verdicts": []}

    # Pull the micro verdict prompt from local registry
    micro_verdict_prompt = await pull_prompt_async(
        "documents_create_micro_verdict",
        include_model=True,
    )
    
    payloads: List[dict] = [
        {
            "filename": doc_info["filename"],
            "document_content": doc_info["document_content"],
            "date_event": issue.get("date_event", ""),
            "undisputed_facts": issue.get("undisputed_facts", ""),
            "claimant_position": issue.get("claimant_position", ""),
            "defendant_position": issue.get("defendant_position", ""),
            "legal_issue": issue.get("legal_issue", ""),
            "recommendation": recommendation,
        }
        for doc_info in document_infos
    ]
    
    results = await micro_verdict_prompt.abatch(
        payloads,
        config={"max_concurrency": len(payloads) or 1},
    )
    
    micro_verdicts: List[MicroVerdict] = []
    
    for doc_info, result in zip(document_infos, results):
        filename = doc_info["filename"]
        
        micro_verdict = MicroVerdict(
            filename=filename,
            recommendation=result.get("recommendation", ""),
            suggestion=result.get("suggestion", ""),
            solved=result.get("solved", False),
            documents=result.get("documents", False),
            case_law=result.get("case_law", False),
        )
        
        print(f"Created micro verdict for {filename}:\n{json.dumps(micro_verdict, indent=2)}\n")
        
        micro_verdicts.append(micro_verdict)
    
    return {
        "micro_verdicts": micro_verdicts
    }


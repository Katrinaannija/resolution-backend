from typing import List

from src.case_law.case_law_state import CaseLawState
from src.utils.local_prompts import pull_prompt_async


async def generate_keywords(state: CaseLawState) -> CaseLawState:
    keyword_prompt = await pull_prompt_async(
        "case_law_keywords",
        include_model=True,
    )

    issue = state["issue"]
    payload = {
        "date_event": issue.get("date_event", ""),
        "undisputed_facts": issue.get("undisputed_facts", ""),
        "claimant_position": issue.get("claimant_position", ""),
        "defendant_position": issue.get("defendant_position", ""),
        "legal_issue": issue.get("legal_issue", ""),
        "relevant_documents": "\n".join(issue.get("relevant_documents", [])),
        "num_keywords": 2,
        "seen_keywords": list(state.get("seen_keywords", set())),
    }

    output = await keyword_prompt.ainvoke(payload)

    keywords: List[str] = output.get("keywords", [])
    seen_keywords = set(keywords) | set(state.get("seen_keywords", set()))

    return {
        "keywords": keywords,
        "seen_keywords": seen_keywords,
    }

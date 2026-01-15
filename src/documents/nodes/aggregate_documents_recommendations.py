from src.documents.documents_state import DocumentsState
from src.utils.pull_prompt import pull_prompt

def aggregate_documents_recommendations(state: DocumentsState) -> DocumentsState:
    """
    Step 4: Aggregate all micro verdicts into final recommendation and suggestion.
    
    Combines all micro verdicts and their extensions into a single cohesive
    recommendation and suggestion that incorporates all the document evidence.
    """
    agg_prompt = pull_prompt(
        "documents_agg_micro_verdicts", include_model=True
    )
    
    issue = state["issue"]
    recommendation = state.get("recommendation", "")
    suggestion = state.get("suggestion", "")
    micro_verdicts = state.get("micro_verdicts", [])
    
    # Format micro_verdicts as string
    formatted_verdicts = "\n\n".join([
        f"Document: {verdict['filename']}\n"
        f"Recommendation Extension: {verdict['recommendation']}\n"
        f"Suggestion Extension: {verdict['suggestion']}"
        for verdict in micro_verdicts
    ]) if micro_verdicts else "No micro verdicts available."
    
    # Invoke the aggregation prompt
    result = agg_prompt.invoke({
        "date_event": issue.get("date_event", ""),
        "undisputed_facts": issue.get("undisputed_facts", ""),
        "claimant_position": issue.get("claimant_position", ""),
        "defendant_position": issue.get("defendant_position", ""),
        "legal_issue": issue.get("legal_issue", ""),
        "current_recommendation": recommendation,
        "current_suggestion": suggestion,
        "micro_verdicts": formatted_verdicts
    })
    
    final_recommendation = result.get("recommendation", "")
    final_suggestion = result.get("suggestion", "")
    solved = result.get("solved", False)
    documents = result.get("documents", False)
    case_law = result.get("case_law", False)
    
    print(f"\nFinal Recommendation:\n{final_recommendation}\n")
    print(f"\nFinal Suggestion:\n{final_suggestion}\n")
    print(f"Solved: {solved}, Documents: {documents}, Case Law: {case_law}\n")
    
    return {
        "final_recommendation": final_recommendation,
        "final_suggestion": final_suggestion,
        "solved": solved,
        "documents": documents,
        "case_law": case_law
    }


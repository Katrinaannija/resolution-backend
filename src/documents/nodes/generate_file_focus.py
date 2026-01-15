from src.documents.documents_state import DocumentsState
from src.tools.document_store import get_all_document_details
from src.utils.local_prompts import pull_prompt

def generate_file_focus(state: DocumentsState) -> DocumentsState:
    """
    Step 1: Generate list of files to inspect and extraction goals for each file.
    
    Takes issue, recommendation, and suggestion as input.
    Generates a list of files that need to be inspected and what information 
    we're looking for in each file.
    """
    # Pull the prompt from local prompts
    file_instruction_prompt = pull_prompt(
        "documents_focus_area", include_model=True
    )
    
    issue = state["issue"]
    recommendation = state.get("recommendation", "")
    suggestion = state.get("suggestion", "")
    
    all_doc_details = get_all_document_details.invoke({})
   
    result = file_instruction_prompt.invoke({
        "date_event": issue.get("date_event", ""),
        "undisputed_facts": issue.get("undisputed_facts", ""),
        "claimant_position": issue.get("claimant_position", ""),
        "defendant_position": issue.get("defendant_position", ""),
        "legal_issue": issue.get("legal_issue", ""),
        "relevant_documents": ", ".join(issue.get("relevant_documents", [])),
        "all_document_details": all_doc_details,
        "recommendation": recommendation,
        "suggestion": suggestion
    })
    
    return {
        "file_focus": result["file_focus"],
        "file_names": result["file_names"]
    }


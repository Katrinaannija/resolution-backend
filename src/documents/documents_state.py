from typing import TypedDict, List

class Issue(TypedDict, total=False):
    date_event: str
    undisputed_facts: str
    claimant_position: str
    defendant_position: str
    legal_issue: str
    relevant_documents: List[str]

class DocumentInfo(TypedDict):
    """LLM-extracted summary for a document."""
    filename: str
    document_content: str

class MicroVerdict(TypedDict):
    """Micro verdict created from document information."""
    filename: str
    recommendation: str
    suggestion: str
    solved: bool
    documents: bool
    case_law: bool

class DocumentsState(TypedDict, total=False):
    # Input fields
    issue_index: int
    issue: Issue
    recommendation: str
    suggestion: str
    
    # Step 1: File instructions
    file_focus: str
    file_names: List[str]
    
    # Step 2: Extracted document information
    document_infos: List[DocumentInfo]
    
    # Step 3: Micro verdicts
    micro_verdicts: List[MicroVerdict]
    
    # Final output
    final_recommendation: str
    final_suggestion: str
    solved: bool
    documents: bool
    case_law: bool

def create_initial_documents_state(
    issue: Issue = None, 
    issue_index: int = 0,
    recommendation: str = "", 
    suggestion: str = ""
) -> DocumentsState:
    """Create a DocumentsState with default values initialized."""
    return DocumentsState(
        issue_index=issue_index,
        issue=issue,
        recommendation=recommendation,
        suggestion=suggestion,
        file_instructions=[],
        document_infos=[],
        micro_verdicts=[],
        final_recommendation="",
        final_suggestion="",
        solved=False,
        documents=False,
        case_law=False
    )


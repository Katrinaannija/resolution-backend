from typing import TypedDict, List

class Issue(TypedDict, total=False):
    date_event: str
    undisputed_facts: str
    claimant_position: str
    defendant_position: str
    legal_issue: str
    relevant_documents: List[str]

class CaseLawState(TypedDict, total=False):
    # index from court issues json, work on a specific issue
    issue_index: int
    issue: Issue
    
    # partial or final output of the pipeline
    # contains legal resolution on the issue 
    recommendation: str
    # intermidiate value used for next iteration to resolve the issue
    suggestion: str
    # history of searched keywords
    seen_keywords: set[str]
    
    keywords: List[str]
    cases: List[dict]
    fetched_case_documents: List[str]  # Changed to list to store multiple documents
    
    # Pipeline B: judgement focus analysis
    focus_area: str
    
    # Joined output
    issue_guidelines: List[str]  # Changed to list to store multiple guidelines
    
    # Micro verdicts from update_recommendation
    micro_verdicts: List[dict]  # List of micro verdicts generated from issue guidelines
    
    solved: bool
    documents: bool
    case_law: bool
    
    output_text: str

def create_initial_state(issue_index: int = 0) -> CaseLawState:
    """Create a CaseLawState with default values initialized."""
    return CaseLawState(
        issue_index=issue_index,
        issue=Issue(
            date_event="",
            undisputed_facts="",
            claimant_position="",
            defendant_position="",
            legal_issue="",
            relevant_documents=[]
        ),
        recommendation="",
        suggestion="",
        seen_keywords=set(),
        keywords=[],
        cases=[],
        fetched_case_documents=[],
        focus_area="",
        issue_guidelines=[],
        micro_verdicts=[],
        output_text=""
    )
 
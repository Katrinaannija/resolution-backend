from src.case_law.case_law_state import CaseLawState, Issue

def initialize_state(state: CaseLawState) -> CaseLawState:
    """
    Initialize default values for all state fields if they are not set.
    This ensures all fields have proper default values throughout the workflow.
    """
    updates = {}
    
    if "issue_index" not in state or state.get("issue_index") is None:
        updates["issue_index"] = 0
    
    if "issue" not in state or state.get("issue") is None:
        updates["issue"] = Issue(
            date_event="",
            undisputed_facts="",
            claimant_position="",
            defendant_position="",
            legal_issue="",
            relevant_documents=[]
        )
    
    if "recommendation" not in state or state.get("recommendation") is None:
        updates["recommendation"] = ""
    
    if "suggestion" not in state or state.get("suggestion") is None:
        updates["suggestion"] = ""
    
    if "seen_keywords" not in state or state.get("seen_keywords") is None:
        updates["seen_keywords"] = set()
    
    if "keywords" not in state or state.get("keywords") is None:
        updates["keywords"] = []
    
    if "cases" not in state or state.get("cases") is None:
        updates["cases"] = []
    
    if "focus_area" not in state or state.get("focus_area") is None:
        updates["focus_area"] = ""
    
    if "issue_guidelines" not in state or state.get("issue_guidelines") is None:
        updates["issue_guidelines"] = []
    
    if "output_text" not in state or state.get("output_text") is None:
        updates["output_text"] = ""
    
    if "fetched_case_documents" not in state or state.get("fetched_case_documents") is None:
        updates["fetched_case_documents"] = []
        
    if "micro_verdicts" not in state or state.get("micro_verdicts") is None:
        updates["micro_verdicts"] = []
    
    return updates


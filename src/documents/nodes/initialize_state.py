import json

from src.utils.json_sanitize import load_json_file
from pathlib import Path
from typing import Optional, Tuple
from src.documents.documents_state import DocumentsState, Issue


def load_from_verdict(issue_index: int) -> Optional[Tuple[Issue, str, str]]:
    """
    Load issue, recommendation, and suggestion from a saved verdict file.
    
    Args:
        issue_index: The index of the issue to load
        
    Returns:
        Tuple of (Issue, recommendation, suggestion) if verdict file exists, None otherwise
    """
    verdict_path = Path(__file__).parent.parent.parent.parent / "dataset" / "issue_verdicts" / f"issue_{issue_index}.json"
    
    if not verdict_path.exists():
        return None
    
    with open(verdict_path, "r") as f:
        verdict_data = json.load(f)
    
    # Load issue from full_issue field
    full_issue = verdict_data.get("full_issue", {})
    issue = Issue(
        date_event=full_issue.get("date_event", ""),
        undisputed_facts=full_issue.get("undisputed_facts", ""),
        claimant_position=full_issue.get("claimant_position", ""),
        defendant_position=full_issue.get("defendant_position", ""),
        legal_issue=full_issue.get("legal_issue", ""),
        relevant_documents=full_issue.get("relevant_documents", [])
    )
    
    # Load recommendation and suggestion from verdict
    # Using 'suggestion' field as it contains the detailed case law analysis
    recommendation = verdict_data.get("suggestion", "")
    suggestion = verdict_data.get("suggestion", "")
    
    return (issue, recommendation, suggestion)


def initialize_state(state: DocumentsState) -> DocumentsState:
    """
    Initialize default values for all state fields if they are not set.
    This ensures all fields have proper default values throughout the workflow.
    If issue is empty, loads it from file using issue_index.
    Priority: 1) saved verdict file, 2) court_issues.json
    """
    updates = {}
    
    # Load issue from file if it's empty
    if "issue" not in state or state.get("issue") is None or not state.get("issue", {}).get("legal_issue"):
        issue_index = state.get("issue_index", 0)
        
        # Try to load from saved verdict first
        verdict_result = load_from_verdict(issue_index)
        
        if verdict_result is not None:
            # Load from saved verdict
            issue, recommendation, suggestion = verdict_result
            updates["issue"] = issue
            
            # Load recommendation and suggestion from verdict
            if "recommendation" not in state or state.get("recommendation") is None:
                updates["recommendation"] = recommendation
            
            if "suggestion" not in state or state.get("suggestion") is None:
                updates["suggestion"] = suggestion
        else:
            # Fall back to loading from court_issues.json
            data = load_json_file("dataset/court_issues/court_issues.json")
            
            event = data["events"][issue_index]
            
            updates["issue"] = Issue(
                date_event=event.get("date_event", ""),
                undisputed_facts=event.get("undisputed_facts", ""),
                claimant_position=event.get("claimant_position", ""),
                defendant_position=event.get("defendant_position", ""),
                legal_issue=event.get("legal_issue", ""),
                relevant_documents=event.get("relevant_documents", []) or []
            )
            
            # Initialize empty if not loading from verdict
            if "recommendation" not in state or state.get("recommendation") is None:
                updates["recommendation"] = ""
            
            if "suggestion" not in state or state.get("suggestion") is None:
                updates["suggestion"] = ""
    else:
        # Issue already exists, just ensure recommendation and suggestion have defaults
        if "recommendation" not in state or state.get("recommendation") is None:
            updates["recommendation"] = ""
        
        if "suggestion" not in state or state.get("suggestion") is None:
            updates["suggestion"] = ""
    
    if "file_instructions" not in state or state.get("file_instructions") is None:
        updates["file_instructions"] = []
    
    if "document_infos" not in state or state.get("document_infos") is None:
        updates["document_infos"] = []
    
    if "micro_verdicts" not in state or state.get("micro_verdicts") is None:
        updates["micro_verdicts"] = []
    
    if "final_recommendation" not in state or state.get("final_recommendation") is None:
        updates["final_recommendation"] = ""
    
    if "final_suggestion" not in state or state.get("final_suggestion") is None:
        updates["final_suggestion"] = ""
    
    return updates


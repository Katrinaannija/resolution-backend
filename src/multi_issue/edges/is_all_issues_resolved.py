
from src.multi_issue.multi_issue_state import MultiIssueState

def is_all_issues_resolved(state: MultiIssueState) -> dict:
    current_result = state.get("current_issue_result")
    
    issue_results = state.get("issue_results", []).copy()
    issue_results.append(current_result)
    
    current_idx = state.get("current_issue_index", 0)
    total = state.get("total_issues", 0)
    next_idx = current_idx + 1
    
    all_done = next_idx >= total
    
    return {
        "issue_results": issue_results,
        "current_issue_index": next_idx,
        "all_processed": all_done
    }


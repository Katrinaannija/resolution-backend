import json
from pathlib import Path
from src.multi_issue.multi_issue_state import MultiIssueState

def load_issues(_: MultiIssueState) -> dict:
    issues_file = Path(__file__).parent.parent.parent.parent / "dataset" / "court_issues" / "court_issues.json"
    
    with open(issues_file, 'r') as f:
        data = json.load(f)
    
    all_issues = data.get("events", [])
    
    print(f"Loaded {len(all_issues)} court issues from {issues_file}")
    
    return {
        "all_issues": all_issues,
        "total_issues": len(all_issues),
        "current_issue_index": 0,
        "issue_results": [],
        "all_processed": False
    }


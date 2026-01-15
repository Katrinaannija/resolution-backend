from typing import TypedDict, List
from src.case_law.case_law_state import Issue

class IssueResult(TypedDict, total=False):
    issue_index: int
    issue: Issue
    recommendation: str
    suggestion: str
    solved: bool
    documents: bool
    case_law: bool
    micro_verdicts: List[dict]
    keywords: List[str]
    focus_area: str

class MultiIssueState(TypedDict, total=False):
    # List of all issues loaded from court_issues.json
    all_issues: List[Issue]
    
    # Current issue being processed
    current_issue_index: int
    
    # Result from the most recently processed issue (temporary storage)
    current_issue_result: IssueResult
    
    # Results from processing all issues
    issue_results: List[IssueResult]
    
    # Total number of issues
    total_issues: int
    
    # Flag to indicate if all issues are processed
    all_processed: bool


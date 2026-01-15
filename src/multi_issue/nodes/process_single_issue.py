from src.multi_issue.multi_issue_state import MultiIssueState, IssueResult
from src.case_law.case_law_state import CaseLawState
from src.case_law_workflow import graph as case_law_graph

def process_single_issue(state: MultiIssueState) -> dict:
    current_idx = state.get("current_issue_index", 0)
    all_issues = state.get("all_issues", [])
    
    if current_idx >= len(all_issues):
        print(f"No more issues to process (index {current_idx} >= {len(all_issues)})")
        return {"all_processed": True}
    
    current_issue = all_issues[current_idx]
    
    print(f"\n{'='*80}")
    print(f"Processing Issue {current_idx + 1}/{len(all_issues)}")
    print(f"Date: {current_issue.get('date_event', 'N/A')}")
    print(f"{'='*80}\n")
    
    subgraph_input: CaseLawState = {
        "issue_index": current_idx,
    }
    
    result = case_law_graph.invoke(subgraph_input)
    
    issue_result: IssueResult = {
        "issue_index": current_idx,
        "issue": current_issue,
        "recommendation": result.get("recommendation", ""),
        "suggestion": result.get("suggestion", ""),
        "solved": result.get("solved", False),
        "documents": result.get("documents", False),
        "case_law": result.get("case_law", False),
        "micro_verdicts": result.get("micro_verdicts", []),
        "keywords": result.get("keywords", []),
        "focus_area": result.get("focus_area", "")
    }
    
    print(f"\n{'='*80}")
    print(f"Completed Issue {current_idx + 1}/{len(all_issues)}")
    print(f"Solved: {issue_result['solved']}")
    print(f"{'='*80}\n")
    
    return {
        "current_issue_result": issue_result
    }


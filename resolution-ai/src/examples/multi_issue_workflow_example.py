"""
Example script demonstrating how to use the multi-issue workflow.

This workflow processes all court issues from court_issues.json through
the case law workflow as a subgraph, saving partial results after each
issue is processed.
"""

import os

GLOBAL_MODEL = os.getenv("GLOBAL_MODEL", "gpt-5.1-mini")
# Override this value when iterating with smaller models.
os.environ["GLOBAL_MODEL"] = GLOBAL_MODEL

from src.multi_issue_workflow import graph
from src.multi_issue.multi_issue_state import MultiIssueState

def run_multi_issue_workflow():
    """
    Run the multi-issue workflow to process all court issues.
    
    The workflow will:
    1. Load all issues from dataset/court_issues/court_issues.json
    2. Process each issue through the case law workflow
    3. Save partial results after each issue to dataset/issue_verdicts/
    4. Save final aggregated results when all issues are processed
    """
    print("Starting Multi-Issue Case Law Workflow")
    print("=" * 80)
    
    # Initialize empty state - the workflow will populate it
    initial_state: MultiIssueState = {}
    
    # Run the workflow
    final_state = graph.invoke(initial_state)
    
    print("\n" + "=" * 80)
    print("Multi-Issue Workflow Completed!")
    print("=" * 80)
    
    # Print summary
    total = final_state.get("total_issues", 0)
    processed = len(final_state.get("issue_results", []))
    
    print(f"\nProcessed {processed} out of {total} issues")
    print(f"Results saved in dataset/issue_verdicts/")
    
    return final_state

if __name__ == "__main__":
    result = run_multi_issue_workflow()


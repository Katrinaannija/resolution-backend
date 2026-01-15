from langgraph.graph import StateGraph, END
from src.multi_issue.multi_issue_state import MultiIssueState
from src.multi_issue.nodes.load_issues import load_issues
from src.multi_issue.nodes.process_single_issue import process_single_issue
from src.multi_issue.edges.is_all_issues_resolved import is_all_issues_resolved
from src.multi_issue.nodes.save_final_results import save_final_results

def should_continue(state: MultiIssueState) -> str:
    all_processed = state.get("all_processed", False)
    
    if all_processed:
        return "save_final"
    else:
        return "process_issue"

workflow = StateGraph(MultiIssueState)

# Add nodes
workflow.add_node("load_issues", load_issues)
workflow.add_node("process_single_issue", process_single_issue)
workflow.add_node("is_all_issues_resolved", is_all_issues_resolved)
workflow.add_node("save_final_results", save_final_results)

# Set entry point
workflow.set_entry_point("load_issues")

# Connect nodes
# After loading issues, start processing the first one
workflow.add_edge("load_issues", "process_single_issue")

# After processing an issue, save the partial result
workflow.add_edge("process_single_issue", "is_all_issues_resolved")

# After saving, check if we should continue or finish
workflow.add_conditional_edges(
    "is_all_issues_resolved",
    should_continue,
    {
        "process_issue": "process_single_issue",  # Loop back to process next issue
        "save_final": "save_final_results"        # Move to final results
    }
)

workflow.add_edge("save_final_results", END)

graph = workflow.compile()


import asyncio
import json
from pathlib import Path
from datetime import datetime
from src.multi_issue.multi_issue_state import MultiIssueState

async def save_final_results(state: MultiIssueState) -> dict:
    issue_results = state.get("issue_results", [])
    
    if not issue_results:
        print("No results to save")
        return {}
    
    output_dir = Path(__file__).parent.parent.parent.parent / "dataset" / "issue_verdicts"
    await asyncio.to_thread(output_dir.mkdir, parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"all_issues_final_{timestamp}.json"
    filepath = output_dir / filename
    
    total = len(issue_results)
    solved = sum(1 for r in issue_results if r.get("solved", False))
    with_documents = sum(1 for r in issue_results if r.get("documents", False))
    with_case_law = sum(1 for r in issue_results if r.get("case_law", False))
    
    final_output = {
        "metadata": {
            "timestamp": timestamp,
            "total_issues": total,
            "issues_solved": solved,
            "issues_with_documents": with_documents,
            "issues_with_case_law": with_case_law,
            "solve_rate": f"{(solved/total*100):.1f}%" if total > 0 else "N/A"
        },
        "results": [
            {
                "issue_index": result["issue_index"],
                "date_event": result["issue"].get("date_event", ""),
                "legal_issue": result["issue"].get("legal_issue", ""),
                "recommendation": result["recommendation"],
                "suggestion": result["suggestion"],
                "solved": result["solved"],
                "documents": result["documents"],
                "case_law": result["case_law"],
                "keywords": result["keywords"],
                "focus_area": result["focus_area"],
                "micro_verdicts_count": len(result.get("micro_verdicts", [])),
                "full_issue": result["issue"]
            }
            for result in issue_results
        ]
    }
    
    
    def _write() -> None:
        with open(filepath, "w") as f:
            json.dump(final_output, indent=2, fp=f)

    await asyncio.to_thread(_write)
    
    return {}


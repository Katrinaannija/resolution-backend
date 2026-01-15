import asyncio
import json
from pathlib import Path
from src.documents.documents_state import DocumentsState

async def save_documents_result(state: DocumentsState) -> dict:
    """Save the final documents workflow result to disk."""
    
    # Create output directory
    output_dir = Path(__file__).parent.parent.parent.parent / "dataset" / "documents_verdicts"
    await asyncio.to_thread(output_dir.mkdir, parents=True, exist_ok=True)
    
    # Get issue index
    issue_idx = state.get("issue_index", 0)
    filename = f"issue_{issue_idx}.json"
    filepath = output_dir / filename
    
    # Prepare result to save
    result_to_save = {
        "issue_index": issue_idx,
        "date_event": state["issue"].get("date_event", ""),
        "legal_issue": state["issue"].get("legal_issue", ""),
        "recommendation": state.get("final_recommendation", ""),
        "suggestion": state.get("final_suggestion", ""),
        "solved": state.get("solved", False),
        "documents": state.get("documents", False),
        "case_law": state.get("case_law", False),
        "micro_verdicts": state.get("micro_verdicts", []),
        "full_issue": state["issue"]
    }
    
    def _write() -> None:
        with open(filepath, "w") as f:
            json.dump(result_to_save, indent=2, fp=f)

    await asyncio.to_thread(_write)
    
    print(f"✓ Saved documents result to: {filepath}")
    
    return {}


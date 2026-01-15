import asyncio
import json
from pathlib import Path
from datetime import datetime
from src.case_law.case_law_state import CaseLawState

async def save_result(state: CaseLawState) -> dict:
    """Save the final case law workflow result to disk."""
    
    # Create output directory
    output_dir = Path(__file__).parent.parent.parent.parent / "dataset" / "issue_verdicts"
    await asyncio.to_thread(output_dir.mkdir, parents=True, exist_ok=True)
    
    # Get issue index and timestamp
    issue_idx = state.get("issue_index", 0)
    filename = f"issue_{issue_idx}.json"
    filepath = output_dir / filename
    
    # Prepare result to save
    result_to_save = {
        "issue_index": issue_idx,
        "date_event": state["issue"].get("date_event", ""),
        "legal_issue": state["issue"].get("legal_issue", ""),
        "recommendation": state.get("recommendation", ""),
        "suggestion": state.get("suggestion", ""),
        "solved": state.get("solved", False),
        "documents": state.get("documents", False),
        "case_law": state.get("case_law", False),
        "keywords": state.get("keywords", []),
        "focus_area": state.get("focus_area", ""),
        "micro_verdicts": state.get("micro_verdicts", []),
        "full_issue": state["issue"]
    }
    
    def _write() -> None:
        with open(filepath, "w") as f:
            json.dump(result_to_save, indent=2, fp=f)

    await asyncio.to_thread(_write)
    
    print(f"✓ Saved case law result to: {filepath}")
    
    return {}


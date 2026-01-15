from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.judgement.judgement_state import JudgementState


def save_judgement(state: JudgementState) -> JudgementState:
    """Persist the judgement output for auditing."""
    output_dir = Path(__file__).resolve().parents[3] / "dataset" / "judgements"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"judgement_{timestamp}.json"
    payload = {
        "judgement": state["judgement"],
        "issues_table": state["issues_table"],
    }

    with path.open("w") as fp:
        json.dump(payload, fp, indent=2)

    print(f"✓ Saved judgement memo to {path}")
    return state


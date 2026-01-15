from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

from src.judgement.judgement_state import JudgementState


async def save_judgement(state: JudgementState) -> JudgementState:
    """Persist the judgement output for auditing."""
    output_dir = Path(__file__).resolve().parents[3] / "dataset" / "judgements"
    await asyncio.to_thread(output_dir.mkdir, parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"judgement_{timestamp}.json"
    payload = {
        "judgement": state["judgement"],
        "issues_table": state["issues_table"],
    }

    def _write() -> None:
        with path.open("w") as fp:
            json.dump(payload, fp, indent=2)

    await asyncio.to_thread(_write)

    print(f"✓ Saved judgement memo to {path}")
    return state


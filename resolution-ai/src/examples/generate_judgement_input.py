#!/usr/bin/env python3
"""
Generate input JSON for the judgement workflow from orchestrator_state files.

Usage:
    python -m src.examples.generate_judgement_input

This script reads:
- All issue_*.json files from dataset/orchestrator_state/
- Statement of Claim from dataset/documents/O - Statement of Claim.md
- Statement of Defence from dataset/documents/P - Statement of Defence.md

And outputs a single JSON file that can be used as input to the judgement workflow.
"""

from __future__ import annotations

import json
from pathlib import Path


def main():
    project_root = Path(__file__).resolve().parents[2]
    
    orchestrator_state_dir = project_root / "dataset" / "orchestrator_state"
    documents_dir = project_root / "dataset" / "documents"
    output_path = project_root / "dataset" / "judgement_input.json"
    
    # Load all issue state files
    issue_files = sorted(orchestrator_state_dir.glob("issue_*.json"))
    if not issue_files:
        print(f"No issue files found in {orchestrator_state_dir}")
        return
    
    print(f"Found {len(issue_files)} issue files:")
    issues = []
    for issue_file in issue_files:
        print(f"  - {issue_file.name}")
        with issue_file.open("r", encoding="utf-8") as f:
            issue_data = json.load(f)
        issues.append(issue_data)
    
    # Sort by issue_index to ensure correct order
    issues.sort(key=lambda x: x.get("issue_index", 0))
    
    # Load statement of claim
    statement_of_claim_path = documents_dir / "O - Statement of Claim.md"
    if statement_of_claim_path.exists():
        statement_of_claim = statement_of_claim_path.read_text(encoding="utf-8")
        print(f"Loaded statement of claim: {len(statement_of_claim)} chars")
    else:
        statement_of_claim = ""
        print(f"Warning: Statement of claim not found at {statement_of_claim_path}")
    
    # Load statement of defence
    statement_of_defence_path = documents_dir / "P - Statement of Defence.md"
    if statement_of_defence_path.exists():
        statement_of_defence = statement_of_defence_path.read_text(encoding="utf-8")
        print(f"Loaded statement of defence: {len(statement_of_defence)} chars")
    else:
        statement_of_defence = ""
        print(f"Warning: Statement of defence not found at {statement_of_defence_path}")
    
    # Build the judgement input
    judgement_input = {
        "issues": issues,
        "statement_of_claim": statement_of_claim,
        "statement_of_defence": statement_of_defence,
    }
    
    # Write output
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(judgement_input, f, indent=2, ensure_ascii=False)
    
    print(f"\nGenerated judgement input at: {output_path}")
    print(f"  - {len(issues)} issues")
    print(f"  - Statement of claim: {len(statement_of_claim)} chars")
    print(f"  - Statement of defence: {len(statement_of_defence)} chars")


if __name__ == "__main__":
    main()



from __future__ import annotations

import json

from src.orchestrator.deep_agent import CourtIssueDeepAgent


def main() -> None:
    """
    Minimal smoke test for the orchestrator deep agent.

    Runs the agent using local prompts and prints a compact summary.
    """
    agent = CourtIssueDeepAgent()
    result = agent.run()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

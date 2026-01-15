from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
import os
import shutil
from pathlib import Path
from typing import Dict, List, Literal, Optional, TypedDict, cast

from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph import END, StateGraph

from src.case_law.case_law_state import CaseLawState
from src.case_law_workflow import graph as case_law_graph
from src.documents.documents_state import DocumentsState
from src.documents_workflow import graph as documents_graph
from src.judgement.judgement_state import JudgementState
from src.judgement_workflow import graph as judgement_graph
from src.utils.pull_prompt import pull_prompt_async

from src.orchestrator.orchestrator_state import IssueWorkState
from src.orchestrator.storage import (
    create_fresh_issue_state,
    load_issue_state,
    save_issue_state,
)

DEFAULT_ISSUES_PATH = (
    Path(__file__).resolve().parents[2] / "dataset" / "court_issues" / "court_issues.json"
)

MAX_CASE_LAW_RUNS = 2
MAX_DOCUMENT_RUNS = 2

DEFAULT_STATEMENT_OF_CLAIM_PATH = (
    Path(__file__).resolve().parents[2] / "dataset" / "documents" / "O - Statement of Claim.md"
)

DEFAULT_STATEMENT_OF_DEFENCE_PATH = (
    Path(__file__).resolve().parents[2] / "dataset" / "documents" / "P - Statement of Defence.md"
)

DEFAULT_AGENT_EVENTS_PATH = (
    Path(__file__).resolve().parents[2] / "dataset" / "agent" / "events" / "events.jsonl"
)


class CourtIssueDeepAgent:
    """
    Minimal deep agent harness that routes issues across the case-law,
    documents, and judgement workflows while persisting intermediate state.
    """

    def __init__(
        self,
        issues_path: str | Path | None = None,
        statement_of_claim_path: str | Path | None = None,
        statement_of_defence_path: str | Path | None = None,
        events_path: str | Path | None = None,
    ):
        self.issues_path = Path(issues_path) if issues_path else DEFAULT_ISSUES_PATH
        self.statement_of_claim_path = (
            Path(statement_of_claim_path)
            if statement_of_claim_path
            else DEFAULT_STATEMENT_OF_CLAIM_PATH
        )
        self.statement_of_defence_path = (
            Path(statement_of_defence_path)
            if statement_of_defence_path
            else DEFAULT_STATEMENT_OF_DEFENCE_PATH
        )
        self.events_path = Path(events_path) if events_path else DEFAULT_AGENT_EVENTS_PATH
        self._router_prompt_name = "orchestrator_issue_router"
        self.router_prompt: Optional[Runnable] = None
        self._event_log_lock: Optional[asyncio.Lock] = None
        self._soc_agent_ran = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> Dict[str, object]:
        return asyncio.run(self._run_impl_async())

    async def run_async(self) -> Dict[str, object]:
        return await self._run_impl_async()

    async def _run_impl_async(self) -> Dict[str, object]:
        await self._ensure_soc_agent_prerequisite_async()
        await self._ensure_router_prompt_async()
        issues = self._load_issues()

        # Process all issues in parallel
        print(f"[orchestrator] Starting parallel processing of {len(issues)} issues")
        tasks = [
            self._process_single_issue_async(issue, idx)
            for idx, issue in enumerate(issues)
        ]
        resolved = await asyncio.gather(*tasks)

        # Verify all issues have been attempted before calling judgement
        all_issues_attempted = all(
            self._is_issue_attempted(issue_state) for issue_state in resolved
        )
        if not all_issues_attempted:
            pending = [
                i for i, s in enumerate(resolved) if not self._is_issue_attempted(s)
            ]
            print(f"[orchestrator] WARNING: Issues {pending} not fully attempted, proceeding to judgement anyway")

        print(f"[orchestrator] All {len(resolved)} issues processed, invoking judgement")
        judgement = await self._invoke_judgement_async(resolved)
        return {"issues": resolved, "judgement": judgement}

    async def _process_single_issue_async(
        self, issue: Dict[str, object], idx: int
    ) -> IssueWorkState:
        """Process a single issue through case_law and documents workflows."""
        issue_state = self._load_or_initialize_issue(issue, idx)
        print(f"[orchestrator] Working on issue #{idx}: {issue['legal_issue']}")

        # Skip already solved issues
        if issue_state["solved"]:
            print(f"[orchestrator] Issue #{idx} already solved, skipping")
            return issue_state

        while not self._is_issue_done(issue_state):
            # Check run limits
            case_law_run_count = len(issue_state.get("case_law_runs", []))
            document_run_count = len(issue_state.get("document_runs", []))

            if case_law_run_count >= MAX_CASE_LAW_RUNS and document_run_count >= MAX_DOCUMENT_RUNS:
                print(f"[orchestrator] Issue #{idx} reached max runs (case_law: {case_law_run_count}, documents: {document_run_count}), finalizing")
                issue_state["solved"] = True
                break

            action = await self._decide_next_action_async(issue_state)
            print(f"[orchestrator] Issue #{idx} next action: {action}")

            # Enforce run limits on specific actions
            # Note: Using separate `if` blocks (not elif) so we can re-check after redirection
            if action == "case_law" and case_law_run_count >= MAX_CASE_LAW_RUNS:
                print(f"[orchestrator] Issue #{idx} case law runs exhausted ({case_law_run_count}/{MAX_CASE_LAW_RUNS}), trying documents")
                action = "documents" if document_run_count < MAX_DOCUMENT_RUNS else "finalize"

            if action == "documents" and document_run_count >= MAX_DOCUMENT_RUNS:
                print(f"[orchestrator] Issue #{idx} document runs exhausted ({document_run_count}/{MAX_DOCUMENT_RUNS}), trying case_law")
                action = "case_law" if case_law_run_count < MAX_CASE_LAW_RUNS else "finalize"

            if action == "case_law":
                issue_state = await self._run_case_law_async(issue_state)
            elif action == "documents":
                issue_state = await self._run_documents_async(issue_state)
            else:
                issue_state["solved"] = True
                break

            save_issue_state(issue_state)

            # If both workflows say no further work is needed, break early.
            if self._can_finalize(issue_state):
                issue_state["solved"] = True
                break

        save_issue_state(issue_state)
        print(f"[orchestrator] Issue #{idx} {'solved' if issue_state['solved'] else 'pending'}")
        return issue_state

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _ensure_soc_agent_prerequisite_async(self) -> None:
        """
        Ensure the Statement of Claim (SOC) agent runs before orchestrator work begins.
        """
        if self._soc_agent_ran:
            return

        print("[orchestrator] Running SOC agent prerequisite to generate court issues")
        try:
            from src.soc_agent import run_soc_agent_async
        except ImportError as exc:  # pragma: no cover - defensive runtime guard
            raise RuntimeError("Failed to import SOC agent prerequisites") from exc

        await run_soc_agent_async()

        if not DEFAULT_ISSUES_PATH.exists():
            raise FileNotFoundError(
                f"SOC agent completed but did not produce {DEFAULT_ISSUES_PATH}"
            )

        if self.issues_path != DEFAULT_ISSUES_PATH:
            self.issues_path.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(
                shutil.copy2,
                DEFAULT_ISSUES_PATH,
                self.issues_path,
            )

        self._soc_agent_ran = True

    def _load_issues(self) -> List[Dict[str, object]]:
        if not self.issues_path.exists():
            raise FileNotFoundError(
                f"Court issues file not found at {self.issues_path}. "
                "The SOC agent prerequisite should generate this file automatically; verify the soc_agent run succeeded."
            )
        with self.issues_path.open() as fp:
            payload = json.load(fp)
        return payload["events"]

    def _load_or_initialize_issue(
        self, issue: Dict[str, object], issue_index: int
    ) -> IssueWorkState:
        persisted = load_issue_state(issue_index)
        if persisted is not None:
            return persisted
        return create_fresh_issue_state(issue, issue_index)

    async def _decide_next_action_async(self, state: IssueWorkState) -> Literal[
        "case_law", "documents", "finalize"
    ]:
        if self.router_prompt is None:
            raise RuntimeError("Router prompt not initialized")
        s = state
        result = await self.router_prompt.ainvoke(
            {
                "issue_index": s["issue_index"],
                "legal_issue": s["issue"]["legal_issue"],
                "solved": s["solved"],
                "requires_documents": s["requires_documents"],
                "requires_case_law": s["requires_case_law"],
                "case_law": s["case_law"],
                "documents": s["documents"],
                "seen_keywords": ", ".join(s["seen_keywords"]) if s["seen_keywords"] else "None",
                "recommendation": s["recommendation"],
                "suggestion": s["suggestion"],
            }
        )
        return result["next_action"]

    async def _run_case_law_async(self, state: IssueWorkState) -> IssueWorkState:
        rec = state["recommendation"] if "recommendation" in state else ""
        sug = state["suggestion"] if "suggestion" in state else ""
        seen = set(state["seen_keywords"]) if "seen_keywords" in state else set()
        case_state: CaseLawState = {
            "issue_index": state["issue_index"],
            "issue": state["issue"],
            "recommendation": rec,
            "suggestion": sug,
            "seen_keywords": seen,
        }
        result = await case_law_graph.ainvoke(case_state)

        state["recommendation"] = result["recommendation"]
        state["suggestion"] = result["suggestion"]
        state["solved"] = result["solved"]
        state["documents"] = result["documents"]
        state["case_law"] = result["case_law"]
        state["requires_case_law"] = state["case_law"]
        state["requires_documents"] = result["documents"]
        seen_keywords = result["seen_keywords"]
        if isinstance(seen_keywords, set):
            seen_keywords = sorted(seen_keywords)
        state["seen_keywords"] = seen_keywords

        run_history = list(state["case_law_runs"]) if "case_law_runs" in state else []
        run_history.append(
            {
                "name": "case_law",
                "recommendation": state["recommendation"],
                "suggestion": state["suggestion"],
                "solved": state["solved"],
                "documents": state["documents"],
                "case_law": state["case_law"],
            }
        )
        state["case_law_runs"] = run_history
        await self._log_pipeline_event_async("case_law", state)
        return state

    async def _run_documents_async(self, state: IssueWorkState) -> IssueWorkState:
        rec = state["recommendation"] if "recommendation" in state else ""
        sug = state["suggestion"] if "suggestion" in state else ""
        documents_state: DocumentsState = {
            "issue_index": state["issue_index"],
            "issue": state["issue"],
            "recommendation": rec,
            "suggestion": sug,
        }
        result = await documents_graph.ainvoke(documents_state)

        state["recommendation"] = result["final_recommendation"]
        state["suggestion"] = result["final_suggestion"]
        state["solved"] = result["solved"]
        state["documents"] = result["documents"]
        state["case_law"] = result["case_law"]
        state["requires_documents"] = state["documents"]
        state["requires_case_law"] = result["case_law"]

        run_history = list(state["document_runs"]) if "document_runs" in state else []
        run_history.append(
            {
                "name": "documents",
                "recommendation": state["recommendation"],
                "suggestion": state["suggestion"],
                "solved": state["solved"],
                "documents": state["documents"],
                "case_law": state["case_law"],
            }
        )
        state["document_runs"] = run_history
        await self._log_pipeline_event_async("document", state)
        return state

    async def _invoke_judgement_async(self, issues: List[IssueWorkState]) -> Dict[str, str]:
        statement_of_claim = self._load_document(self.statement_of_claim_path)
        statement_of_defence = self._load_document(self.statement_of_defence_path)

        judgement_state: JudgementState = {
            "issues": issues,
            "statement_of_claim": statement_of_claim,
            "statement_of_defence": statement_of_defence,
        }
        result = await judgement_graph.ainvoke(judgement_state)
        await self._append_event_async(
            {
                "type": "judgement",
                "date": self._current_timestamp(),
                "judgement": result,
            }
        )
        return result

    def _load_document(self, path: Path) -> str:
        """Load document content from a file path."""
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def _current_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    async def _log_pipeline_event_async(
        self, event_type: Literal["case_law", "document"], state: IssueWorkState
    ) -> None:
        iteration = len(state.get("case_law_runs", [])) + len(
            state.get("document_runs", [])
        )
        issue = state.get("issue") or {}
        await self._append_event_async(
            {
                "type": event_type,
                "date": self._current_timestamp(),
                "recommendation": state.get("recommendation"),
                "suggestion": state.get("suggestion"),
                "solved": state.get("solved"),
                "iteration": iteration,
                "issue_id": state.get("issue_index"),
                "legal_issue": issue.get("legal_issue") if isinstance(issue, dict) else None,
            }
        )

    async def _append_event_async(self, payload: Dict[str, object]) -> None:
        if self._event_log_lock is None:
            self._event_log_lock = asyncio.Lock()
        entry = dict(payload)
        entry.setdefault("date", self._current_timestamp())
        async with self._event_log_lock:
            await asyncio.to_thread(self._write_event_entry, entry)

    def _write_event_entry(self, entry: Dict[str, object]) -> None:
        """Write a single event payload to disk (runs in a worker thread)."""
        events_dir = self.events_path.parent
        events_dir.mkdir(parents=True, exist_ok=True)
        json_line = json.dumps(entry, default=str) + "\n"
        with self.events_path.open("a", encoding="utf-8") as fp:
            fp.write(json_line)
            fp.flush()
            os.fsync(fp.fileno())

    def _is_issue_done(self, state: IssueWorkState) -> bool:
        return bool(state["solved"]) and self._can_finalize(state)

    def _can_finalize(self, state: IssueWorkState) -> bool:
        return not state["documents"] and not state["case_law"]

    def _is_issue_attempted(self, state: IssueWorkState) -> bool:
        """Check if issue is either solved or has exhausted all attempts."""
        if state["solved"]:
            return True
        case_law_runs = len(state.get("case_law_runs", []))
        document_runs = len(state.get("document_runs", []))
        return case_law_runs >= MAX_CASE_LAW_RUNS and document_runs >= MAX_DOCUMENT_RUNS

    async def _ensure_router_prompt_async(self) -> None:
        if self.router_prompt is None:
            self.router_prompt = await pull_prompt_async(
                self._router_prompt_name,
                include_model=True,
            )


def orchestrator_deep_agent_factory(config: RunnableConfig) -> Runnable:
    """LangGraph runtime factory that wraps the imperative agent in a Runnable graph."""
    configurable: Dict[str, object] = {}
    if config and hasattr(config, "get"):
        cf = config.get("configurable", None)
        if cf is not None:
            configurable = cf
    issues_path_val = configurable.get("issues_path")
    statement_of_claim_path_val = configurable.get("statement_of_claim_path")
    statement_of_defence_path_val = configurable.get("statement_of_defence_path")
    events_path_val = configurable.get("events_path")

    agent = CourtIssueDeepAgent(
        issues_path=issues_path_val,
        statement_of_claim_path=statement_of_claim_path_val,
        statement_of_defence_path=statement_of_defence_path_val,
        events_path=events_path_val,
    )
    return _build_orchestrator_graph(agent)


class OrchestratorGraphState(TypedDict, total=False):
    issues: List[IssueWorkState]
    judgement: Dict[str, str]


def _build_orchestrator_graph(agent: CourtIssueDeepAgent):
    workflow = StateGraph(OrchestratorGraphState)

    async def run_agent(_: OrchestratorGraphState) -> OrchestratorGraphState:
        result = await agent.run_async()
        return cast(OrchestratorGraphState, result)

    workflow.add_node("run_agent", run_agent)
    workflow.set_entry_point("run_agent")
    workflow.add_edge("run_agent", END)
    return workflow.compile()


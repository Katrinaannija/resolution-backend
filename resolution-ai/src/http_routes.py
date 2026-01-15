"""
Custom HTTP routes for LangGraph Cloud deployment.
Exposes /events endpoint to serve events.jsonl as JSON.
Provides endpoints to start/stop/status the orchestrator deep agent.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import signal
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.orchestrator.deep_agent import CourtIssueDeepAgent

# Path to events file (relative to project root)
EVENTS_FILE = Path(__file__).parent.parent / "dataset" / "agent" / "events" / "events.jsonl"
# Path to agent state file (file-based state for cross-process tracking)
STATE_FILE = Path(__file__).parent.parent / "dataset" / "agent" / "agent_state.json"
# Path to orchestrator state directory
ORCHESTRATOR_STATE_DIR = Path(__file__).parent.parent / "dataset" / "orchestrator_state"

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://alien-lex-synth.lovable.app",
        "https://eu.smith.langchain.com",
        "https://smith.langchain.com",
        "http://localhost:2024",
        "http://127.0.0.1:2024",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# File-based Agent State Tracking (persists across processes)
# ---------------------------------------------------------------------------
def _load_agent_state_sync() -> Dict[str, Any]:
    """Load agent state from file (sync version for thread)."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, IOError):
            pass
    return {"status": "idle", "pid": None, "error": None}


def _save_agent_state_sync(status: str, pid: Optional[int] = None, error: Optional[str] = None):
    """Save agent state to file (sync version for thread)."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({
        "status": status,
        "pid": pid,
        "error": error,
    }))


async def load_agent_state() -> Dict[str, Any]:
    """Load agent state from file (async)."""
    return await asyncio.to_thread(_load_agent_state_sync)


async def save_agent_state(status: str, pid: Optional[int] = None, error: Optional[str] = None):
    """Save agent state to file (async)."""
    await asyncio.to_thread(_save_agent_state_sync, status, pid, error)


def is_process_running(pid: int) -> bool:
    """Check if a process with the given PID is still running."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


# In-memory task reference (for same-process cancellation)
_agent_task: Optional[asyncio.Task] = None


# ---------------------------------------------------------------------------
# Events Endpoint
# ---------------------------------------------------------------------------
def _load_events_from_jsonl_sync() -> List[Dict[str, Any]]:
    """Load events from JSONL file (sync version for thread)."""
    events = []
    if EVENTS_FILE.exists():
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        event = json.loads(line)
                        events.append(event)
                    except json.JSONDecodeError:
                        continue
    return events


def _clear_events_file_sync():
    """Clear events file (sync version for thread)."""
    if EVENTS_FILE.exists():
        EVENTS_FILE.write_text("")


def _clear_orchestrator_state_sync():
    """Delete orchestrator state directory (sync version for thread)."""
    if ORCHESTRATOR_STATE_DIR.exists():
        shutil.rmtree(ORCHESTRATOR_STATE_DIR)


@app.get("/events")
async def get_events():
    """Return all events from the events.jsonl file."""
    return await asyncio.to_thread(_load_events_from_jsonl_sync)


# ---------------------------------------------------------------------------
# Agent Control Endpoints
# ---------------------------------------------------------------------------
@app.post("/agent/start")
async def start_agent():
    """Start the orchestrator deep agent in the background."""
    global _agent_task

    state = await load_agent_state()

    # Check if already running (verify process is actually alive)
    if state["status"] == "running" and state["pid"]:
        if is_process_running(state["pid"]):
            raise HTTPException(status_code=409, detail="Agent is already running")
        # Process died but state wasn't updated - clean up
        await save_agent_state("idle")

    # Clear events file and orchestrator state for fresh run
    await asyncio.to_thread(_clear_events_file_sync)
    await asyncio.to_thread(_clear_orchestrator_state_sync)

    # Save running state with current PID
    current_pid = os.getpid()
    await save_agent_state("running", pid=current_pid)

    async def run_agent():
        global _agent_task
        try:
            agent = CourtIssueDeepAgent()
            await agent.run_async()
            await save_agent_state("completed")
        except asyncio.CancelledError:
            await save_agent_state("stopped")
            raise
        except Exception as e:
            await save_agent_state("failed", error=str(e))
        finally:
            _agent_task = None

    _agent_task = asyncio.create_task(run_agent())

    return {"status": "started", "message": "Agent started successfully", "pid": current_pid}


@app.post("/agent/stop")
async def stop_agent():
    """Stop the currently running orchestrator agent."""
    global _agent_task

    state = await load_agent_state()

    if state["status"] != "running":
        raise HTTPException(status_code=400, detail=f"No agent is currently running (status: {state['status']})")

    stopped = False

    # Try in-memory task cancellation first (same process)
    if _agent_task is not None and not _agent_task.done():
        _agent_task.cancel()
        try:
            await _agent_task
        except asyncio.CancelledError:
            pass
        _agent_task = None
        stopped = True

    # Try killing the process if we have a PID (different process)
    if not stopped and state["pid"] and is_process_running(state["pid"]):
        try:
            os.kill(state["pid"], signal.SIGTERM)
            stopped = True
        except (OSError, ProcessLookupError):
            pass

    await save_agent_state("stopped")

    return {"status": "stopped", "message": "Agent stopped successfully"}


@app.get("/agent/status")
async def get_agent_status():
    """Get the current status of the orchestrator agent."""
    state = await load_agent_state()

    # Verify running status - check if process is actually alive
    if state["status"] == "running" and state["pid"]:
        if not is_process_running(state["pid"]):
            # Process died unexpectedly
            await save_agent_state("failed", error="Agent process died unexpectedly")
            state = await load_agent_state()

    return state

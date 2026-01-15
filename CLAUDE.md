# CLAUDE.md - AI Assistant Guide for Resolution Backend

## Project Overview

**Resolution Backend** is a LangGraph-based AI system designed for legal case analysis and resolution. The system processes legal documents, analyzes case law, and generates judicial recommendations through a multi-agent orchestration architecture.

### Core Purpose
- Analyze statements of claim and defence documents
- Search and evaluate relevant case law precedents
- Extract insights from legal documents
- Generate structured legal recommendations and draft judgements
- Provide AI-assisted legal resolution through multiple specialized workflows

## Tech Stack

### Primary Technologies
- **Python 3.11+** - Core runtime environment
- **LangGraph 0.2.0+** - Multi-agent workflow orchestration framework
- **LangChain 1.1.0+** - LLM integration and chains
- **OpenAI GPT-5.1** - Primary language model (configurable)
- **FastAPI 0.115.0+** - HTTP API server
- **Langfuse 2.0.0+** - Observability and analytics

### Development Tools
- **uv** - Fast Python package installer and resolver
- **langgraph-cli** - Development server and deployment tooling
- **python-dotenv** - Environment configuration management

### Additional Libraries
- **requests** - HTTP client for external API calls
- **beautifulsoup4** - HTML parsing for case law extraction

## Architecture

### High-Level Design

The system follows a **hierarchical multi-agent architecture**:

```
CourtIssueDeepAgent (Orchestrator)
    ├── SOC Agent (Statement of Claim Parser)
    ├── Case Law Workflow (Legal Precedent Analysis)
    ├── Documents Workflow (Evidence Analysis)
    ├── Multi-Issue Workflow (Batch Processing)
    └── Judgement Workflow (Final Decision Generation)
```

### Agent Communication Pattern

1. **Orchestrator (CourtIssueDeepAgent)** coordinates all sub-workflows
2. **Parallel Processing** - Multiple issues are processed concurrently
3. **State Persistence** - Each workflow maintains state between runs
4. **Event Streaming** - Real-time progress via JSONL event logs
5. **Iterative Refinement** - Workflows can run multiple times per issue (max 2 runs each)

## Directory Structure

```
resolution-backend/
├── src/                          # Main source code
│   ├── case_law/                 # Case law analysis workflow
│   │   ├── case_law_state.py     # State definitions
│   │   └── nodes/                # Workflow nodes
│   ├── documents/                # Document analysis workflow
│   │   ├── documents_state.py
│   │   └── nodes/
│   ├── judgement/                # Final judgement generation
│   │   ├── judgement_state.py
│   │   └── nodes/
│   ├── multi_issue/              # Multi-issue batch processing
│   │   ├── multi_issue_state.py
│   │   ├── nodes/
│   │   └── edges/                # Conditional routing logic
│   ├── orchestrator/             # Main orchestration logic
│   │   ├── deep_agent.py         # CourtIssueDeepAgent
│   │   ├── storage.py            # State persistence
│   │   └── orchestrator_state.py
│   ├── tools/                    # Shared utility tools
│   │   ├── case_law_search.py
│   │   ├── document_store.py
│   │   ├── snippet_extractor.py
│   │   └── soc_issue_table.py
│   ├── utils/                    # Helper utilities
│   ├── examples/                 # Usage examples
│   ├── soc_agent.py              # Statement of Claim agent
│   ├── cos_agent.py              # Alternative agent variant
│   ├── case_law_workflow.py      # Case law graph definition
│   ├── documents_workflow.py     # Documents graph definition
│   ├── multi_issue_workflow.py   # Multi-issue graph
│   ├── judgement_workflow.py     # Judgement graph
│   ├── demo_event_pipeline.py    # Demo/testing pipeline
│   └── http_routes.py            # FastAPI HTTP endpoints
├── dataset/                      # Data files and storage
│   ├── agent/
│   │   ├── agent_state.json      # Agent execution state
│   │   └── events/
│   │       └── events.jsonl      # Real-time event stream
│   ├── documents/                # Legal document files (.md)
│   ├── document_details/         # Document metadata
│   ├── court_issues/             # Generated court issues JSON
│   └── orchestrator_state/       # Orchestrator persistence
├── frontend-examples/            # TypeScript/React examples
│   ├── sdk/                      # Client SDK examples
│   └── package.json
├── docs/                         # HTML workflow diagrams
├── langgraph.json                # LangGraph configuration
├── pyproject.toml                # Python dependencies
└── README.md                     # Basic usage guide
```

## Key Workflows

### 1. SOC Agent (Statement of Claim)
**File**: `src/soc_agent.py`
**Purpose**: Parse legal documents and generate structured issue tables

**Tools**:
- `list_documents` - List available documents
- `retrieve_document` - Fetch document content
- `get_all_document_details` - Get document metadata
- `generate_soc_issue_table` - Create structured issues
- `write_court_issues_json` - Persist issues to disk

**Output**: `dataset/court_issues/court_issues.json`

### 2. Case Law Workflow
**File**: `src/case_law_workflow.py`
**State**: `src/case_law/case_law_state.py`
**Purpose**: Search legal precedents and analyze relevance

**Pipeline A (Keyword Search)**:
1. `initialize_state` - Set default values
2. `load_court_issue` - Load specific issue
3. `generate_keywords` - Extract search terms
4. `search_caselaw` - Query case law database
5. `fetch_case_document` - Retrieve full case text

**Pipeline B (Parallel Analysis)**:
1. `judgement_focus` - Identify key legal areas

**Join & Processing**:
1. `create_issue_guidelines` - Merge both pipelines
2. `micro_verdicts` - Generate micro-recommendations
3. `aggregate_recommendations` - Consolidate findings
4. `save_result` - Persist results

### 3. Documents Workflow
**File**: `src/documents_workflow.py`
**State**: `src/documents/documents_state.py`
**Purpose**: Analyze evidence documents for specific issues

**Sequential Pipeline**:
1. `initialize_state`
2. `generate_file_focus` - Identify relevant documents
3. `extract_document_info` - Extract key information
4. `create_micro_verdicts` - Generate document-based verdicts
5. `aggregate_documents_recommendations` - Consolidate
6. `save_documents_result` - Persist

### 4. Multi-Issue Workflow
**File**: `src/multi_issue_workflow.py`
**Purpose**: Batch process multiple court issues

**Loop Structure**:
1. `load_issues` - Load all issues
2. `process_single_issue` - Process one issue
3. `is_all_issues_resolved` - Check completion
4. Loop back or continue to `save_final_results`

### 5. Judgement Workflow
**File**: `src/judgement_workflow.py`
**Purpose**: Generate final judicial decision based on all issue analyses

**Pipeline**:
1. `initialize_state`
2. `draft_judgement` - Generate final judgement
3. `save_judgement` - Persist to disk

### 6. Orchestrator Deep Agent
**File**: `src/orchestrator/deep_agent.py`
**Class**: `CourtIssueDeepAgent`
**Purpose**: Coordinate all workflows and manage execution lifecycle

**Execution Flow**:
1. Run SOC agent to generate court issues
2. Load issues from JSON
3. Process all issues in parallel
4. For each issue:
   - Run case law workflow (max 2 times)
   - Run documents workflow (max 2 times)
   - Use LLM-based router to decide next action
5. Aggregate all issue resolutions
6. Generate final judgement
7. Stream events to `events.jsonl`

**Key Configuration**:
- `MAX_CASE_LAW_RUNS = 2`
- `MAX_DOCUMENT_RUNS = 2`
- Router prompt: `orchestrator_issue_router` (local prompt in `src/utils/prompts.py`)

## State Management

### State Persistence Strategy

1. **Issue State**: Stored in `dataset/orchestrator_state/issue_{index}.json`
2. **Agent State**: Stored in `dataset/agent/agent_state.json`
3. **Event Log**: Appended to `dataset/agent/events/events.jsonl`
4. **Results**: Saved to workflow-specific output files

### State Types

**CaseLawState** (TypedDict):
```python
{
    "issue_index": int,
    "issue": Issue,
    "recommendation": str,
    "suggestion": str,
    "seen_keywords": set[str],
    "keywords": List[str],
    "cases": List[dict],
    "fetched_case_documents": List[str],
    "focus_area": str,
    "issue_guidelines": List[str],
    "micro_verdicts": List[dict],
    "solved": bool,
    "documents": bool,
    "case_law": bool,
    "output_text": str
}
```

**DocumentsState** (Similar structure adapted for document analysis)

**IssueWorkState** (Orchestrator):
```python
{
    "issue_index": int,
    "issue": Issue,
    "solved": bool,
    "requires_documents": bool,
    "requires_case_law": bool,
    "recommendation": str,
    "suggestion": str,
    "seen_keywords": List[str],
    "case_law_runs": List[dict],
    "document_runs": List[dict],
    "documents": bool,
    "case_law": bool
}
```

## HTTP API Routes

**Server**: FastAPI on `localhost:2024`
**Configuration**: `src/http_routes.py`

### Endpoints

#### `GET /events`
Returns all events from the event log.

```bash
curl http://localhost:2024/events
```

#### `POST /agent/start`
Start the orchestrator deep agent in the background.

```bash
curl -X POST http://localhost:2024/agent/start
```

**Response**:
```json
{
  "status": "started",
  "message": "Agent started successfully",
  "pid": 12345
}
```

#### `GET /agent/status`
Get current agent execution status.

```bash
curl http://localhost:2024/agent/status
```

**Response**:
```json
{
  "status": "running|idle|completed|failed|stopped",
  "pid": 12345,
  "error": "error message if failed"
}
```

#### `POST /agent/stop`
Stop the currently running agent.

```bash
curl -X POST http://localhost:2024/agent/stop
```

### CORS Configuration

Allowed origins:
- `https://alien-lex-synth.lovable.app`
- `https://eu.smith.langchain.com`
- `https://smith.langchain.com`
- `http://localhost:2024`
- `http://127.0.0.1:2024`

## Development Workflow

### Initial Setup

```bash
# Install dependencies using uv
uv sync

# Set up environment variables
cp .env.example .env  # Create if doesn't exist
# Add required keys:
# - OPENAI_API_KEY
# - GLOBAL_MODEL (optional, defaults to gpt-4o-mini)
```

### Running the Development Server

```bash
# Start LangGraph dev server
uv run langgraph dev

# Server starts on localhost:2024
```

### Testing Workflows

```bash
# Run specific examples
uv run python -m src.examples.case_law_workflow_example
uv run python -m src.examples.documents_workflow_example
uv run python -m src.examples.multi_issue_workflow_example
uv run python -m src.examples.deep_agent_orchestrator_example

# Run SOC agent directly
uv run python -m src.soc_agent
```

### Frontend Examples

```bash
cd frontend-examples
npm install

# Frontend examples connect to the local backend HTTP API
# Make sure the backend is running first (langgraph dev)

# Run pipeline with custom question
npm run run -- "How do we summarize the outstanding invoices?"

# Fetch events for a specific run
npm run events -- <runId>
```

## Key Conventions

### 1. Async-First Design

All workflow nodes should prefer async implementations:

```python
async def my_node(state: MyState) -> MyState:
    # Use async operations
    result = await some_async_operation()
    return state
```

### 2. State Immutability

Never mutate state directly. Always return new state:

```python
# Good
def update_state(state: MyState) -> MyState:
    return {**state, "new_field": "value"}

# Bad
def update_state(state: MyState) -> MyState:
    state["new_field"] = "value"  # Mutates original
    return state
```

### 3. Local Prompt Management

System prompts are stored locally in `src/utils/prompts.py`, version-controlled in the repository:

```python
from src.utils.pull_prompt import pull_prompt_async

# Pull from local registry
prompt = await pull_prompt_async("prompt_name", include_model=True)
```

**All 16 Prompts Defined in `src/utils/prompts.py`**:
- **SOC Agent**: `soc_agent_user_prompt`, `soc_system_prompt`, `soc_issue_table`
- **Orchestrator**: `orchestrator_issue_router`, `orchestrator_judgement_summary`
- **Case Law**: `case_law_keywords`, `case_law_judgement_focus`, `case_law_issue_guidelines`, `case_law_micro_verdict`, `case_law_agg_recommendations`
- **Documents**: `documents_focus_area`, `documents_extract_content`, `documents_create_micro_verdict`, `documents_agg_micro_verdicts`

**Model Configuration**:
- Default model: `gpt-4o-mini` (configurable via `GLOBAL_MODEL` environment variable)
- Prompts can be bound to models using `include_model=True` parameter

### 4. Event Logging

All major operations should log events to `events.jsonl`:

```python
await self._append_event_async({
    "type": "case_law|document|judgement",
    "date": self._current_timestamp(),
    "recommendation": state.get("recommendation"),
    "iteration": iteration,
    "issue_id": issue_index,
    "legal_issue": issue.get("legal_issue")
})
```

### 5. File Naming Conventions

- **State files**: `{workflow}_state.py`
- **Workflow graphs**: `{workflow}_workflow.py`
- **Node files**: `src/{workflow}/nodes/{node_name}.py`
- **Tools**: `src/tools/{tool_name}.py`
- **Examples**: `src/examples/{workflow}_example.py`

### 6. Graph Definition Pattern

All workflows follow this pattern:

```python
from langgraph.graph import StateGraph, END
from .state import MyState
from .nodes import node1, node2

workflow = StateGraph(MyState)

# Add nodes
workflow.add_node("node1", node1)
workflow.add_node("node2", node2)

# Set entry point
workflow.set_entry_point("node1")

# Add edges
workflow.add_edge("node1", "node2")
workflow.add_edge("node2", END)

# Compile
graph = workflow.compile()
```

### 7. Tool Definition

Tools should be defined with proper type hints and docstrings:

```python
from langchain.tools import tool

@tool
def my_tool(arg: str) -> str:
    """
    Clear description of what the tool does.

    Args:
        arg: Description of the argument

    Returns:
        Description of the return value
    """
    return result
```

### 8. Error Handling

Use try-except with fallbacks for external operations:

```python
try:
    result = await external_api_call()
except Exception as e:
    # Log error
    print(f"[workflow] Error: {e}")
    # Use fallback or default
    result = default_value
```

## Data Flow

### Complete Execution Flow

```
1. HTTP Request → POST /agent/start
2. Clear events.jsonl and orchestrator state
3. Run SOC Agent
   ├── Load documents from dataset/documents/
   ├── Parse statement of claim & defence
   └── Generate court_issues.json
4. Load court issues
5. For each issue (parallel):
   ├── Check if already solved (from state)
   ├── Decide action (LLM router):
   │   ├── case_law → Run Case Law Workflow
   │   ├── documents → Run Documents Workflow
   │   └── finalize → Mark as solved
   ├── Save issue state after each run
   └── Log event to events.jsonl
6. Aggregate all issue results
7. Run Judgement Workflow
   ├── Load all issue recommendations
   ├── Load statement of claim & defence
   └── Generate final judgement
8. Log final judgement event
9. Update agent state to "completed"
10. Return results
```

### Event Stream Format

Events are logged as JSONL (JSON Lines):

```jsonl
{"type": "case_law", "date": "2026-01-15T10:30:00Z", "recommendation": "...", "iteration": 1, "issue_id": 0, "legal_issue": "..."}
{"type": "document", "date": "2026-01-15T10:35:00Z", "recommendation": "...", "iteration": 2, "issue_id": 0, "legal_issue": "..."}
{"type": "judgement", "date": "2026-01-15T10:40:00Z", "judgement": {...}}
```

## Important Configuration Files

### langgraph.json

Defines LangGraph server configuration:

```json
{
  "dependencies": ["."],
  "graphs": {
    "soc_agent": "./src/soc_agent.py:agent",
    "case_law_resolver": "./src/case_law_workflow.py:graph",
    "docs_resolver": "./src/documents_workflow.py:graph",
    "multi_issue_resolver_agent": "./src/multi_issue_workflow.py:graph",
    "judgement_workflow": "./src/judgement_workflow.py:graph",
    "orchestrator_deep_agent": "./src/orchestrator/deep_agent.py:orchestrator_deep_agent_factory",
    "demo_event_pipeline": "./src/demo_event_pipeline.py:graph"
  },
  "http": {
    "app": "./src/http_routes.py:app"
  },
  "env": ".env"
}
```

### pyproject.toml

Python project configuration:

- **Project name**: `resolution-ai`
- **Python version**: `>=3.11`
- **Key dependencies**: See Tech Stack section

## Testing & Deployment

### Local Testing

```bash
# Run dev server
uv run langgraph dev

# Test endpoints
curl http://localhost:2024/agent/status
curl -X POST http://localhost:2024/agent/start
curl http://localhost:2024/events
```

### Observability

**Langfuse Integration**:
- LLM call tracing and analytics
- Event tracking and monitoring
- Performance metrics

**Event Streaming**:
- Real-time event logging to `dataset/agent/events/events.jsonl`
- JSONL format for easy parsing and streaming

### Debugging Tips

1. **Check event log**: `dataset/agent/events/events.jsonl`
2. **Check issue state**: `dataset/orchestrator_state/issue_{index}.json`
3. **Check agent state**: `dataset/agent/agent_state.json`
4. **Langfuse traces**: View in Langfuse dashboard
5. **Server logs**: Console output from `langgraph dev`

## Common Pitfalls

### 1. State Serialization Issues

**Problem**: Sets and complex objects can't serialize to JSON.

**Solution**: Convert sets to lists before saving:
```python
if isinstance(seen_keywords, set):
    seen_keywords = sorted(seen_keywords)
state["seen_keywords"] = seen_keywords
```

### 2. Async Context Issues

**Problem**: Mixing sync and async operations.

**Solution**: Use `asyncio.to_thread` for sync operations in async context:
```python
await asyncio.to_thread(sync_function, args)
```

### 3. Missing Environment Variables

**Problem**: OpenAI API key not set.

**Solution**: Ensure `.env` file exists with:
```bash
OPENAI_API_KEY=sk-...
GLOBAL_MODEL=gpt-4o-mini  # Optional, this is the default
```

### 4. Stale State

**Problem**: Old state files causing unexpected behavior.

**Solution**: Clear state directories:
```bash
rm -rf dataset/orchestrator_state/*
rm dataset/agent/agent_state.json
rm dataset/agent/events/events.jsonl
```

### 5. Prompt Not Found

**Problem**: Local prompt doesn't exist in registry.

**Solution**: Ensure the prompt name exists in `src/utils/prompts.py` PROMPT_REGISTRY:
```python
# All prompts are defined in src/utils/prompts.py
# Check the PROMPT_REGISTRY dictionary for available prompt names
from src.utils.prompts import PROMPT_REGISTRY
print(PROMPT_REGISTRY.keys())  # View all available prompts
```

## AI Assistant Guidelines

When working with this codebase:

1. **Understand the workflow graph** before making changes to node logic
2. **Preserve state immutability** - always return new state objects
3. **Use async/await consistently** for all I/O operations
4. **Log events** for all significant operations
5. **Test with the dev server** (`langgraph dev`) before proposing changes
6. **Edit prompts in `src/utils/prompts.py`** - all prompts are version-controlled locally
7. **Maintain backward compatibility** with existing state formats
8. **Document new nodes** with clear docstrings
9. **Follow the established patterns** for new workflows
10. **Consider parallel execution** when processing multiple issues

## Additional Resources

- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **LangChain**: https://python.langchain.com/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Langfuse**: https://langfuse.com/

## Version Information

- **Last Updated**: 2026-01-15
- **Python**: 3.11+
- **LangGraph**: 0.2.0+
- **Model**: GPT-5.1 (configurable)

---

**Note**: This document should be updated whenever significant architectural changes are made to the system.

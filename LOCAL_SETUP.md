# Local Development Setup Guide

## Quick Start (5 minutes)

### 1. Prerequisites Check

You already have:
- ✅ Python 3.11+ installed
- ✅ `uv` package manager installed
- ✅ Git configured
- ✅ Test documents in `dataset/documents/`

### 2. Environment Setup

Create your `.env` file:

```bash
# Copy the example file
cp .env.example .env

# Edit with your API key
# Replace sk-your-key-here with your actual OpenAI API key
```

Your `.env` should look like:
```bash
OPENAI_API_KEY=sk-proj-...your-actual-key...
GLOBAL_MODEL=gpt-4o-mini
```

### 3. Install Dependencies

```bash
# Install all Python dependencies
uv sync
```

This will:
- Create a virtual environment in `.venv/`
- Install all packages from `pyproject.toml`
- Lock versions in `uv.lock`

### 4. Start the Development Server

```bash
# Start the LangGraph dev server
uv run langgraph dev
```

Server will start on **http://localhost:2024**

You should see:
```
Ready!
- API: http://127.0.0.1:2024
```

### 5. Test Your Setup

Open a **new terminal** and run:

```bash
# Check server health
curl http://localhost:2024/agent/status

# Expected response:
# {"status": "idle", "pid": null}
```

✅ **You're all set!** The backend is running locally.

---

## Testing Pipelines

### Quick Test: Check Imports

```bash
# Test that all components load correctly
uv run python -c "
from src.utils.prompts import PROMPT_REGISTRY
from src.case_law_workflow import graph as case_law_graph
from src.documents_workflow import graph as docs_graph
from src.orchestrator.deep_agent import CourtIssueDeepAgent
print('✅ All imports successful')
print(f'✅ {len(PROMPT_REGISTRY)} prompts loaded')
"
```

### Full Pipeline Test

**Option 1: Via HTTP API (Recommended)**

```bash
# Start the agent
curl -X POST http://localhost:2024/agent/start

# Check status
curl http://localhost:2024/agent/status

# View real-time events
curl http://localhost:2024/events

# Stop agent
curl -X POST http://localhost:2024/agent/stop
```

**Option 2: Via Python Script**

```bash
# Run the orchestrator example
uv run python -m src.examples.deep_agent_orchestrator_example
```

**Option 3: Test Individual Workflows**

```bash
# Test SOC agent (parses legal documents)
uv run python -m src.soc_agent

# Test case law workflow
uv run python -m src.examples.case_law_workflow_example

# Test documents workflow
uv run python -m src.examples.documents_workflow_example
```

### What Happens During a Full Test?

1. **SOC Agent** parses legal documents → creates `dataset/court_issues/court_issues.json`
2. **Case Law Workflow** searches precedents for each issue
3. **Documents Workflow** analyzes evidence documents
4. **Judgement Workflow** generates final decision
5. **Events** logged to `dataset/agent/events/events.jsonl`
6. **State** saved to `dataset/orchestrator_state/issue_*.json`

---

## Git Workflow (Cursor + Claude Code)

### Current Branch

You're on: `claude/local-deployment-setup-avbaF`

### Making Changes

**In Cursor:**
1. Edit files as needed
2. Test locally: `uv run langgraph dev`
3. Stage changes: `git add .`
4. Commit: `git commit -m "Description of changes"`
5. Push: `git push -u origin claude/local-deployment-setup-avbaF`

**With Claude Code:**
- Claude Code will automatically commit and push to the correct branch
- Branch naming: Must start with `claude/` and end with session ID
- Just ask: "Commit these changes" or "Push my changes"

### Creating Pull Requests

**Via GitHub CLI (if installed):**
```bash
gh pr create --title "Your PR title" --body "Description"
```

**Via GitHub Web:**
1. Go to https://github.com/Katrinaannija/resolution-backend
2. Click "Compare & pull request"
3. Select your branch
4. Create PR

### Branch Protection

⚠️ **Important**: Push will fail (403) if:
- Branch doesn't start with `claude/`
- Branch doesn't end with matching session ID
- Network issues (will auto-retry up to 4 times)

---

## Development Workflow

### Typical Development Session

```bash
# 1. Start development server (Terminal 1)
uv run langgraph dev

# 2. Make changes in Cursor
# Edit files in src/

# 3. Test changes (Terminal 2)
curl -X POST http://localhost:2024/agent/start
curl http://localhost:2024/agent/status

# 4. View logs (Terminal 1)
# Watch console output from langgraph dev

# 5. Check results
cat dataset/agent/events/events.jsonl
cat dataset/court_issues/court_issues.json

# 6. Commit and push (when ready)
git add .
git commit -m "Your change description"
git push -u origin claude/local-deployment-setup-avbaF
```

### Hot Reload

The dev server supports hot reload for most changes:
- ✅ Changes to workflow nodes
- ✅ Changes to prompts in `src/utils/prompts.py`
- ✅ Changes to tools
- ❌ Changes to `langgraph.json` (requires restart)

---

## File Structure (What You'll Edit)

```
resolution-backend/
├── src/
│   ├── utils/prompts.py          ← Edit prompts here
│   ├── case_law_workflow.py      ← Case law graph
│   ├── documents_workflow.py     ← Documents graph
│   ├── judgement_workflow.py     ← Judgement graph
│   ├── orchestrator/
│   │   └── deep_agent.py         ← Main orchestrator
│   ├── case_law/nodes/           ← Case law logic
│   ├── documents/nodes/          ← Document analysis logic
│   └── tools/                    ← Utility tools
├── dataset/                      ← Generated data (gitignored)
│   ├── court_issues/
│   ├── orchestrator_state/
│   └── agent/events/
├── .env                          ← Your API keys (gitignored)
└── pyproject.toml                ← Dependencies
```

---

## Common Tasks

### Update Dependencies

```bash
# Add a new package
uv add package-name

# Update all packages
uv sync --upgrade

# Commit the changes
git add pyproject.toml uv.lock
git commit -m "Update dependencies"
```

### Clear State (Start Fresh)

```bash
# Remove all generated data
rm -rf dataset/orchestrator_state/*
rm -f dataset/agent/agent_state.json
rm -f dataset/agent/events/events.jsonl
rm -f dataset/court_issues/court_issues.json

# Restart dev server
# Press Ctrl+C in Terminal 1, then:
uv run langgraph dev
```

### View Logs

```bash
# Real-time events
tail -f dataset/agent/events/events.jsonl

# Pretty print last event
tail -1 dataset/agent/events/events.jsonl | python -m json.tool
```

---

## Troubleshooting

### "OpenAI API key not set"
```bash
# Check .env file exists
cat .env

# Should contain:
# OPENAI_API_KEY=sk-...
```

### "Port 2024 already in use"
```bash
# Find and kill the process
lsof -ti:2024 | xargs kill -9

# Or use a different port
uv run langgraph dev --port 3000
```

### "Module not found" errors
```bash
# Reinstall dependencies
rm -rf .venv/
uv sync
```

### Changes not reflecting
```bash
# Restart dev server
# Press Ctrl+C in terminal running langgraph dev
uv run langgraph dev
```

### Git push fails with 403
```bash
# Ensure branch name is correct
git branch

# Should start with 'claude/' and end with session ID
# If not, create correct branch:
git checkout -b claude/your-feature-name-sessionID
```

---

## Performance Tips

1. **Use cheaper models for testing**: Set `GLOBAL_MODEL=gpt-4o-mini` in `.env`
2. **Comment out workflows**: Temporarily disable workflows you're not testing
3. **Use fewer documents**: Move test documents out of `dataset/documents/` if testing one workflow
4. **Monitor costs**: Check OpenAI dashboard regularly

---

## Next Steps

1. ✅ Set up `.env` with your API key
2. ✅ Run `uv sync` to install dependencies
3. ✅ Start dev server: `uv run langgraph dev`
4. ✅ Test the API: `curl http://localhost:2024/agent/status`
5. ✅ Run a full test: `curl -X POST http://localhost:2024/agent/start`
6. 📝 Make changes in Cursor
7. 🚀 Push changes to your branch

---

## Resources

- **Full Testing Guide**: See `TESTING_AND_DEPLOYMENT.md`
- **Architecture Guide**: See `CLAUDE.md`
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **API Endpoints**: See `README.md`

---

## Questions?

- Check logs: `dataset/agent/events/events.jsonl`
- Check state: `dataset/orchestrator_state/`
- Review prompts: `src/utils/prompts.py`
- Test individual workflows: `src/examples/`

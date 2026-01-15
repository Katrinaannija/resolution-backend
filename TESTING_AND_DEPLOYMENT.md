# Testing and Deployment Guide

## 🧪 How to Test Your Code Works

### 1. Quick Smoke Test (2 minutes)

Test that all imports and prompts load correctly:

```bash
# Activate environment
cd /home/user/resolution-backend

# Test prompt loading
uv run python -c "
from src.utils.prompts import PROMPT_REGISTRY
print(f'✅ Loaded {len(PROMPT_REGISTRY)} prompts')
print('Prompts:', list(PROMPT_REGISTRY.keys()))
"

# Test pull_prompt compatibility
uv run python -c "
from src.utils.pull_prompt import pull_prompt
prompt = pull_prompt('soc_agent_user_prompt')
print('✅ pull_prompt working, type:', type(prompt).__name__)
"
```

**Expected output:**
```
✅ Loaded 14 prompts
Prompts: ['soc_agent_user_prompt', 'soc_system_prompt', ...]
✅ pull_prompt working, type: ChatPromptTemplate
```

### 2. Component Test (5 minutes)

Test individual workflow components:

```bash
# Test case law workflow
uv run python -c "
from src.case_law_workflow import graph
print('✅ Case law workflow loads')
print('Nodes:', list(graph.nodes.keys()))
"

# Test documents workflow
uv run python -c "
from src.documents_workflow import graph
print('✅ Documents workflow loads')
print('Nodes:', list(graph.nodes.keys()))
"

# Test orchestrator
uv run python -c "
from src.orchestrator.deep_agent import CourtIssueDeepAgent
print('✅ Orchestrator loads')
"
```

### 3. Development Server Test (10 minutes)

Test the full system locally:

```bash
# Set required environment variables
export OPENAI_API_KEY="sk-your-key-here"

# Optional: Override default model
export GLOBAL_MODEL="gpt-4o-mini"  # or gpt-4, gpt-3.5-turbo, etc.

# Start the development server
uv run langgraph dev

# Server starts on http://localhost:2024
```

**In another terminal, test the HTTP endpoints:**

```bash
# Check server is running
curl http://localhost:2024/health
# Expected: {"status": "ok"}

# Get current agent status
curl http://localhost:2024/agent/status
# Expected: {"status": "idle", "pid": null}

# Check events endpoint
curl http://localhost:2024/events
# Expected: [] (empty array if no runs yet)
```

### 4. Full Workflow Test (30+ minutes)

**Prerequisites:**
- Add test documents to `dataset/documents/`
- Must have at least:
  - `O - Statement of Claim.md`
  - `P - Statement of Defence.md`

**Run the full pipeline:**

```bash
# Option A: Via HTTP API
curl -X POST http://localhost:2024/agent/start

# Check status
curl http://localhost:2024/agent/status

# Watch events stream
curl http://localhost:2024/events

# Option B: Via Python script
uv run python -m src.examples.deep_agent_orchestrator_example
```

**Success indicators:**
- ✅ SOC agent generates `dataset/court_issues/court_issues.json`
- ✅ Events appear in `dataset/agent/events/events.jsonl`
- ✅ Issue states saved in `dataset/orchestrator_state/issue_*.json`
- ✅ No errors in console output
- ✅ Final judgement generated

### 5. Automated Test Suite (Future)

Create a test file `tests/test_prompts.py`:

```python
import pytest
from src.utils.prompts import PROMPT_REGISTRY, get_prompt

def test_all_prompts_exist():
    """Verify all 14 prompts are registered"""
    expected_prompts = [
        "soc_agent_user_prompt",
        "soc_system_prompt",
        "soc_issue_table",
        "orchestrator_issue_router",
        "orchestrator_judgement_summary",
        "case_law_keywords",
        "case_law_judgement_focus",
        "case_law_issue_guidelines",
        "case_law_micro_verdict",
        "case_law_agg_recommendations",
        "documents_focus_area",
        "documents_extract_content",
        "documents_create_micro_verdict",
        "documents_agg_micro_verdicts",
    ]
    for prompt_name in expected_prompts:
        assert prompt_name in PROMPT_REGISTRY

def test_prompt_can_be_retrieved():
    """Test that prompts can be loaded"""
    prompt = get_prompt("soc_agent_user_prompt")
    assert prompt is not None

def test_prompt_with_model_binding():
    """Test model binding works (requires OPENAI_API_KEY)"""
    import os
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    prompt = get_prompt("orchestrator_issue_router", include_model=True)
    assert prompt is not None
```

Run with: `uv run pytest tests/`

---

## 🚀 How to Deploy

### Deployment Option 1: Traditional Server (Recommended)

**1. Prepare your server:**
```bash
# SSH into your server
ssh user@your-server.com

# Install Python 3.11+
sudo apt update
sudo apt install python3.11 python3.11-venv

# Install uv (fast package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**2. Clone and setup:**
```bash
# Clone repository
git clone https://github.com/Katrinaannija/resolution-backend.git
cd resolution-backend

# Checkout the branch with LangSmith removal
git checkout claude/langsmith-prompt-dependency-i9yE1

# Install dependencies
uv sync
```

**3. Configure environment:**
```bash
# Create .env file
nano .env
```

Add:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
GLOBAL_MODEL=gpt-4o-mini  # Optional: default model

# Optional: If you still use Langfuse for observability
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

**4. Create systemd service:**
```bash
sudo nano /etc/systemd/system/resolution-backend.service
```

Add:
```ini
[Unit]
Description=Resolution Backend
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/resolution-backend
Environment="PATH=/home/youruser/resolution-backend/.venv/bin:/usr/bin"
EnvironmentFile=/home/youruser/resolution-backend/.env
ExecStart=/home/youruser/.local/bin/uv run langgraph dev --host 0.0.0.0 --port 2024
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**5. Start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable resolution-backend
sudo systemctl start resolution-backend

# Check status
sudo systemctl status resolution-backend

# View logs
sudo journalctl -u resolution-backend -f
```

**6. Setup reverse proxy (nginx):**
```bash
sudo apt install nginx
sudo nano /etc/nginx/sites-available/resolution-backend
```

Add:
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:2024;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/resolution-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**7. Setup SSL (Let's Encrypt):**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

### Deployment Option 2: Docker

**1. Create Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src ./src
COPY dataset ./dataset
COPY langgraph.json ./

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 2024

# Run the server
CMD ["uv", "run", "langgraph", "dev", "--host", "0.0.0.0", "--port", "2024"]
```

**2. Create docker-compose.yml:**
```yaml
version: '3.8'

services:
  resolution-backend:
    build: .
    ports:
      - "2024:2024"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GLOBAL_MODEL=gpt-4o-mini
    volumes:
      - ./dataset:/app/dataset
    restart: unless-stopped
```

**3. Deploy:**
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Deployment Option 3: Cloud Platforms

#### Railway.app
1. Connect GitHub repository
2. Add environment variable: `OPENAI_API_KEY`
3. Set start command: `uv run langgraph dev --host 0.0.0.0 --port $PORT`
4. Deploy

#### Render.com
1. New Web Service from GitHub
2. Build Command: `uv sync`
3. Start Command: `uv run langgraph dev --host 0.0.0.0 --port $PORT`
4. Add environment variable: `OPENAI_API_KEY`
5. Deploy

#### Fly.io
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Launch app
flyctl launch

# Set secrets
flyctl secrets set OPENAI_API_KEY=sk-your-key

# Deploy
flyctl deploy
```

---

## 📊 Monitoring After Deployment

### Health Checks

```bash
# Check if server is responding
curl https://api.yourdomain.com/agent/status

# Expected: {"status": "idle|running|completed", ...}
```

### Log Monitoring

```bash
# Systemd service
sudo journalctl -u resolution-backend -f

# Docker
docker-compose logs -f

# PM2
pm2 logs resolution-backend
```

### Key Metrics to Watch

1. **API Response Time**: Should be < 1 second for status endpoints
2. **Event Generation**: Check `dataset/agent/events/events.jsonl` grows
3. **OpenAI API Errors**: Watch for rate limits or invalid key errors
4. **Memory Usage**: Should stay under 2GB for typical workloads
5. **Disk Space**: `dataset/` directory can grow over time

---

## 🔧 Troubleshooting Deployment

### Issue: "OpenAI API key not set"
**Fix:** Ensure `.env` file has `OPENAI_API_KEY=sk-...` or set environment variable

### Issue: "Port 2024 already in use"
**Fix:** Change port with `--port 3000` flag or stop conflicting service

### Issue: "Import errors" or "Module not found"
**Fix:** Run `uv sync` to ensure all dependencies are installed

### Issue: "Permission denied" writing to dataset/
**Fix:** Ensure the user running the service has write permissions:
```bash
chown -R youruser:youruser /path/to/resolution-backend/dataset
chmod -R 755 /path/to/resolution-backend/dataset
```

### Issue: High OpenAI costs
**Solutions:**
1. Use cheaper model: `GLOBAL_MODEL=gpt-3.5-turbo`
2. Implement request caching
3. Add rate limiting to HTTP endpoints
4. Monitor usage in OpenAI dashboard

---

## 🎯 Pre-Deployment Checklist

- [ ] All tests pass locally
- [ ] `.env` file configured with API keys
- [ ] Test documents exist in `dataset/documents/`
- [ ] `uv sync` runs without errors
- [ ] Development server starts successfully
- [ ] Can access HTTP endpoints locally
- [ ] Full workflow test completes
- [ ] Logs show no errors
- [ ] `.gitignore` excludes sensitive files
- [ ] Environment variables set on production server
- [ ] Firewall allows traffic on deployment port
- [ ] SSL certificate configured (for production)
- [ ] Monitoring/logging configured
- [ ] Backup strategy for `dataset/` directory

---

## 📞 Support

If you encounter issues:
1. Check logs first
2. Verify environment variables are set
3. Test locally before deploying
4. Check OpenAI API key is valid and has credits

For specific errors, provide:
- Error message and stack trace
- Relevant logs
- Steps to reproduce

## Langraph Dev

```bash
uv run langgraph dev
```

## HTTP API Routes (localhost:2024)

### Get Events
```bash
curl http://localhost:2024/events
```

### Start Agent
```bash
curl -X POST http://localhost:2024/agent/start
```

### Get Agent Status
```bash
curl http://localhost:2024/agent/status
```

### Stop Agent
```bash
curl -X POST http://localhost:2024/agent/stop
```
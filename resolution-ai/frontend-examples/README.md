# Frontend Examples

This folder contains standalone TypeScript examples that rely on LangSmith and LangChain. Each example is wired to run via `ts-node`.

## Setup

```bash
cd frontend-examples
npm install
```

Export your LangSmith credentials:

```bash
export LANGSMITH_API_KEY=sk-...
export LANGSMITH_PROJECT=my-project # optional
```

Alternatively, place these values in `/Users/arturs/resolution-ai/.env` (one directory up from this folder). The scripts automatically call `dotenv` with that path, so the keys load without exporting them manually.

## Usage

- Run the full pipeline, optionally providing a custom question:

  ```bash
  npm run run -- "How do we summarize the outstanding invoices?"
  ```

- Fetch events for a specific run id:

  ```bash
  npm run events -- <runId>
  ```

The scripts execute `lagmsmith_pipeline_events.ts`, which will print the pipeline output and the recorded child run events for the trace.

While the run is executing, the script streams each LangChain node’s inputs and outputs so you can observe the pipeline state as it progresses.

### Two-step demo pipeline

Need a lightweight graph that always emits deterministic node outputs? Export `LANGGRAPH_ASSISTANT_ID=demo_event_pipeline` (defined in `src/demo_event_pipeline.py`) before running the script. The demo graph contains only two nodes—`generate_outline` and `write_summary`—so every streamed `on_chain_end` event now prints the exact payload returned by each step.

### Event schema snapshots

Each streaming session now feeds an `EventSchemaRegistry`. The registry captures the *shape* of every event—event name, detected object kinds, field types, and a handful of truncated example values—without persisting the raw payloads. At the end of the run the script prints a JSON summary you can wire into a GUI or promote into TypeScript typings.

The same summary is automatically saved under `frontend-examples/schema-snapshots/<assistant>-<timestamp>.json`. To control where the file lands:

- Set `EVENT_SCHEMA_PATH=/absolute/or/relative/path.json`, or
- Pass `--schema-out=/path/to/output.json` when running `ts-node lagmsmith_pipeline_events.ts`.

You can also import `EventSchemaRegistry` from `eventSchemaRegistry.ts` and call `registry.toJSON()` inside an API route or WebSocket handler if you prefer streaming the summary elsewhere.

The schema summary now embeds structured JSON previews for nested objects and arrays instead of opaque `{Object}` or `[array xN]` placeholders, making it easier to inspect real sample payloads.

Need to persist the fully streamed events too? Every run writes a sanitized copy of the actual stream to `<assistant>-<timestamp>-events.json` alongside the schema snapshot. Point the log somewhere else with `EVENT_STREAM_PATH` or `--events-out=/tmp/raw-events.json`.

## React demo app

Need a browser-based UI instead of the CLI script? Check out `react-langgraph-demo/`, a minimal Vite + React experience that uses the LangGraph SDK to stream events directly in the page.

```bash
cd /Users/arturs/resolution-ai/frontend-examples/react-langgraph-demo
cp env.example .env.local   # then fill in your LangGraph details
npm install
npm run dev
```

The UI ships with a prompt box, run button, and live event viewer. Update the `input` payload in `src/App.tsx` to match your graph’s schema. Remember that Vite exposes `VITE_*` variables to the browser, so keep this app for local debugging only.


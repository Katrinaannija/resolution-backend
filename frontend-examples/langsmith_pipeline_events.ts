import { ReadableStream as NodeReadableStream } from "node:stream/web";
import * as fs from "node:fs/promises";
import { config as loadEnv } from "dotenv";
import * as path from "path";

loadEnv({
  path: path.resolve(__dirname, "..", ".env"),
});

console.log(process.env);

import { Client } from "@langchain/langgraph-sdk";
import { EventSchemaRegistry, EventSummary } from "./eventSchemaRegistry";

type JsonPrimitive = string | number | boolean | null;
type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };
type JsonObject = { [key: string]: JsonValue };

const RAW_EVENT_MAX_DEPTH = 10;
const RAW_EVENT_MAX_ARRAY_ENTRIES = 25;
const RAW_EVENT_MAX_OBJECT_KEYS = 25;

type LangGraphStreamChunk = {
  event: string;
  data: Record<string, any>;
};

type AggregatedStreamRecord = {
  assistantId: string;
  runSlug: string;
  recordedAt: string;
  runId?: string;
  output?: JsonValue;
};

function isJsonObject(value: JsonValue): value is JsonObject {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function logNodeOutputs(chunk: LangGraphStreamChunk) {
  const data = chunk.data;
  if (
    chunk.event !== "events" ||
    data?.event !== "on_chain_end" ||
    !data?.outputs
  ) {
    return;
  }

  const nodeName =
    data?.metadata?.langgraph_node ??
    data?.name ??
    (Array.isArray(data?.metadata?.langgraph_path)
      ? data.metadata.langgraph_path.join(" -> ")
      : "unknown-node");

  console.log(`\n[${nodeName}] node output`);
  console.dir(data.outputs, { depth: null });
}

const DEFAULT_SCHEMA_DIR = path.resolve(__dirname, "schema-snapshots");
const DEFAULT_AGGREGATE_SUFFIX = "-aggregated.jsonl";

function getFlagValue(name: string): string | undefined {
  const prefix = `--${name}=`;
  const arg = process.argv.find((value) => value.startsWith(prefix));
  return arg ? arg.slice(prefix.length) : undefined;
}

function timestampSlug(date = new Date()): string {
  return date.toISOString().replace(/[:.]/g, "-");
}

function resolveSchemaPath(assistantId: string, slug?: string): string {
  const cliPath = getFlagValue("schema-out");
  const envPath = process.env.EVENT_SCHEMA_PATH;
  const target = cliPath ?? envPath;

  if (target) {
    return path.resolve(process.cwd(), target);
  }

  return path.join(
    DEFAULT_SCHEMA_DIR,
    `${assistantId}-${slug ?? timestampSlug()}.json`
  );
}

function resolveEventLogPath(assistantId: string, slug?: string): string {
  const cliPath = getFlagValue("events-out");
  const envPath = process.env.EVENT_STREAM_PATH;
  const target = cliPath ?? envPath;

  if (target) {
    return path.resolve(process.cwd(), target);
  }

  return path.join(
    DEFAULT_SCHEMA_DIR,
    `${assistantId}-${slug ?? timestampSlug()}-events.json`
  );
}

function resolveAggregateLogPath(assistantId: string): string {
  const cliPath = getFlagValue("aggregate-out");
  const envPath = process.env.EVENT_AGGREGATE_PATH;
  const target = cliPath ?? envPath;

  if (target) {
    return path.resolve(process.cwd(), target);
  }

  return path.join(DEFAULT_SCHEMA_DIR, `${assistantId}${DEFAULT_AGGREGATE_SUFFIX}`);
}

async function persistSchema(schema: EventSummary[], targetPath: string) {
  await fs.mkdir(path.dirname(targetPath), { recursive: true });
  await fs.writeFile(targetPath, JSON.stringify(schema, null, 2), "utf8");
  console.log(`Schema saved to ${targetPath}`);
}

async function appendAggregatedRecord(
  record: AggregatedStreamRecord,
  targetPath: string
) {
  await fs.mkdir(path.dirname(targetPath), { recursive: true });
  await fs.appendFile(targetPath, `${JSON.stringify(record)}\n`, "utf8");
  console.log(`Aggregated stream appended to ${targetPath}`);
}

async function persistAggregatedEvent(
  record: AggregatedStreamRecord,
  targetPath: string
) {
  await fs.mkdir(path.dirname(targetPath), { recursive: true });
  await fs.writeFile(targetPath, JSON.stringify(record, null, 2), "utf8");
  console.log(`Aggregated event saved to ${targetPath}`);
}

function isTopLevelEvent(data: Record<string, any>, assistantId: string): boolean {
  if (!data) {
    return false;
  }
  if (data.name === assistantId) {
    return true;
  }
  const graphId = data?.metadata?.graph_id;
  return typeof graphId === "string" && graphId === assistantId;
}

function mergeStreamingFragment(
  existing: JsonValue | undefined,
  incoming: JsonValue
): JsonValue {
  if (existing === undefined) {
    return incoming;
  }

  if (typeof existing === "string" && typeof incoming === "string") {
    return `${existing}${incoming}`;
  }

  if (Array.isArray(existing) && Array.isArray(incoming)) {
    const maxLength = Math.max(existing.length, incoming.length);
    const merged: JsonValue[] = [];
    for (let idx = 0; idx < maxLength; idx += 1) {
      const nextValue = incoming[idx];
      if (nextValue === undefined) {
        merged[idx] = existing[idx];
        continue;
      }
      const currentValue = existing[idx];
      merged[idx] =
        currentValue === undefined
          ? nextValue
          : mergeStreamingFragment(currentValue, nextValue);
    }
    return merged as JsonValue;
  }

  if (isJsonObject(existing) && isJsonObject(incoming)) {
    const merged: JsonObject = { ...existing };
    Object.entries(incoming).forEach(([key, value]) => {
      merged[key] = mergeStreamingFragment(
        merged[key] as JsonValue | undefined,
        value
      );
    });
    return merged;
  }

  return incoming;
}

function mergeFinalSnapshot(
  existing: JsonValue | undefined,
  incoming: JsonValue
): JsonValue {
  if (existing === undefined) {
    return incoming;
  }

  if (typeof existing === "string" && typeof incoming === "string") {
    return existing.length >= incoming.length ? existing : incoming;
  }

  if (Array.isArray(existing) && Array.isArray(incoming)) {
    const maxLength = Math.max(existing.length, incoming.length);
    const merged: JsonValue[] = [];
    for (let idx = 0; idx < maxLength; idx += 1) {
      const currentValue = existing[idx];
      const nextValue = incoming[idx];
      if (currentValue !== undefined && nextValue !== undefined) {
        merged[idx] = mergeFinalSnapshot(currentValue, nextValue);
      } else if (currentValue !== undefined) {
        merged[idx] = currentValue;
      } else if (nextValue !== undefined) {
        merged[idx] = nextValue;
      }
    }
    return merged as JsonValue;
  }

  if (isJsonObject(existing) && isJsonObject(incoming)) {
    const merged: JsonObject = { ...incoming };
    Object.entries(existing).forEach(([key, value]) => {
      merged[key] =
        key in merged
          ? mergeFinalSnapshot(value, merged[key] as JsonValue)
          : value;
    });
    return merged;
  }

  return existing ?? incoming;
}

function sanitizeForJson(value: unknown, depth = 0): JsonValue {
  if (depth > RAW_EVENT_MAX_DEPTH) {
    return "[Truncated]";
  }

  if (
    value === null ||
    typeof value === "string" ||
    typeof value === "boolean"
  ) {
    return value as JsonValue;
  }

  if (typeof value === "number") {
    return Number.isFinite(value) ? value : `Number(${value})`;
  }

  if (typeof value === "bigint") {
    return `BigInt(${value.toString()})`;
  }

  if (typeof value === "symbol") {
    return `Symbol(${value.description ?? ""})`;
  }

  if (typeof value === "function") {
    return "[Function]";
  }

  if (value instanceof Date) {
    return value.toISOString();
  }

  if (value instanceof URL) {
    return value.toString();
  }

  if (value instanceof NodeReadableStream) {
    return "[ReadableStream]";
  }

  if (Buffer.isBuffer(value)) {
    return `[Buffer length=${value.length}]`;
  }

  if (Array.isArray(value)) {
    const items = value
      .slice(0, RAW_EVENT_MAX_ARRAY_ENTRIES)
      .map((entry) => sanitizeForJson(entry, depth + 1));
    if (value.length > RAW_EVENT_MAX_ARRAY_ENTRIES) {
      items.push(`[+${value.length - RAW_EVENT_MAX_ARRAY_ENTRIES} more]`);
    }
    return items as JsonValue;
  }

  if (value && typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>);
    const result: Record<string, JsonValue> = {};
    entries.slice(0, RAW_EVENT_MAX_OBJECT_KEYS).forEach(([key, child]) => {
      result[key] = sanitizeForJson(child, depth + 1);
    });
    if (entries.length > RAW_EVENT_MAX_OBJECT_KEYS) {
      result["__truncated__"] = `[+${entries.length - RAW_EVENT_MAX_OBJECT_KEYS} keys]`;
    }
    return result;
  }

  return String(value);
}

async function main() {
  const apiUrl = process.env.LANGSMITH_DEPLOYMENT_URL;
  const apiKey = process.env.LANGSMITH_API_KEY;
  const assistantId = process.env.LANGGRAPH_ASSISTANT_ID ?? "orchestrator_deep_agent";
  const runSlug = timestampSlug();

  if (!apiUrl) throw new Error("LANGGRAPH_API_URL not set");
  if (!apiKey) throw new Error("LANGSMITH_API_KEY not set");

  const client = new Client({
    apiUrl: apiUrl,
    apiKey: apiKey,
  });

  // --- choose: stateless vs stateful run ---

  // Option A: stateless run (no thread, nothing stored in checkpointer)
  const threadId: string | null = null;

  // Option B: stateful run (uncomment if you want persistent thread)
  // const thread = await client.threads.create();
  // const threadId: string = thread.thread_id;

  // --- pipeline input ---
  // Shape MUST match your graph’s expected input schema
  const input = {
    // Common pattern if you built a chat-style pipeline:
    messages: [
      { role: "user", content: "Run the dev pipeline for me please" },
    ],

    // Add any other fields your pipeline expects, e.g.:
    // query: "some value",
    // metadata: { userId: "123" },
  };

  // --- stream everything ---

  // streamMode notes:
  //  - "events"   -> literally all events (best if you want *everything*)
  //  - "updates"  -> just state updates per node
  //  - "values"   -> full graph state each step
  //  - "messages-tuple" -> token streaming + metadata (for chat UIs)
  //
  // streamSubgraphs: true will also stream outputs from subgraphs
  const stream = client.runs.stream(
    threadId,          // null for stateless run, or a thread_id string
    assistantId,       // e.g. "agent"
    {
      input,
      streamMode: "events",     // "all outputs" style stream
      streamSubgraphs: true,    // include subgraph events if you have them
    }
  );

  const registry = new EventSchemaRegistry();
  let aggregatedOutput: JsonValue | undefined;
  let runId: string | undefined;

  // Consume the async generator
  for await (const chunk of stream as AsyncGenerator<LangGraphStreamChunk>) {
    // chunk has shape: { event, data, id? }
    // console.log("===== STREAM EVENT =====");
    // console.log("event:", chunk.event);
    // console.dir(chunk.data, { depth: null });

    logNodeOutputs(chunk);
    registry.record(chunk.event, chunk.data);

    if (chunk.event === "metadata") {
      if (typeof chunk.data?.run_id === "string") {
        runId = chunk.data.run_id;
      }
      continue;
    }

    if (chunk.event !== "events") {
      continue;
    }

    const eventData = chunk.data;
    if (!isTopLevelEvent(eventData, assistantId)) {
      continue;
    }

    if (eventData?.event === "on_chain_stream" && eventData?.data?.chunk) {
      const fragment = sanitizeForJson(eventData.data.chunk);
      aggregatedOutput = mergeStreamingFragment(aggregatedOutput, fragment);
      continue;
    }

    if (eventData?.event === "on_chain_end") {
      const payload =
        eventData?.data?.output ??
        eventData?.data?.outputs ??
        eventData?.data;
      if (payload !== undefined) {
        const fragment = sanitizeForJson(payload);
        aggregatedOutput = mergeFinalSnapshot(aggregatedOutput, fragment);
      }
    }
  }

  const schemaSummary = registry.toJSON();
  console.log("Schema summary:");
  console.dir(schemaSummary, { depth: null });
  const schemaPath = resolveSchemaPath(assistantId, runSlug);
  const eventLogPath = resolveEventLogPath(assistantId, runSlug);
  const aggregateLogPath = resolveAggregateLogPath(assistantId);
  const aggregatedRecord: AggregatedStreamRecord = {
    assistantId,
    runSlug,
    recordedAt: new Date().toISOString(),
    runId,
    output: aggregatedOutput,
  };

  await persistSchema(schemaSummary, schemaPath);
  await persistAggregatedEvent(aggregatedRecord, eventLogPath);
  await appendAggregatedRecord(aggregatedRecord, aggregateLogPath);
  console.log("Run finished.");
}

main().catch((err) => {
  console.error("Error while running pipeline:", err);
  process.exit(1);
});

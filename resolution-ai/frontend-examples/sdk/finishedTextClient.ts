import { Client } from "@langchain/langgraph-sdk";

type JsonPrimitive = string | number | boolean | null;
type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };
type JsonObject = { [key: string]: JsonValue };

function isJsonObject(value: JsonValue): value is JsonObject {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
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
      } else {
        merged[idx] = mergeStreamingFragment(existing[idx], nextValue);
      }
    }
    return merged;
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
    return incoming.length >= existing.length ? incoming : existing;
  }

  if (Array.isArray(existing) && Array.isArray(incoming)) {
    const maxLength = Math.max(existing.length, incoming.length);
    const merged: JsonValue[] = [];
    for (let idx = 0; idx < maxLength; idx += 1) {
      const current = existing[idx];
      const nextValue = incoming[idx];
      if (current !== undefined && nextValue !== undefined) {
        merged[idx] = mergeFinalSnapshot(current, nextValue);
      } else if (current !== undefined) {
        merged[idx] = current;
      } else if (nextValue !== undefined) {
        merged[idx] = nextValue;
      }
    }
    return merged;
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

  return incoming ?? existing;
}

function renderMessages(messages: JsonValue): string {
  if (!Array.isArray(messages)) {
    return "";
  }
  return messages
    .map((entry) => {
      if (isJsonObject(entry)) {
        const content = entry["content"];
        if (typeof content === "string") {
          return content;
        }
        if (Array.isArray(content)) {
          return content
            .map((segment) => {
              if (typeof segment === "string") {
                return segment;
              }
              if (isJsonObject(segment) && typeof segment["text"] === "string") {
                return segment["text"];
              }
              return "";
            })
            .join("");
        }
      } else if (typeof entry === "string") {
        return entry;
      }
      return "";
    })
    .filter(Boolean)
    .join("\n\n");
}

function renderTextFromOutput(output?: JsonValue): string {
  if (output === undefined || output === null) {
    return "";
  }
  if (typeof output === "string") {
    return output;
  }
  if (Array.isArray(output)) {
    return output.map((entry) => renderTextFromOutput(entry)).join("\n\n");
  }
  if (isJsonObject(output)) {
    if (output["messages"]) {
      return renderMessages(output["messages"]);
    }
    if (typeof output["content"] === "string") {
      return output["content"];
    }
  }
  return JSON.stringify(output, null, 2);
}

function isTopLevelEvent(data: Record<string, any>, assistantId: string): boolean {
  if (!data) {
    return false;
  }
  if (data.name === assistantId) {
    return true;
  }
  return data?.metadata?.graph_id === assistantId;
}

export interface RunPromptTextOptions {
  apiUrl: string;
  apiKey: string;
  promptName: string;
  input: Record<string, unknown>;
  threadId: string;
}

export interface FinishedTextEvent {
  runId?: string;
  promptName: string;
  recordedAt: string;
  output: JsonValue | undefined;
  text: string;
}

export async function runPromptToFinishedText(
  options: RunPromptTextOptions
): Promise<FinishedTextEvent> {
  const { apiKey, apiUrl, promptName, input, threadId } = options;

  const client = new Client({
    apiKey,
    apiUrl,
  });

  let aggregatedOutput: JsonValue | undefined;
  let runId: string | undefined;

  const stream = client.runs.stream(threadId, promptName, {
    input,
    streamMode: "events",
    streamSubgraphs: true,
  });

  for await (const chunk of stream as AsyncGenerator<Record<string, any>>) {
    if (chunk.event === "metadata" && typeof chunk.data?.run_id === "string") {
      runId = chunk.data.run_id;
      continue;
    }

    if (chunk.event !== "events" || !isTopLevelEvent(chunk.data, promptName)) {
      continue;
    }

    const event = chunk.data?.event;
    if (event === "on_chain_stream" && chunk.data?.data?.chunk) {
      aggregatedOutput = mergeStreamingFragment(
        aggregatedOutput,
        chunk.data.data.chunk as JsonValue
      );
      continue;
    }

    if (event === "on_chain_end") {
      const payload =
        chunk.data?.data?.output ??
        chunk.data?.data?.outputs ??
        chunk.data?.data;
      if (payload !== undefined) {
        aggregatedOutput = mergeFinalSnapshot(
          aggregatedOutput,
          payload as JsonValue
        );
      }
    }
  }

  return {
    runId,
    promptName,
    recordedAt: new Date().toISOString(),
    output: aggregatedOutput,
    text: renderTextFromOutput(aggregatedOutput),
  };
}



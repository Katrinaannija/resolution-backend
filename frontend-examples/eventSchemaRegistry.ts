type Primitive =
  | "string"
  | "number"
  | "boolean"
  | "null"
  | "undefined"
  | "bigint"
  | "symbol";

type ValueKind = Primitive | "object" | "array";

export interface FieldSummary {
  path: string;
  types: ValueKind[];
  examples: string[];
}

export interface EventSummary {
  event: string;
  occurrences: number;
  objectKinds: string[];
  fields: FieldSummary[];
}

export interface EventSchemaRegistryOptions {
  maxExamplesPerField?: number;
  maxStringLength?: number;
  maxDepth?: number;
  maxArrayEntries?: number;
  maxExampleLength?: number;
  maxPreviewKeys?: number;
  maxPreviewDepth?: number;
}

interface InternalFieldSummary {
  path: string;
  types: Set<ValueKind>;
  examples: Set<string>;
}

interface InternalEventSummary {
  event: string;
  occurrences: number;
  objectKinds: Set<string>;
  fields: Map<string, InternalFieldSummary>;
}

/**
 * Collects variations for streamed LangSmith/LangGraph events without storing
 * the verbatim payloads. Useful for building API contracts and GUI typing.
 */
export class EventSchemaRegistry {
  private readonly summaries = new Map<string, InternalEventSummary>();
  private readonly options: Required<EventSchemaRegistryOptions>;

  constructor(options?: EventSchemaRegistryOptions) {
    this.options = {
      maxExamplesPerField: options?.maxExamplesPerField ?? 4,
      maxStringLength: options?.maxStringLength ?? 60,
      maxDepth: options?.maxDepth ?? 5,
      maxArrayEntries: options?.maxArrayEntries ?? 3,
      maxExampleLength: options?.maxExampleLength ?? 240,
      maxPreviewKeys: options?.maxPreviewKeys ?? 8,
      maxPreviewDepth: options?.maxPreviewDepth ?? 3,
    };
  }

  record(event: string, payload: unknown) {
    const summary = this.getOrCreateSummary(event);
    summary.occurrences += 1;
    summary.objectKinds.add(this.describeObjectKind(payload));
    this.walk(payload, summary, [], 0);
  }

  get(event: string): EventSummary | undefined {
    const summary = this.summaries.get(event);
    return summary ? this.serialize(summary) : undefined;
  }

  toJSON(): EventSummary[] {
    return Array.from(this.summaries.values()).map((summary) =>
      this.serialize(summary)
    );
  }

  printReport() {
    console.dir(this.toJSON(), { depth: null });
  }

  private getOrCreateSummary(event: string): InternalEventSummary {
    if (!this.summaries.has(event)) {
      this.summaries.set(event, {
        event,
        occurrences: 0,
        objectKinds: new Set<string>(),
        fields: new Map<string, InternalFieldSummary>(),
      });
    }
    return this.summaries.get(event)!;
  }

  private walk(
    value: unknown,
    summary: InternalEventSummary,
    path: string[],
    depth: number
  ) {
    if (depth > this.options.maxDepth) {
      return;
    }

    const fieldPath = path.join(".");
    if (fieldPath) {
      const fieldSummary = this.getOrCreateField(summary, fieldPath);
      const kind = this.describeValueKind(value);
      fieldSummary.types.add(kind);
      const example = this.exampleFor(value);
      if (
        example !== undefined &&
        fieldSummary.examples.size < this.options.maxExamplesPerField
      ) {
        fieldSummary.examples.add(example);
      }
    }

    if (value === null || value === undefined) {
      return;
    }

    if (Array.isArray(value)) {
      const entries = value.slice(0, this.options.maxArrayEntries);
      entries.forEach((entry, idx) => {
        this.walk(entry, summary, [...path, `[${idx}]`], depth + 1);
      });
      return;
    }

    if (typeof value === "object") {
      Object.entries(value).forEach(([key, child]) => {
        this.walk(child, summary, [...path, key], depth + 1);
      });
    }
  }

  private getOrCreateField(
    summary: InternalEventSummary,
    path: string
  ): InternalFieldSummary {
    if (!summary.fields.has(path)) {
      summary.fields.set(path, {
        path,
        types: new Set<ValueKind>(),
        examples: new Set<string>(),
      });
    }
    return summary.fields.get(path)!;
  }

  private exampleFor(value: unknown): string | undefined {
    if (value === null) return "null";
    if (value === undefined) return "undefined";
    if (typeof value === "string") {
      return this.truncate(value, this.options.maxStringLength);
    }
    if (typeof value === "number" || typeof value === "boolean") {
      return String(value);
    }
    if (typeof value === "bigint") {
      return `${value.toString()}n`;
    }
    if (typeof value === "symbol") {
      return value.description ? `Symbol(${value.description})` : "Symbol()";
    }
    if (Array.isArray(value) || typeof value === "object") {
      return this.formatStructuredExample(value);
    }
    return undefined;
  }

  private formatStructuredExample(value: unknown): string | undefined {
    try {
      const preview = this.previewValue(value, 0);
      if (preview === undefined) {
        return undefined;
      }
      const serialized = JSON.stringify(preview);
      return this.truncate(serialized, this.options.maxExampleLength);
    } catch {
      return undefined;
    }
  }

  private previewValue(value: unknown, depth: number): unknown {
    if (depth >= this.options.maxPreviewDepth) {
      return "[Truncated]";
    }
    if (value === null) {
      return null;
    }
    if (value === undefined) {
      return "undefined";
    }
    if (typeof value === "string") {
      return this.truncate(value, this.options.maxStringLength);
    }
    if (typeof value === "number" || typeof value === "boolean") {
      return value;
    }
    if (typeof value === "bigint") {
      return `${value.toString()}n`;
    }
    if (typeof value === "symbol") {
      return value.description ? `Symbol(${value.description})` : "Symbol()";
    }
    if (Array.isArray(value)) {
      return value
        .slice(0, this.options.maxArrayEntries)
        .map((entry) => this.previewValue(entry, depth + 1));
    }
    if (typeof value === "object") {
      const entries = Object.entries(value as Record<string, unknown>).slice(
        0,
        this.options.maxPreviewKeys
      );
      return entries.reduce<Record<string, unknown>>(
        (acc, [key, child]) => {
          acc[key] = this.previewValue(child, depth + 1);
          return acc;
        },
        {}
      );
    }
    return String(value);
  }

  private truncate(value: string, limit: number): string {
    return value.length > limit ? `${value.slice(0, limit)}…` : value;
  }

  private describeValueKind(value: unknown): ValueKind {
    if (value === null) return "null";
    if (value === undefined) return "undefined";
    if (Array.isArray(value)) return "array";
    const type = typeof value;
    if (type === "object") return "object";
    return type as Primitive;
  }

  private describeObjectKind(value: unknown): string {
    if (value === null) return "null";
    if (Array.isArray(value)) return "array";
    if (typeof value === "object") {
      const record = value as Record<string, unknown>;
      if (typeof record.type === "string") return record.type;
      if (typeof record.__typename === "string") return record.__typename;
      const ctor = (value as { constructor?: { name?: string } }).constructor;
      if (ctor?.name) return ctor.name;
      return "object";
    }
    return typeof value;
  }

  private serialize(summary: InternalEventSummary): EventSummary {
    return {
      event: summary.event,
      occurrences: summary.occurrences,
      objectKinds: Array.from(summary.objectKinds),
      fields: Array.from(summary.fields.values()).map((field) => ({
        path: field.path,
        types: Array.from(field.types),
        examples: Array.from(field.examples),
      })),
    };
  }
}


# Lanceglass — Code Snippets (verbatim)

Source: `/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/lanceglass/`
Commit: `cdfeca8` (2026-09-01) · package.json `26.9.1-alpha.1401` · `@lancedb/lancedb@0.27.2`, `apache-arrow@18.1.0`, Bun runtime.

> "A local-first looking glass for Claude Code and Codex JSONL histories, powered by LanceDB." — package.json description

This document exists so a reader never has to open the source. All blocks below are copy-pasted verbatim from the repo, with `file:line` citations. Where the requested feature (topic 5, topic 7) turned out **not to exist** in the code, that is stated plainly instead of being papered over — see the "Reality check" callouts in sections 5 and 7.

---

## 1. The JSONL parser / normalizer

Everything funnels through one function: `normalize()` in `src/normalize.ts`. It accepts one already-`JSON.parse`d JSONL record plus context (source label, file path, file hash, line number, fallback session id) and returns `{ events, occurrences }` — typed rows ready for LanceDB `insert`. It understands **two envelope dialects** (Claude Code and Codex) and normalizes both to the same `EventRow` shape.

### 1.1 Canonical ID derivation primitives

`src/normalize.ts:1-32`

```ts
import { createHash } from "node:crypto";
import { basename } from "node:path";
import type { EventRow, EventSourceRow, SemanticRole } from "./types";

export const sha256 = (value: string | Uint8Array) =>
  createHash("sha256").update(value).digest("hex");

function stable(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  return `{${Object.entries(value as Record<string, unknown>)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, item]) => `${JSON.stringify(key)}:${stable(item)}`)
    .join(",")}}`;
}

const string = (value: unknown) => typeof value === "string" ? value : "";

function toolResultText(value: unknown): string {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    return value.map((item) => {
      if (typeof item === "string") return item;
      if (item && typeof item === "object") {
        const block = item as Record<string, unknown>;
        return block.type === "text" ? string(block.text) : stable(block);
      }
      return "";
    }).filter(Boolean).join("\n");
  }
  return value && typeof value === "object" ? stable(value) : "";
}
```

`stable()` is the load-bearing primitive here: a **deterministic, key-sorted JSON stringifier**. It is used both to flatten non-text tool payloads into searchable text, and — critically — as the input to `sha256()` when a record has no natural unique id, so the same logical event always hashes to the same fallback UUID regardless of source key ordering.

### 1.2 The `Block` shape and per-envelope state

`src/normalize.ts:57-75`

```ts
type Block = {
  index: number;
  type: string;
  role: SemanticRole;
  text: string;
  toolName: string;
  toolUseId: string;
  isError: boolean;
};

export type NormalizationState = {
  sessionId: string;
  cwd: string;
  sessionIdentity: "fallback" | "session_id" | "id";
};

export function createNormalizationState(fallbackSession: string): NormalizationState {
  return { sessionId: fallbackSession, cwd: "", sessionIdentity: "fallback" };
}
```

`NormalizationState` is threaded line-by-line through one JSONL file (see the importer's `for await` loops in §6). It exists because a Codex rollout spreads session identity and `cwd` across separate `session_meta` / `turn_context` records that arrive *before* the `response_item` records that need them.

### 1.3 Claude Code envelope → blocks

`src/normalize.ts:77-138`

```ts
function extractBlocks(record: Record<string, unknown>): Block[] {
  const envelope = string(record.type);
  if (envelope === "summary") {
    const text = string(record.summary);
    return text ? [{
      index: 0, type: "summary", role: "summary", text,
      toolName: "", toolUseId: "", isError: false,
    }] : [];
  }
  if (envelope !== "user" && envelope !== "assistant") return [];

  const message = record.message && typeof record.message === "object"
    ? record.message as Record<string, unknown>
    : {};
  const content = message.content;
  if (typeof content === "string") {
    return content.trim() ? [{
      index: 0,
      type: "text",
      role: envelope === "user" ? "human_intent" : "assistant_answer",
      text: content,
      toolName: "",
      toolUseId: "",
      isError: false,
    }] : [];
  }
  if (!Array.isArray(content)) return [];

  return content.flatMap((value, index): Block[] => {
    if (!value || typeof value !== "object") return [];
    const block = value as Record<string, unknown>;
    const type = string(block.type);
    if (type === "text" && string(block.text).trim()) return [{
      index,
      type,
      role: envelope === "user" ? "human_intent" : "assistant_answer",
      text: string(block.text),
      toolName: "",
      toolUseId: "",
      isError: false,
    }];
    if (type === "tool_use") return [{
      index,
      type,
      role: "tool_action",
      text: stable(block.input ?? {}),
      toolName: string(block.name),
      toolUseId: string(block.id),
      isError: false,
    }];
    if (type === "tool_result" && toolResultText(block.content).trim()) return [{
      index,
      type,
      role: "tool_evidence",
      text: toolResultText(block.content),
      toolName: "",
      toolUseId: string(block.tool_use_id),
      isError: block.is_error === true,
    }];
    return []; // progress, thinking and images are not search documents.
  });
}
```

### 1.4 Codex envelope → blocks (session/cwd state machine)

`src/normalize.ts:140-256`

```ts
function codexBlocks(
  record: Record<string, unknown>,
  state: NormalizationState,
): { eventUuid: string; envelope: string; blocks: Block[] } {
  const envelope = string(record.type);
  const payload = record.payload && typeof record.payload === "object" && !Array.isArray(record.payload)
    ? record.payload as Record<string, unknown>
    : {};

  if (envelope === "session_meta") {
    // A rollout may contain a second compatibility session_meta record. The
    // first payload.id identifies the file/rollout, so do not replace it with
    // the later payload.session_id.
    const payloadId = string(payload.id);
    const legacySessionId = string(payload.session_id);
    if (payloadId && state.sessionIdentity !== "id") {
      state.sessionId = payloadId;
      state.sessionIdentity = "id";
    } else if (legacySessionId && state.sessionIdentity === "fallback") {
      state.sessionId = legacySessionId;
      state.sessionIdentity = "session_id";
    }
    state.cwd = string(payload.cwd) || state.cwd;
    return { eventUuid: "", envelope, blocks: [] };
  }
  if (envelope === "turn_context") {
    state.cwd = string(payload.cwd) || state.cwd;
    return { eventUuid: "", envelope, blocks: [] };
  }
  if (envelope !== "response_item") return { eventUuid: "", envelope, blocks: [] };

  const payloadType = string(payload.type);
  const payloadId = string(payload.id);
  const callId = string(payload.call_id);
  const eventUuid = payloadId || `hash:${sha256(stable({
    sessionId: state.sessionId,
    timestamp: record.timestamp ?? "",
    ordinal: record.__ordinal ?? "",
    payloadType,
    callId,
  }))}`;

  if (payloadType === "message") {
    const role = string(payload.role);
    if (role !== "user" && role !== "assistant") return { eventUuid, envelope, blocks: [] };
    const content = Array.isArray(payload.content) ? payload.content : [];
    const blocks = content.flatMap((item, index): Block[] => {
      if (!item || typeof item !== "object" || Array.isArray(item)) return [];
      const contentBlock = item as Record<string, unknown>;
      const contentType = string(contentBlock.type);
      const text = string(contentBlock.text);
      if (
        (contentType !== "text" && contentType !== "input_text" && contentType !== "output_text") ||
        !text.trim()
      ) return [];
      return [{
        index,
        type: contentType,
        role: role === "user" ? "human_intent" : "assistant_answer",
        text,
        toolName: "",
        toolUseId: "",
        isError: false,
      }];
    });
    return { eventUuid, envelope, blocks };
  }
  if (payloadType === "custom_tool_call") {
    const input = payload.input ?? payload.arguments ?? {};
    return {
      eventUuid,
      envelope,
      blocks: [{
        index: 0,
        type: payloadType,
        role: "tool_action",
        text: typeof input === "string" ? input : stable(input),
        toolName: string(payload.name),
        toolUseId: callId,
        isError: false,
      }],
    };
  }
  // ... function_call is the mirror of custom_tool_call (src/normalize.ts:223-238)
  if (payloadType === "custom_tool_call_output" || payloadType === "function_call_output") {
    const text = codexToolOutputText(payload.output);
    return {
      eventUuid,
      envelope,
      blocks: text.trim() ? [{
        index: 0,
        type: payloadType,
        role: "tool_evidence",
        text,
        toolName: "",
        toolUseId: callId,
        isError: false,
      }] : [],
    };
  }
  return { eventUuid, envelope, blocks: [] };
}
```

Note the fallback event id: `payloadId || hash:${sha256(stable({sessionId, timestamp, ordinal, payloadType, callId}))}`. Codex `response_item` records are *not guaranteed* to carry a stable `id`; when absent, identity is derived from a stable hash of session + timestamp + **line ordinal** (passed out-of-band, see below) + payload type + call id, so a re-import of the same byte-identical line always reproduces the same event id.

### 1.5 `normalize()` — the field mapping and canonical ID entry point

`src/normalize.ts:258-327`

```ts
export function normalize(
  record: Record<string, unknown>,
  context: {
    source: string;
    filePath: string;
    fileHash: string;
    line: number;
    fallbackSession: string;
  },
  state = createNormalizationState(context.fallbackSession),
) {
  const codex = context.source === "codex";
  // The ordinal is supplied out-of-band so fallback IDs remain independent of
  // object key ordering while the persisted source record stays untouched.
  const codexRecord = codex ? { ...record, __ordinal: context.line } : record;
  const extracted = codex ? codexBlocks(codexRecord, state) : null;
  const sessionId = codex
    ? state.sessionId
    : string(record.sessionId) || string(record.session_id) || context.fallbackSession;
  const eventUuid = codex ? extracted!.eventUuid : string(record.uuid) || `hash:${sha256(stable({
    sessionId,
    timestamp: record.timestamp ?? "",
    type: record.type ?? "",
    parentUuid: record.parentUuid ?? "",
    message: record.message ?? null,
    summary: record.summary ?? null,
  }))}`;
  const cwd = codex ? state.cwd : string(record.cwd);
  const blocks = codex ? extracted!.blocks : extractBlocks(record);

  const events: EventRow[] = blocks.map((block) => {
    const textHash = sha256(block.text);
    return {
      id: `${eventUuid}#${block.index}`,
      event_uuid: eventUuid,
      block_index: block.index,
      session_id: sessionId,
      parent_uuid: string(record.parentUuid),
      timestamp: string(record.timestamp),
      project: basename(cwd) || "?",
      envelope_type: codex ? extracted!.envelope : string(record.type),
      block_type: block.type,
      semantic_role: block.role,
      tool_name: block.toolName,
      tool_use_id: block.toolUseId,
      is_error: block.isError,
      text: block.text.slice(0, 4_000),
      text_hash: textHash,
      source: context.source,
    };
  });

  const occurrences: EventSourceRow[] = events.map((event) => ({
    id: sha256([
      event.id,
      context.source,
      context.filePath,
      context.line,
      event.text_hash,
    ].join("\0")),
    event_id: event.id,
    source: context.source,
    file_path: context.filePath,
    file_hash: context.fileHash,
    source_line: context.line,
    observed_text_hash: event.text_hash,
  }));

  return { events, occurrences };
}
```

**The identity model in one sentence:** a *canonical event* (`events.id = "${eventUuid}#${blockIndex}"`) is content identity (deduplicated globally across files), while an *occurrence* (`event_sources.id = sha256(eventId + source + filePath + line + textHash)`) is provenance (one row per physical sighting of that event in a specific file at a specific line) — so the same canonical event observed from two different JSONL files produces one `events` row and two `event_sources` rows.

### 1.6 The typed row shapes it produces

`src/types.ts:1-66`

```ts
export type SemanticRole =
  | "human_intent"
  | "assistant_answer"
  | "tool_action"
  | "tool_evidence"
  | "summary";

export type EventRow = {
  id: string;
  event_uuid: string;
  block_index: number;
  session_id: string;
  parent_uuid: string;
  timestamp: string;
  project: string;
  envelope_type: string;
  block_type: string;
  semantic_role: SemanticRole;
  tool_name: string;
  tool_use_id: string;
  is_error: boolean;
  text: string;
  text_hash: string;
  source: string;
};

export type EmbeddingEventRow = Pick<
  EventRow,
  | "id"
  | "session_id"
  | "timestamp"
  | "project"
  | "block_type"
  | "semantic_role"
  | "text"
  | "source"
>;

export type EventVectorRow = {
  event_id: string;
  // Scalar scope metadata is deliberately copied into the vector store so a
  // later ANN query can pre-filter without joining across physical databases.
  source: string;
  project: string;
  session_id: string;
  timestamp: string;
  // This hashes the exact text sent to the embedding provider, rather than
  // EventRow.text_hash (which tracks the untruncated source block).
  text_hash: string;
  model: string;
  dimension: number;
  embedded_at: string;
  vector: Float32Array;
};

export type EventSourceRow = {
  id: string;
  event_id: string;
  source: string;
  file_path: string;
  file_hash: string;
  source_line: number;
  observed_text_hash: string;
};
```

### 1.7 Field mapping proven by test (both dialects)

`tests/normalize.test.ts:21-56` (Codex — note the same call also proves `cwd`/`project` state carries across records via `turn_context`, and that `input_image` is dropped):

```ts
describe("Codex JSONL normalization", () => {
  test("captures file session and cwd, then maps only user and assistant text", () => {
    const events = run([
      { type: "session_meta", timestamp: "t0", payload: {
        id: "rollout-session", session_id: "legacy-session", cwd: "/work/sample-oracle",
      } },
      // Compatibility metadata must not replace the unique rollout id.
      { type: "session_meta", timestamp: "t0", payload: {
        id: "legacy-session", session_id: "legacy-session", cwd: "/work/sample-oracle",
      } },
      { type: "response_item", timestamp: "t1", payload: {
        type: "message", id: "user-message", role: "user",
        content: [
          { type: "input_text", text: "What changed?" },
          { type: "input_image", image_url: "data:image/png;base64,secret" },
        ],
      } },
      { type: "turn_context", timestamp: "t2", payload: { cwd: "/work/new-oracle" } },
      { type: "response_item", timestamp: "t3", payload: {
        type: "message", id: "assistant-message", role: "assistant",
        content: [{ type: "output_text", text: "The importer changed." }],
      } },
    ]);

    expect(events).toHaveLength(2);
    expect(events[0]).toMatchObject({
      id: "user-message#0", event_uuid: "user-message", session_id: "rollout-session",
      project: "sample-oracle", block_type: "input_text", semantic_role: "human_intent",
      text: "What changed?", timestamp: "t1",
    });
    expect(events[1]).toMatchObject({
      id: "assistant-message#0", session_id: "rollout-session", project: "new-oracle",
      block_type: "output_text", semantic_role: "assistant_answer",
      text: "The importer changed.", timestamp: "t3",
    });
    expect(events.some((event) => event.text.includes("data:image"))).toBe(false);
  });
```

`tests/normalize.test.ts:184-200` (Claude Code):

```ts
describe("Claude normalization compatibility", () => {
  test("preserves the existing Claude envelope mapping", () => {
    const rows = normalize({
      type: "assistant", uuid: "claude-event", sessionId: "claude-session",
      cwd: "/work/claude-demo", timestamp: "2026-01-01T00:00:00Z",
      message: { content: [
        { type: "text", text: "answer" },
        { type: "tool_use", id: "tool-1", name: "Bash", input: { command: "pwd" } },
      ] },
    }, { ...context, source: "claude" });
    expect(rows.events).toEqual([
      expect.objectContaining({ id: "claude-event#0", semantic_role: "assistant_answer", text: "answer" }),
      expect.objectContaining({
        id: "claude-event#1", semantic_role: "tool_action", tool_name: "Bash",
        tool_use_id: "tool-1", text: "{\"command\":\"pwd\"}",
      }),
    ]);
  });
```

### 1.8 A real fixture line-for-line

`fixtures/minimal/session.jsonl` (bundled — the whole demo/CI path runs on this, never on a real user's history):

```jsonl
{"type":"user","uuid":"u-1","sessionId":"smoke-session","timestamp":"2026-08-30T00:00:00.000Z","cwd":"/demo/lanceglass","message":{"role":"user","content":"How do we import JSONL and know whether it is new?"}}
{"type":"assistant","uuid":"a-1","parentUuid":"u-1","sessionId":"smoke-session","timestamp":"2026-08-30T00:00:01.000Z","cwd":"/demo/lanceglass","message":{"role":"assistant","content":[{"type":"text","text":"Use a source-file manifest plus stable event UUID and block identity."},{"type":"tool_use","id":"tool-1","name":"Bash","input":{"command":"wc -l session.jsonl"}}]}}
{"type":"user","uuid":"r-1","parentUuid":"a-1","sessionId":"smoke-session","timestamp":"2026-08-30T00:00:02.000Z","cwd":"/demo/lanceglass","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"tool-1","content":"6 session.jsonl"}]}}
{"type":"summary","sessionId":"smoke-session","timestamp":"2026-08-30T00:00:03.000Z","summary":"Created a smoke-first typed JSONL database lab."}
{"type":"progress","uuid":"p-1","sessionId":"smoke-session","data":{"type":"hook_progress"}}
{deliberately corrupt smoke line
```

Line 5 (`type: "progress"`) is real telemetry that produces **zero** blocks (falls through `extractBlocks`'s envelope check). Line 6 is deliberately invalid JSON — the importer counts it as `corrupt` and moves on (§6, §8) rather than aborting the file.

---

## 2. Chunking / block-splitting — how one message becomes N searchable units

There is no separate "chunker" module. Splitting happens **inside** `extractBlocks` / `codexBlocks` (§1.3, §1.4): a single JSONL record's `message.content` (Claude) or `payload.content` (Codex) is an **array of content blocks** — text, `tool_use`, `tool_result`, images, thinking, etc. `.flatMap()` walks that array and keeps only the blocks the app considers a "search document":

`src/normalize.ts:105-138` (the Claude side, repeated for orientation):

```ts
  return content.flatMap((value, index): Block[] => {
    if (!value || typeof value !== "object") return [];
    const block = value as Record<string, unknown>;
    const type = string(block.type);
    if (type === "text" && string(block.text).trim()) return [{ index, type, role: /* human_intent | assistant_answer */ envelope === "user" ? "human_intent" : "assistant_answer", text: string(block.text), toolName: "", toolUseId: "", isError: false }];
    if (type === "tool_use") return [{ index, type, role: "tool_action", text: stable(block.input ?? {}), toolName: string(block.name), toolUseId: string(block.id), isError: false }];
    if (type === "tool_result" && toolResultText(block.content).trim()) return [{ index, type, role: "tool_evidence", text: toolResultText(block.content), toolName: "", toolUseId: string(block.tool_use_id), isError: block.is_error === true }];
    return []; // progress, thinking and images are not search documents.
  });
```

Each surviving `Block` becomes its **own** `EventRow`, keyed `"${eventUuid}#${block.index}"` (`src/normalize.ts:291`) — so block index inside the original message *is* the chunk offset, and it is stable across re-imports because it is the array index, not a counter that depends on which blocks survived filtering.

Two hard-coded length limits act as the actual "chunk size" ceilings, applied at two different points in the pipeline:

1. **At ingest**, every block's text is hard-truncated to 4,000 characters before it is ever written to the `events` table — `src/normalize.ts:304`:
   ```ts
   text: block.text.slice(0, 4_000),
   ```
2. **At embedding time**, a second, independent truncation to 2,000 characters is applied on top of the already-4,000-char-capped stored text — `src/schemas.ts:27-28` and `src/embeddings.ts:171-173`:
   ```ts
   // src/schemas.ts
   export const EMBEDDING_TEXT_LIMIT = 2_000;
   export const EMBEDDING_TEXT_POLICY = "event.text.slice(0,2000)@v1";
   ```
   ```ts
   // src/embeddings.ts
   export function embeddingText(text: string) {
     return text.slice(0, EMBEDDING_TEXT_LIMIT);
   }
   ```
   The policy string `"event.text.slice(0,2000)@v1"` is itself persisted into the vector table's Arrow schema metadata (§3) — versioning the *truncation rule*, not just the model, so a future change to the slice length is a detectable contract break rather than a silent drift.

Not every surviving block becomes a "searchable unit" for embedding purposes, though — `isEmbeddableEvent` is the second-stage filter that decides which rows are eligible to ever get a vector, by role priority and minimum length:

`src/embeddings.ts:117-135, 175-185`:

```ts
type Candidate = {
  event: EmbeddingEventRow;
  text: string;
  textHash: string;
};

const ROLE_PRIORITY: Record<EmbeddingEventRow["semantic_role"], number> = {
  human_intent: 0,
  summary: 1,
  assistant_answer: 2,
  tool_action: 3,
  tool_evidence: 3,
};

const EMBEDDING_ROLES = [
  "human_intent",
  "summary",
  "assistant_answer",
] as const;
```

```ts
export const EMBEDDING_MIN_CHARACTERS = 80;
// ...
export function isEmbeddableEvent(event: EmbeddingEventRow) {
  if (ROLE_PRIORITY[event.semantic_role] > 2) return false;
  if (!["text", "summary", "input_text", "output_text"].includes(event.block_type)) {
    return false;
  }
  const text = embeddingText(event.text);
  const trimmed = text.trimStart();
  return text.trim().length > EMBEDDING_MIN_CHARACTERS &&
    !trimmed.startsWith("<system-reminder>") &&
    !trimmed.startsWith("[Image: source:");
}
```

So the full chunk pipeline is: **JSONL record → content array → per-block `EventRow` (4,000-char cap, stable `id#index`) → role/length/prefix filter (`isEmbeddableEvent`) → 2,000-char re-slice (`embeddingText`) → embedding batch**. `tool_action` / `tool_evidence` blocks are stored and browsable, but role priority `> 2` excludes them from ever being embedded (`ROLE_PRIORITY.tool_action === 3`).

---

## 3. LanceDB table creation + insert (schema, vector dimensions, index)

Lanceglass deliberately runs **two physical LanceDB stores**, opened independently so that ordinary import never touches (or requires) an embedding service — `lessons/08-optional-embeddings.md:1-17`:

> The Lanceglass has **two physical LanceDB stores** on purpose:
>
> | Store | Default path | Tables | When it may be opened |
> |---|---|---|---|
> | `database.plain` | `.data/lancedb` | `events`, `event_sources`, `source_files` | every plan/import/UI read |
> | `database.vector` | `.data/lancedb.vector[.<space-id>]` | `event_vectors` | only explicit embedding or future semantic search |
>
> The boundary is visible in code:
> ```ts
> const database = await Database.open();
> await importSource(database.plain, spec); // no Ollama, no vector connection
> await embedPending(database.plain, database.vector, provider, { maxEvents: 300 });
> ```

### 3.1 The three plain-store Arrow schemas + the vector schema factory

`src/schemas.ts` (full file):

```ts
import {
  Bool,
  Field,
  Float32,
  Float64,
  FixedSizeList,
  Int32,
  Schema,
  Utf8,
} from "apache-arrow";
import type { EmbeddingSpace } from "./embedding-provider";

const string = (name: string) => new Field(name, new Utf8(), false);
const integer = (name: string) => new Field(name, new Int32(), false);
const number = (name: string) => new Field(name, new Float64(), false);
const boolean = (name: string) => new Field(name, new Bool(), false);

// Embeddings intentionally live outside SCHEMAS. Core JSONL imports create
// only their three ordinary tables; this optional table appears on the first
// successful embedding batch.
export const EVENT_VECTORS_TABLE = "event_vectors";
export const EMBEDDING_MODEL = "bge-m3";
export const EMBEDDING_REVISION =
  "7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab";
export const EMBEDDING_SPACE_ID = "ollama-bge-m3-790764642607-1024-cosine-text-v1";
export const EMBEDDING_DIMENSION = 1_024;
export const EMBEDDING_TEXT_LIMIT = 2_000;
export const EMBEDDING_TEXT_POLICY = "event.text.slice(0,2000)@v1";

export type EventVectorSpaceContract = EmbeddingSpace;

export const ACTIVE_EVENT_VECTOR_CONTRACT: EventVectorSpaceContract = Object.freeze({
  id: EMBEDDING_SPACE_ID,
  provider: "ollama",
  model: EMBEDDING_MODEL,
  revision: EMBEDDING_REVISION,
  dimension: EMBEDDING_DIMENSION,
  distance: "cosine",
  textPolicy: EMBEDDING_TEXT_POLICY,
});

export const SCHEMAS = {
  events: new Schema([
    string("id"),
    string("event_uuid"),
    integer("block_index"),
    string("session_id"),
    string("parent_uuid"),
    string("timestamp"),
    string("project"),
    string("envelope_type"),
    string("block_type"),
    string("semantic_role"),
    string("tool_name"),
    string("tool_use_id"),
    boolean("is_error"),
    string("text"),
    string("text_hash"),
    string("source"),
  ]),
  event_sources: new Schema([
    string("id"),
    string("event_id"),
    string("source"),
    string("file_path"),
    string("file_hash"),
    integer("source_line"),
    string("observed_text_hash"),
  ]),
  source_files: new Schema([
    string("id"),
    string("source"),
    string("path"),
    number("size"),
    number("mtime_ms"),
    string("sha256"),
    string("state"),
    string("imported_at"),
    integer("parsed_records"),
    integer("inserted_events"),
    integer("duplicate_events"),
    integer("corrupt_lines"),
  ]),
} as const;

export function eventVectorSchema(space: EventVectorSpaceContract) {
  return new Schema([
    string("event_id"),
    string("source"),
    string("project"),
    string("session_id"),
    string("timestamp"),
    string("text_hash"),
    string("model"),
    integer("dimension"),
    string("embedded_at"),
    new Field(
      "vector",
      new FixedSizeList(
        space.dimension,
        new Field("item", new Float32(), false),
      ),
      false,
    ),
  ], new Map([
    ["embedding_space_id", space.id],
    ["embedding_provider", space.provider],
    ["embedding_model", space.model],
    ["embedding_revision", space.revision],
    ["embedding_dimension", String(space.dimension)],
    ["embedding_distance", space.distance],
    ["embedding_text_policy", space.textPolicy],
  ]));
}

export const EVENT_VECTOR_SCHEMA = eventVectorSchema(ACTIVE_EVENT_VECTOR_CONTRACT);

export function schemaDescription() {
  return Object.fromEntries(Object.entries(SCHEMAS).map(([table, schema]) => [
    table,
    schema.fields.map((field) => `${field.name}: ${field.type}`),
  ]));
}
```

(`schemaDescription()` is what backs the `bun src/cli.ts schema` command — it never touches LanceDB, just reflects the Arrow `Schema` objects above back as strings.)

The vector column is `FixedSizeList(1024, Float32)` — a 1,024-dimension `bge-m3` embedding — and the **entire embedding contract** (space id, provider, model, revision hash, dimension, distance metric, text-slicing policy) is written into the Arrow schema's key/value **metadata map**, not just into application config. That metadata is what makes a vector store self-describing and lets `assertEventVectorContract` (below) refuse to write into a table built for a different model.

### 3.2 Plain-store table creation + generic insert-if-new

`src/database.plain.ts:36-79`:

```ts
/** The always-on typed JSONL store: canonical rows, provenance, and manifest. */
export class PlainDatabase {
  private constructor(
    readonly directory: string,
    readonly connection: Connection,
  ) {}

  static async open(directory: string) {
    return new PlainDatabase(directory, await lancedb.connect(directory));
  }

  async create() {
    const names = new Set(await this.connection.tableNames());
    for (const [name, schema] of Object.entries(SCHEMAS)) {
      if (!names.has(name)) await this.connection.createEmptyTable(name, schema);
    }
    return (await this.connection.tableNames()).sort();
  }

  async tableNames() {
    return (await this.connection.tableNames()).sort();
  }

  async table(name: keyof typeof SCHEMAS): Promise<Table> {
    await this.create();
    return this.connection.openTable(name);
  }

  events() { return new EventRepository(this); }
  occurrences() { return new EventSourceRepository(this); }
  files() { return new SourceFileRepository(this); }
}

async function insertNew<T extends { id: string }>(table: Table, rows: T[]) {
  const firstById = new Map<string, T>();
  for (const row of rows) {
    if (!firstById.has(row.id)) firstById.set(row.id, row);
  }
  const unique = [...firstById.values()];
  if (!unique.length) return { inserted: 0, duplicates: 0 };
  const result = await table.mergeInsert("id").whenNotMatchedInsertAll().execute(unique);
  const inserted = result.numInsertedRows;
  return { inserted, duplicates: rows.length - inserted };
}
```

`table()` lazily calls `create()` on every access — every table read/write is guaranteed to at least have an empty table to open, with zero explicit "did you run migrations" step.

### 3.3 Vector-store table creation, and the contract check that guards it

`src/database.vector.ts` (nearly the whole module — `metadata()`/`metadataForEventIds()`/`rowsForEventIds()` are the only methods elided here since they're quoted where they're used, in §4 and §5):

```ts
import * as lancedb from "@lancedb/lancedb";
import type { Connection, Table } from "@lancedb/lancedb";
import { DataType, Precision } from "apache-arrow";
import { stat } from "node:fs/promises";
import {
  ACTIVE_EVENT_VECTOR_CONTRACT,
  EVENT_VECTORS_TABLE,
  eventVectorSchema,
  type EventVectorSpaceContract,
} from "./schemas";
import { sql } from "./database.plain";
import type { EventVectorMetadata, EventVectorRow } from "./types";

/**
 * The optional semantic store. Read methods do not connect when its directory
 * does not exist, keeping normal import/status work vector-free.
 */
export class VectorDatabase {
  private connectionPromise: Promise<Connection> | undefined;

  constructor(
    readonly directory: string,
    readonly space: EventVectorSpaceContract = ACTIVE_EVENT_VECTOR_CONTRACT,
  ) {}

  async exists() {
    try {
      return (await stat(this.directory)).isDirectory();
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") return false;
      throw error;
    }
  }

  async connectionIfPresent(): Promise<Connection | undefined> {
    if (!(await this.exists())) return undefined;
    return this.connectionForWrite();
  }

  async connectionForWrite(): Promise<Connection> {
    this.connectionPromise ??= lancedb.connect(this.directory);
    return this.connectionPromise;
  }

  async tableNames() {
    const connection = await this.connectionIfPresent();
    return connection ? (await connection.tableNames()).sort() : [];
  }

  eventVectors() { return new EventVectorRepository(this); }
}

function vectorContractError(reason: string) {
  return new Error(
    `${EVENT_VECTORS_TABLE} contract mismatch (${reason}); rebuild ${EVENT_VECTORS_TABLE} before embedding`,
  );
}

async function assertEventVectorContract(table: Table, space: EventVectorSpaceContract) {
  const schema = await table.schema();
  const expectedMetadata = {
    embedding_space_id: space.id,
    embedding_provider: space.provider,
    embedding_model: space.model,
    embedding_revision: space.revision,
    embedding_dimension: String(space.dimension),
    embedding_distance: space.distance,
    embedding_text_policy: space.textPolicy,
  };
  for (const [name, expected] of Object.entries(expectedMetadata)) {
    if (schema.metadata.get(name) !== expected) {
      throw vectorContractError(`${name} is not ${JSON.stringify(expected)}`);
    }
  }

  const expectedSchema = eventVectorSchema(space);
  if (schema.fields.length !== expectedSchema.fields.length) {
    throw vectorContractError("field count differs from the active embedding schema");
  }
  for (const [index, expected] of expectedSchema.fields.entries()) {
    const actual = schema.fields[index];
    if (!actual || actual.name !== expected.name ||
      actual.nullable !== expected.nullable ||
      actual.type.toString() !== expected.type.toString()) {
      throw vectorContractError(`field ${expected.name} differs from the active embedding schema`);
    }
  }

  const vector = schema.fields.find((field) => field.name === "vector");
  if (!vector || !DataType.isFixedSizeList(vector.type)) {
    throw vectorContractError("vector is not FixedSizeList<Float32>");
  }
  if (vector.type.listSize !== space.dimension) {
    throw vectorContractError(`vector dimension is not ${space.dimension}`);
  }
  if (!DataType.isFloat(vector.type.valueType) ||
    vector.type.valueType.precision !== Precision.SINGLE) {
    throw vectorContractError("vector values are not Float32");
  }
}

export class EventVectorRepository {
  constructor(private readonly db: VectorDatabase) {}

  private async existingTable(): Promise<Table | undefined> {
    const connection = await this.db.connectionIfPresent();
    if (!connection || !(await connection.tableNames()).includes(EVENT_VECTORS_TABLE)) return undefined;
    const table = await connection.openTable(EVENT_VECTORS_TABLE);
    await assertEventVectorContract(table, this.db.space);
    return table;
  }

  private async writableTable(): Promise<Table> {
    const existing = await this.existingTable();
    if (existing) return existing;

    const table = await (await this.db.connectionForWrite()).createEmptyTable(
      EVENT_VECTORS_TABLE,
      eventVectorSchema(this.db.space),
      { mode: "create", existOk: true },
    );
    await assertEventVectorContract(table, this.db.space);
    return table;
  }

  async count() {
    const table = await this.existingTable();
    return table ? table.countRows() : 0;
  }

  // ... metadata()/metadataForEventIds()/rowsForEventIds() — see §5 & §4 ...

  async upsert(rows: EventVectorRow[]) {
    const unique = [...new Map(rows.map((row) => [row.event_id, row])).values()];
    if (!unique.length) return 0;
    await (await this.writableTable())
      .mergeInsert("event_id")
      .whenMatchedUpdateAll()
      .whenNotMatchedInsertAll()
      .execute(unique);
    return unique.length;
  }
}
```

Key points for this section:
- **Table creation is lazy and on-write only.** `VectorDatabase.exists()` stats the directory; nothing connects to LanceDB until an explicit embed/read call. `writableTable()` calls `createEmptyTable(..., { mode: "create", existOk: true })` only the first time a vector batch is actually upserted.
- **No ANN index is ever built.** There is no `createIndex()` / IVF_PQ call anywhere in the codebase (verified: `grep -rn "createIndex\|IVF_PQ\|\.index(" src/` returns nothing). Every vector-table read in this repo is a **scalar** `.query().where("event_id IN (...)")` lookup by primary key, never a `.search(vector)` similarity query — see the Reality Check in §5.
- **Insert path is `mergeInsert` (upsert), not `add`.** Both the plain store's `insertNew()` (§3.2, `whenNotMatchedInsertAll` only — pure dedupe-on-id) and the vector store's `upsert()` (`whenMatchedUpdateAll().whenNotMatchedInsertAll()` — replace on `event_id` match) use LanceDB's `mergeInsert` API keyed by a single stable string primary key. This is the mechanical foundation of the idempotency story in §6.
- **`Database`** (`src/database.ts:88-105`) is a thin container pairing one `PlainDatabase` with one `VectorDatabase`, with a same-directory guard (`assertSeparateDirectories`, `src/database.ts:68-78`) that resolves symlinks before comparing so `foo`, `foo/.`, and a symlinked alias can't silently collide the two stores.

---

## 4. The embedding call — model, batching, incremental/resumable

### 4.1 The provider abstraction and validated deployments

`src/embedding-provider.ts:226-247` — one canonical shape every transport adapts to:

```ts
export type EmbeddingProvider = {
  readonly space: EmbeddingSpace;
  embed(texts: string[]): Promise<number[][]>;
};

/**
 * Adapts any transport response to the one canonical provider interface.
 * Shape conversion belongs here; count, dimension, and numeric validation stay
 * centralized in the embedding pipeline.
 */
export function wrapEmbeddingProvider(options: Readonly<{
  space: EmbeddingSpace;
  request: (texts: string[]) => Promise<unknown>;
  toVectors: (response: unknown) => number[][];
}>): EmbeddingProvider {
  return Object.freeze({
    space: options.space,
    async embed(texts: string[]) {
      return options.toVectors(await options.request(texts));
    },
  });
}
```

Three deployments are wired in today — `src/embedding-provider.ts:183-224`:

```ts
export const EMBEDDING_DEPLOYMENTS: Readonly<
  Record<"m5-ollama" | "dual-4090" | "cloudflare", EmbeddingDeployment>
> = Object.freeze({
  "m5-ollama": defineEmbeddingDeployment({
    id: "m5-ollama",
    label: "M5 · Ollama",
    location: "local",
    hardware: "apple-m5",
    config: {
      kind: "ollama",
      endpoint: { baseUrlEnv: "M5_OLLAMA_URL", defaultBaseUrl: "http://127.0.0.1:11434" },
      space: ACTIVE_EMBEDDING_SPACE,
    },
  }),
  "dual-4090": defineEmbeddingDeployment({
    id: "dual-4090",
    label: "2× RTX 4090 · Ollama pool",
    location: "lan",
    hardware: "2x-nvidia-rtx-4090",
    config: { kind: "ollama-pool", baseUrlsEnv: "DUAL_4090_OLLAMA_URLS", space: DUAL_4090_EMBEDDING_SPACE },
  }),
  cloudflare: defineEmbeddingDeployment({
    id: "cloudflare",
    label: "Cloudflare Workers AI",
    location: "cloud",
    hardware: "cloudflare-managed",
    config: {
      kind: "cloudflare-workers-ai",
      accountIdEnv: "CLOUDFLARE_ACCOUNT_ID",
      apiTokenEnv: "CLOUDFLARE_API_TOKEN",
      apiBaseUrlEnv: "CLOUDFLARE_AI_BASE_URL",
      space: CLOUDFLARE_EMBEDDING_SPACE,
    },
  }),
});
```

All three point at the same model family, `bge-m3`, 1,024 dimensions, cosine distance — `src/embedding-provider.ts:67-90`:

```ts
export const ACTIVE_EMBEDDING_SPACE = defineEmbeddingSpace({
  id: EMBEDDING_SPACE_ID,
  provider: "ollama",
  model: EMBEDDING_MODEL,
  revision: EMBEDDING_REVISION,
  dimension: EMBEDDING_DIMENSION,
  distance: "cosine",
  textPolicy: EMBEDDING_TEXT_POLICY,
});

/** Verified identical to M5 Ollama; deployment hardware is not a vector space. */
export const DUAL_4090_EMBEDDING_SPACE = ACTIVE_EMBEDDING_SPACE;

export const CLOUDFLARE_EMBEDDING_SPACE = defineEmbeddingSpace({
  id: "cloudflare-bge-m3-8bddd3ea514a-1024-cosine-text-v1",
  provider: "cloudflare-workers-ai",
  model: "@cf/baai/bge-m3",
  // Workers AI does not expose a model digest. This is the Float32 SHA-256 of
  // CLOUDFLARE_REVISION_PROBE_TEXT, stable across repeated independent probes.
  revision: "probe-f32-sha256:8bddd3ea514a586ab90e4568f0664ae82b97672184c2e875c7d1d35931c911a6",
  dimension: EMBEDDING_DIMENSION,
  distance: "cosine",
  textPolicy: EMBEDDING_TEXT_POLICY,
});
```

Note Cloudflare gets its **own separate embedding-space id** even though it claims to run the same model — because Workers AI exposes no model digest to pin against, so the code pins a fingerprint of a fixed probe string instead (see 4.3).

### 4.2 Ollama transport — single endpoint and a load-balanced pool with failover

`src/embedding-provider.ts:314-358`:

```ts
async function requestOllamaEmbeddings(
  url: string,
  space: EmbeddingSpace,
  texts: string[],
  timeoutMs: number,
) {
  const response = await fetch(`${url.replace(/\/$/, "")}/api/embed`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ model: space.model, input: texts }),
    signal: AbortSignal.timeout(timeoutMs),
  });
  if (!response.ok) {
    const body = (await response.text()).slice(0, 500);
    throw new Error(`Ollama /api/embed failed at ${url} (${response.status}): ${body}`);
  }
  const body = await response.json() as { embeddings?: unknown };
  if (!Array.isArray(body.embeddings)) {
    throw new EmbeddingValidationError(
      `Ollama /api/embed response from ${url} has no embeddings array`,
    );
  }
  return body.embeddings as number[][];
}

export class OllamaEmbeddingProvider implements EmbeddingProvider {
  readonly url: string;
  readonly space = ACTIVE_EMBEDDING_SPACE;
  readonly timeoutMs: number;
  readonly #verified = new Map<string, Promise<void>>();

  constructor(options: OllamaEmbeddingProviderOptions = {}) {
    this.url = options.url ??
      process.env.M5_OLLAMA_URL ??
      process.env.OLLAMA_URL ??
      "http://127.0.0.1:11434";
    this.timeoutMs = options.timeoutMs ?? 120_000;
  }

  async embed(texts: string[]) {
    if (!texts.length) return [];
    await ensureOllamaEndpoint(this.#verified, this.url, this.space, this.timeoutMs);
    return requestOllamaEmbeddings(this.url, this.space, texts, this.timeoutMs);
  }
}
```

Before the first real batch, `ensureOllamaEndpoint` (`src/embedding-provider.ts:295-312`, not quoted — it just memoizes the promise below per URL) verifies the server actually has the pinned model+digest installed via `verifyOllamaEndpoint` — `src/embedding-provider.ts:266-293`:

```ts
async function verifyOllamaEndpoint(
  url: string,
  space: EmbeddingSpace,
  timeoutMs: number,
) {
  const response = await fetch(`${url.replace(/\/$/, "")}/api/tags`, {
    signal: AbortSignal.timeout(timeoutMs),
  });
  if (!response.ok) {
    throw new Error(`Ollama /api/tags failed at ${url} (${response.status})`);
  }
  const body = await response.json() as {
    models?: Array<{ name?: unknown; model?: unknown; digest?: unknown }>;
  };
  const names = new Set([space.model, `${space.model}:latest`]);
  const model = body.models?.find((item) =>
    (typeof item.name === "string" && names.has(item.name)) ||
    (typeof item.model === "string" && names.has(item.model))
  );
  if (!model) throw new Error(`Ollama model ${space.model} is not installed at ${url}`);
  if (space.revision !== "unversioned" && model.digest !== space.revision) {
    throw new Error(
      `Ollama model revision mismatch at ${url}: expected ${space.revision}, got ${
        typeof model.digest === "string" ? model.digest : "missing"
      }`,
    );
  }
}
```

The pool provider (`dual-4090`) shards one batch across N endpoints, then fails over within a shard by rotating through the remaining URLs — `src/embedding-provider.ts:380-427`:

```ts
export class OllamaPoolEmbeddingProvider implements EmbeddingProvider {
  readonly urls: readonly string[];
  readonly space = DUAL_4090_EMBEDDING_SPACE;
  readonly timeoutMs: number;
  #cursor = 0;
  readonly #verified = new Map<string, Promise<void>>();

  async embed(texts: string[]) {
    if (!texts.length) return [];
    if (texts.length === 1) {
      const start = this.#cursor++ % this.urls.length;
      return this.#embedShard(texts, start);
    }

    const shardCount = Math.min(texts.length, this.urls.length);
    const baseSize = Math.floor(texts.length / shardCount);
    const largerShardCount = texts.length % shardCount;
    let start = 0;
    const shards = Array.from({ length: shardCount }, (_, endpointIndex) => {
      const size = baseSize + (endpointIndex < largerShardCount ? 1 : 0);
      const shard = { endpointIndex, start, texts: texts.slice(start, start + size) };
      start += size;
      return shard;
    });

    const completed = await Promise.all(shards.map(async (shard) => ({
      start: shard.start,
      vectors: await this.#embedShard(shard.texts, shard.endpointIndex),
    })));
    const vectors = new Array<number[]>(texts.length);
    for (const shard of completed) {
      for (let index = 0; index < shard.vectors.length; index++) {
        vectors[shard.start + index] = shard.vectors[index]!;
      }
    }
    return vectors;
  }

  async #embedShard(texts: string[], primaryEndpointIndex: number) {
    const failures: string[] = [];
    for (let offset = 0; offset < this.urls.length; offset++) {
      const url = this.urls[(primaryEndpointIndex + offset) % this.urls.length]!;
      try {
        await ensureOllamaEndpoint(this.#verified, url, this.space, this.timeoutMs);
        return await requestOllamaEmbeddings(url, this.space, texts, this.timeoutMs);
      } catch (error) {
        failures.push(`${url}: ${error instanceof Error ? error.message : String(error)}`);
      }
    }
    throw new Error(`all Ollama pool endpoints failed: ${failures.join(" | ")}`);
  }
}
```

### 4.3 Cloudflare Workers AI transport — pinning a model with no digest

`src/embedding-providers/cloudflare.ts:99-176` (the class; helper functions `float32Fingerprint`/`verifyRevisionProbe`/`redactRemoteMessage` are quoted in full in §7):

```ts
/**
 * Cloudflare Workers AI native REST adapter.
 *
 * A deterministic single-text probe runs before the first user batch. Workers
 * AI exposes no model digest, so the adapter refuses to write into the pinned
 * vector space if the managed model output changes.
 */
export class CloudflareWorkersAIProvider implements EmbeddingProvider {
  readonly space: EmbeddingSpace;
  readonly accountId: string;
  readonly apiBaseUrl: string;
  readonly timeoutMs: number;
  readonly #apiToken: string;
  readonly #fetcher: typeof globalThis.fetch;
  #verification: Promise<void> | undefined;

  constructor(options: CloudflareWorkersAIProviderOptions = {}) {
    this.space = defineEmbeddingSpace(options.space ?? CLOUDFLARE_EMBEDDING_SPACE);
    if (this.space.provider !== "cloudflare-workers-ai") {
      throw new Error("Cloudflare Workers AI space provider must be cloudflare-workers-ai");
    }
    if (!this.space.revision.startsWith(REVISION_PREFIX)) {
      throw new Error(
        `Cloudflare Workers AI space ${this.space.id} must use a pinned ${REVISION_PREFIX} revision`,
      );
    }
    this.accountId = required(options.accountId ?? process.env.CLOUDFLARE_ACCOUNT_ID, "CLOUDFLARE_ACCOUNT_ID");
    this.#apiToken = required(options.apiToken ?? process.env.CLOUDFLARE_API_TOKEN, "CLOUDFLARE_API_TOKEN");
    this.apiBaseUrl = (options.apiBaseUrl ?? process.env.CLOUDFLARE_AI_BASE_URL ?? DEFAULT_API_BASE_URL).replace(/\/$/, "");
    this.timeoutMs = options.timeoutMs ?? 120_000;
    this.#fetcher = options.fetcher ?? globalThis.fetch;
  }

  async #request(texts: string[]) {
    const response = await this.#fetcher(
      `${this.apiBaseUrl}/accounts/${encodeURIComponent(this.accountId)}/ai/run/${this.space.model}`,
      {
        method: "POST",
        headers: { authorization: `Bearer ${this.#apiToken}`, "content-type": "application/json" },
        body: JSON.stringify({ text: texts }),
        signal: AbortSignal.timeout(this.timeoutMs),
      },
    );
    if (!response.ok) {
      const detail = await cloudflareErrorDetail(response, this.#apiToken);
      throw new Error(`Cloudflare Workers AI failed (${response.status}): ${detail}`);
    }
    return vectorsFromResponse(await response.json(), texts.length);
  }

  async #ensureRevision() {
    this.#verification ??= this.#request([CLOUDFLARE_REVISION_PROBE_TEXT])
      .then((vectors) => verifyRevisionProbe(vectors[0]!, this.space));
    try {
      await this.#verification;
    } catch (error) {
      this.#verification = undefined;
      throw error;
    }
  }

  async embed(texts: string[]) {
    if (!texts.length) return [];
    await this.#ensureRevision();
    return this.#request(texts);
  }
}
```

`float32Fingerprint` (§7) turns the probe response vector into a SHA-256 over its exact IEEE-754 little-endian bytes — the closest thing to a "digest" a black-box hosted model can offer. If Cloudflare silently changes the model backing `@cf/baai/bge-m3`, the fingerprint of the fixed probe text changes and `verifyRevisionProbe` throws before any real text is embedded into the pinned space.

### 4.4 `embedPending` — the batching / paging / resumability pipeline

This is the actual orchestrator, in `src/embeddings.ts`. Constants first (`src/embeddings.ts:63-67`):

```ts
export const EMBEDDING_MIN_CHARACTERS = 80;
export const DEFAULT_EMBED_BATCH_SIZE = 8;
export const DEFAULT_EMBED_LIMIT = 300;
export const EMBEDDING_PAGE_SIZE = 256;
export const EMBEDDING_ID_CHUNK_SIZE = 256;
```

Vector validation before anything is ever persisted — `src/embeddings.ts:215-251`:

```ts
export function validateEmbeddingVectors(
  value: unknown,
  expectedCount: number,
  dimension: number,
) {
  if (!Array.isArray(value) || value.length !== expectedCount) {
    throw new EmbeddingValidationError(
      `embedding response count mismatch: expected ${expectedCount}, got ${
        Array.isArray(value) ? value.length : "non-array"
      }`,
    );
  }

  return value.map((raw, index) => {
    if (!Array.isArray(raw) && !ArrayBuffer.isView(raw)) {
      throw new EmbeddingValidationError(`embedding ${index} is not an array`);
    }
    const numbers = Array.from(raw as ArrayLike<unknown>);
    if (numbers.length !== dimension) {
      throw new EmbeddingValidationError(
        `embedding ${index} has dimension ${numbers.length}; expected ${dimension}`,
      );
    }
    if (numbers.some((item) => typeof item !== "number" || !Number.isFinite(item))) {
      throw new EmbeddingValidationError(`embedding ${index} contains a non-finite value`);
    }
    const vector = Float32Array.from(numbers as number[]);
    if ([...vector].some((item) => !Number.isFinite(item))) {
      throw new EmbeddingValidationError(`embedding ${index} overflows Float32`);
    }
    const normSquared = vector.reduce((sum, item) => sum + item * item, 0);
    if (!Number.isFinite(normSquared) || normSquared <= 0) {
      throw new EmbeddingValidationError(`embedding ${index} has zero norm`);
    }
    return vector;
  });
}

async function embedBatch(
  provider: EmbeddingProvider,
  texts: string[],
  retries: number,
  retryDelayMs: number,
  sleep: (milliseconds: number) => Promise<void>,
) {
  for (let attempt = 0; ; attempt++) {
    try {
      return validateEmbeddingVectors(
        await provider.embed(texts),
        texts.length,
        provider.space.dimension,
      );
    } catch (error) {
      if (error instanceof EmbeddingValidationError || attempt >= retries) throw error;
      await sleep(retryDelayMs * 2 ** attempt);
    }
  }
}
```

Malformed-shape errors (`EmbeddingValidationError`) are **never retried** — only transport-level failures get exponential backoff (`retryDelayMs * 2 ** attempt`). See §8 for why that distinction matters.

The full orchestrator — `src/embeddings.ts:323-474`:

```ts
export async function embedPending(
  plain: PlainDatabase,
  vectorDatabase: VectorDatabase,
  provider: EmbeddingProvider,
  options: EmbedOptions = {},
): Promise<EmbedReport> {
  assertProviderContract(provider, vectorDatabase);
  const space = provider.space;
  const release = await acquireEmbeddingLock(vectorDatabase);
  try {
    const maxEvents = positiveInteger(options.maxEvents ?? DEFAULT_EMBED_LIMIT, "maxEvents");
    const batchSize = positiveInteger(options.batchSize ?? DEFAULT_EMBED_BATCH_SIZE, "batchSize");
    const retries = nonNegativeInteger(options.retries ?? 2, "retries");
    const retryDelayMs = nonNegativeInteger(options.retryDelayMs ?? 500, "retryDelayMs");
    const sleep = options.sleep ?? delay;
    const project = options.project?.trim() || undefined;
    const folder = options.folder ? resolve(options.folder) : undefined;
    const dateRange = embeddingDateRange(options.since, options.until);

    const pageSize = Math.min(maxEvents, EMBEDDING_PAGE_SIZE);
    const selected: Candidate[] = [];
    let scanned = 0;
    let eligible = 0;
    let upToDate = 0;
    let moreMayRemain = false;

    const folderEventIds = folder
      ? await plain.occurrences().eventIdsInFolder(options.source ?? "", folder)
      : undefined;
    const eventIdChunks: Array<string[] | undefined> = folderEventIds
      ? chunks(folderEventIds, EMBEDDING_ID_CHUNK_SIZE)
      : [undefined];

    // Page candidates from LanceDB and fetch vector metadata only for IDs in
    // the current page. `--limit 1` therefore reads one candidate instead of
    // materializing the full corpus and vector table in JavaScript. Folder
    // provenance becomes bounded event-ID chunks before touching vectors.
    scanRoles: for (const role of EMBEDDING_ROLES) {
      for (const eventIds of eventIdChunks) {
        let offset = 0;
        for (;;) {
          const page = await plain.events().embeddingPage({
            source: options.source,
            project,
            ...dateRange,
            eventIds,
            semanticRole: role,
            minimumCharacters: EMBEDDING_MIN_CHARACTERS,
            offset,
            limit: pageSize,
          });
          if (!page.length) break;
          offset += page.length;
          scanned += page.length;
          const existing = await vectorDatabase.eventVectors().metadataForEventIds(
            page.map((event) => event.id),
          );

          for (const event of page) {
            // The SQL predicate handles the common path. Keep this semantic
            // guard as a defense for hand-written rows and future normalizers.
            if (!isEmbeddableEvent(event)) continue;
            eligible++;
            const text = embeddingText(event.text);
            const textHash = sha256(text);
            const vector = existing.get(event.id);
            if (vector?.text_hash === textHash &&
              vector.model === space.model &&
              vector.dimension === space.dimension &&
              vector.source === event.source &&
              vector.project === event.project &&
              vector.session_id === event.session_id &&
              vector.timestamp === event.timestamp) {
              upToDate++;
              continue;
            }
            selected.push({ event, text, textHash });
            if (selected.length === maxEvents) {
              moreMayRemain = true;
              break scanRoles;
            }
          }
          if (page.length < pageSize) break;
        }
      }
    }

    let embedded = 0;
    const reportProgress = (status: EmbedProgress["status"]) => options.onProgress?.({
      phase: "embed", status, current: embedded, total: selected.length,
      scanned, eligible, up_to_date: upToDate, selected: selected.length,
      embedded, more_may_remain: moreMayRemain,
    });
    reportProgress("start");

    for (let index = 0; index < selected.length; index += batchSize) {
      const batch = selected.slice(index, index + batchSize);
      const vectors = await embedBatch(
        provider, batch.map((candidate) => candidate.text), retries, retryDelayMs, sleep,
      );
      const rows: EventVectorRow[] = batch.map((candidate, offset) => ({
        event_id: candidate.event.id,
        source: candidate.event.source,
        project: candidate.event.project,
        session_id: candidate.event.session_id,
        timestamp: candidate.event.timestamp,
        text_hash: candidate.textHash,
        model: space.model,
        dimension: space.dimension,
        embedded_at: new Date().toISOString(),
        vector: vectors[offset]!,
      }));
      embedded += await vectorDatabase.eventVectors().upsert(rows);
      reportProgress("progress");
    }

    reportProgress("complete");
    return {
      embedding_space_id: space.id, provider: space.provider, model: space.model,
      revision: space.revision, dimension: space.dimension, text_policy: space.textPolicy,
      source: options.source || undefined, project, folder,
      since: options.since || undefined, until: options.until || undefined,
      scanned, eligible, up_to_date: upToDate, selected: selected.length, embedded,
      more_may_remain: moreMayRemain, vectors: await vectorDatabase.eventVectors().count(),
    };
  } finally {
    await release();
  }
}
```

**How incrementality actually works:** for every scanned candidate, the code compares the vector row that already exists for that `event_id` (`existing.get(event.id)`) against the row it would write today — `text_hash` (hash of the exact 2,000-char sliced text sent to the provider), `model`, `dimension`, and the copied scope columns (`source`, `project`, `session_id`, `timestamp`). If **all** match, the candidate is `up_to_date` and is skipped without ever calling the provider. Only a genuine content or scope change re-embeds a row — proven by `tests/embeddings.test.ts:286-314` (§6).

**How resumability works:** each batch of `batchSize` (default 8) candidates is embedded and `upsert()`-ed to the vector table *before* the loop moves to the next batch, so a crash or thrown error mid-run leaves every already-completed batch durable. `tests/embeddings.test.ts:355-382` proves this directly:

```ts
  test("persists completed vector batches and resumes from the plain store after failure", async () => {
    const { plain, vector: vectors } = await temporaryStores();
    await plain.events().insert([
      event("first#0", "human_intent", text("a"), "2026-08-31T10:00:00.000Z"),
      event("second#0", "human_intent", text("b"), "2026-08-31T09:00:00.000Z"),
      event("third#0", "human_intent", text("c"), "2026-08-31T08:00:00.000Z"),
    ]);
    let calls = 0;
    const unreliable = provider(async (inputs) => {
      calls++;
      if (calls === 2) throw new Error("temporary Ollama outage");
      return inputs.map((_input, index) => vector(index + calls));
    });

    await expect(embedPending(plain, vectors, unreliable, {
      maxEvents: 3, batchSize: 2, retries: 0,
    })).rejects.toThrow("temporary Ollama outage");
    expect(await vectors.eventVectors().count()).toBe(2);
    expect(await plain.events().count()).toBe(3);

    const resumed = await embedPending(plain, vectors, provider(async (inputs) =>
      inputs.map((_input, index) => vector(index + 10))
    ), { maxEvents: 3, batchSize: 2 });
    expect(resumed).toMatchObject({ up_to_date: 2, selected: 1, embedded: 1, vectors: 3 });
    expect(await plain.events().count()).toBe(3);
  });
```

Batch 1 (2 events) commits fine; batch 2 (the 3rd event) throws on the provider call and the whole `embedPending` rejects — but the 2 already-committed vectors survive. The very next call, with a working provider, sees those 2 as `up_to_date` and embeds only the 1 remaining row.

**Single-writer lock.** `embedPending` also takes an exclusive file lock on the vector store directory for its whole duration, so two concurrent `embed run` invocations against the same store can't race — `src/embeddings.ts:274-321`:

```ts
async function acquireEmbeddingLock(vectorDatabase: VectorDatabase) {
  const lockPath = `${vectorDatabase.directory}.${EVENT_VECTORS_TABLE}.lock`;
  await mkdir(dirname(lockPath), { recursive: true });

  // Write a complete unique candidate first, then atomically hard-link it to
  // the stable lock path. A contender can therefore never observe a created
  // lock with missing ownership data.
  const token = randomUUID();
  const candidatePath = `${lockPath}.${token}.candidate`;
  const owner = { token, pid: process.pid, started_at: new Date().toISOString() };
  await writeFile(candidatePath, JSON.stringify(owner), { flag: "wx" });
  try {
    await link(candidatePath, lockPath);
  } catch (error) {
    await unlink(candidatePath).catch(() => {});
    if ((error as NodeJS.ErrnoException).code !== "EEXIST") throw error;
    const activeOwner = await readLockOwner(lockPath);
    const ownerDescription = Number.isInteger(activeOwner?.pid) ? ` (pid ${activeOwner!.pid})` : "";
    throw new Error(
      `${EVENT_VECTORS_TABLE} writer is already active for ${vectorDatabase.directory}${ownerDescription}; wait for it to finish`,
    );
  }
  await unlink(candidatePath).catch(() => {});

  return async () => {
    // Do not delete a lock replaced by another owner after a failed/crashed
    // process. The random token makes release ownership explicit.
    if ((await readLockOwner(lockPath))?.token === token) {
      await unlink(lockPath).catch(() => {});
    }
  };
}
```

Write-candidate-then-hard-link is the classic POSIX "atomic lock acquire" idiom: `link()` fails with `EEXIST` if the destination already exists and is otherwise atomic, so no window exists where a competitor could observe a lock file with incomplete owner JSON.

---

## 5. Search implementation (lexical / vector / hybrid, RRF or weighted fusion)

### Reality check — **this feature does not exist in the codebase.**

I looked for it directly and came up empty:

```
$ grep -rn -i "rrf\|reciprocal\|fusion\|hybrid\|rerank\|lexical\|fts\|full.text\|bm25" --include="*.ts" src/ ui/src/
(no matches)

$ grep -rn "\.search(\|vectorSearch\|nearestTo" --include="*.ts" src/
(no matches — LanceDB's `.search(queryVector)` ANN API is never called anywhere)

$ grep -n "pathname ===" src/server.ts
# every route registered — no /api/search, no query-text parameter anywhere
727:  const relative = pathname === "/"
745:      if (... url.pathname === "/" || url.pathname === "/admin" ...
755:      if (... url.pathname === "/api/status")
758:      if (... url.pathname === "/api/events")
768:      if (... url.pathname === "/api/events/facets")
773:      if (... url.pathname === "/api/events/live")
782:      if (... url.pathname === "/api/history")
785:      if (... url.pathname === "/api/history/session")
788:      if (... url.pathname === "/api/vectors/visualize")
791:      if (... url.pathname === "/api/import/plan")
800:      if (... url.pathname === "/api/import/intake")
804:      if (... url.pathname === "/api/import")
815:      if (... url.pathname === "/api/jobs/import")
819:      if (... url.pathname === "/api/jobs")
```

The README is explicit that this is by design, not an oversight — the product is a **history browser** with an optional **PCA visualization** of embeddings, not a retrieval/ranking engine:

> - **Read work as history.** Browse by day, week, month, source, project, folder, or session instead of opening thousands of JSONL files.
> - **Embed later.** Plain rows and vector indexes live in separate LanceDB stores. Import never contacts an embedding service.
> — `README.md:35-40`

> - **Vector map** — scoped 2D or 3D PCA projection across selected vector spaces.
> — `README.md:152`

`docs/vector-visualization-plugins.md:1-7` confirms the vector feature is explicitly a *rendering* contract, not a query/ranking one:

> History visualizations are replaceable React components. The host keeps vector spaces, filters, loading, errors, selection, and evidence navigation honest; a plugin only draws the already-projected points and reports a selected `event_id`.

So there is no `RRF`, no weighted-fusion score, no BM25/FTS index, and no `nearestTo`/ANN call to show. What follows instead is the actual code for **the two mechanisms that are the closest functional analogs**: (a) exact chronological retrieval with filters, and (b) unsupervised dimensionality reduction of already-computed embeddings for a scatter-plot "map." Neither ranks results against a user's query text.

### 5.1 "Latest N" retrieval — a bounded min-heap over a streamed scalar scan (`src/database.plain.ts:131-213`)

This is what powers the event browser (`/api/events`) — filtered by `source`/`project`/`folder`/`session`, ordered by timestamp, bounded to `limit`. It is a **top-k-by-timestamp** selection, not a relevance search:

```ts
  async latestExact(
    source = "",
    project = "",
    limit = 50,
    eventKeys?: ReadonlySet<string>,
    signal?: AbortSignal,
  ) {
    throwIfAborted(signal);
    if (eventKeys && !eventKeys.size) return { rows: [] as EventRow[], total: 0 };
    const table = await this.db.table("events");
    const predicates = [
      source && `source = ${sql(source)}`,
      project && `project = ${sql(project)}`,
    ].filter(Boolean) as string[];
    let query = table.query();
    if (predicates.length) query = query.where(predicates.join(" AND "));
    query = query.select(["id", "source", "timestamp"]);

    type Candidate = Pick<EventRow, "id" | "source" | "timestamp">;
    const heap: Candidate[] = [];
    const older = (left: Candidate, right: Candidate) =>
      left.timestamp < right.timestamp ||
      (left.timestamp === right.timestamp && `${left.source}\0${left.id}` < `${right.source}\0${right.id}`);
    const swap = (left: number, right: number) => {
      [heap[left], heap[right]] = [heap[right]!, heap[left]!];
    };
    const push = (candidate: Candidate) => {
      heap.push(candidate);
      for (let index = heap.length - 1; index > 0;) {
        const parent = Math.floor((index - 1) / 2);
        if (!older(heap[index]!, heap[parent]!)) break;
        swap(index, parent);
        index = parent;
      }
    };
    const replaceOldest = (candidate: Candidate) => {
      heap[0] = candidate;
      for (let index = 0;;) {
        const left = index * 2 + 1;
        const right = left + 1;
        let oldest = index;
        if (left < heap.length && older(heap[left]!, heap[oldest]!)) oldest = left;
        if (right < heap.length && older(heap[right]!, heap[oldest]!)) oldest = right;
        if (oldest === index) break;
        swap(index, oldest);
        index = oldest;
      }
    };

    let total = 0;
    for await (const batch of query) {
      throwIfAborted(signal);
      for (const value of batch.toArray()) {
        const candidate = value as unknown as Candidate;
        if (eventKeys && !eventKeys.has(`${candidate.source}\0${candidate.id}`)) continue;
        total += 1;
        if (heap.length < limit) push(candidate);
        else if (older(heap[0]!, candidate)) replaceOldest(candidate);
      }
    }

    const selected = heap.sort((left, right) =>
      right.timestamp.localeCompare(left.timestamp) ||
      `${right.source}\0${right.id}`.localeCompare(`${left.source}\0${left.id}`)
    );
    const keys = new Set(selected.map((row) => `${row.source}\0${row.id}`));
    const ids = [...new Set(selected.map((row) => row.id))];
    if (!ids.length) return { rows: [] as EventRow[], total };
    throwIfAborted(signal);
    const rows = await table.query()
      .where(`id IN (${ids.map(sql).join(", ")})`)
      .toArray() as unknown as EventRow[];
    const rowsByKey = new Map(rows
      .filter((row) => keys.has(`${row.source}\0${row.id}`))
      .map((row) => [`${row.source}\0${row.id}`, row]));
    return {
      rows: selected.flatMap((row) => {
        const full = rowsByKey.get(`${row.source}\0${row.id}`);
        return full ? [full] : [];
      }),
      total,
    };
  }
```

This is a textbook **min-heap top-k**: LanceDB has no native "order by timestamp, limit N" for this table, so the code streams every matching row's narrow `{id, source, timestamp}` projection in Arrow batches, maintains a size-`limit` binary min-heap keyed by "oldest first" so the *newest* `limit` rows always survive, and only re-fetches the full row (all 16 columns) for the small `ids` set that actually made the cut. The comment at `database.plain.ts:113-118` explains the companion `latestWindow` (a faster, approximate sibling used for the live-tail poll) explicitly in these terms:

```ts
    // LanceDB's scalar query has limit/offset but no timestamp order. Read only
    // a bounded physical tail, then restore the UI's chronological ordering in
    // memory. Imports append committed batches, so this window exposes fresh
    // rows without materializing the entire source on every live tick.
```

### 5.2 Embedding "map" — deterministic power-iteration PCA, not a query

`src/history-vectors.ts` computes a 2D/3D projection of an already-scoped, already-embedded set of events (one session, one day, filtered by human/agent "actor") purely for visualization. There is no query vector, no distance-to-query ranking, no top-k-by-similarity anywhere in this file.

Scoping the candidate set (source/project/session/date/actor, cross-referenced against the same `event_sources` provenance table used for browsing) — `src/history-vectors.ts:125-165`:

```ts
async function exactlyScopedEligibleEvents(
  plain: PlainDatabase,
  request: HistoryVectorRequest,
) {
  const names = await plain.tableNames();
  if (!names.includes("events")) return [];
  const rows = await (await plain.connection.openTable("events")).query()
    .where([
      `source = ${sql(request.source)}`,
      `project = ${sql(request.project)}`,
      `session_id = ${sql(request.session_id)}`,
    ].join(" AND "))
    .toArray() as unknown as EventRow[];
  const eligible = rows
    .filter((row) => bangkokDateKey(row.timestamp) === request.date)
    .filter((row) => matchesActor(row, request.actors))
    .filter((row) => isEmbeddableEvent(row as EmbeddingEventRow))
    .sort(eventOrder);
  if (!eligible.length) return [];
  if (!names.includes("event_sources")) {
    return request.folder === UNKNOWN_PROVENANCE_FOLDER ? eligible : [];
  }
  // ... folder provenance filtering, mirrors the browser path ...
  return eligible;
}
```

The dimensionality reduction itself — a from-scratch power-iteration PCA (no external ML library), producing 3 orthonormal axes and clipping outliers to a 5th/95th-percentile range — `src/history-vectors.ts:167-249`:

```ts
function dot(left: Float32Array, right: Float32Array) {
  let result = 0;
  for (let index = 0; index < left.length; index += 1) {
    result += left[index]! * right[index]!;
  }
  return result;
}

function normalizedAxes(vectors: Float32Array[]) {
  if (vectors.length <= 1) {
    return { coordinates: vectors.map(() => [0, 0, 0] as const), explainedVariance: null };
  }
  const dimension = vectors[0]!.length;
  const mean = new Float64Array(dimension);
  for (const vector of vectors) {
    for (let index = 0; index < dimension; index += 1) mean[index]! += vector[index]! / vectors.length;
  }
  const centered = vectors.map((vector) => {
    const result = new Float32Array(dimension);
    for (let index = 0; index < dimension; index += 1) result[index] = vector[index]! - mean[index]!;
    return result;
  });
  const components: Float32Array[] = [];
  const capturedVariance: number[] = [];
  const totalVariance = centered.reduce((sum, row) => sum + dot(row, row), 0);
  let seed = 42;
  const random = () => {
    seed = (seed * 1_103_515_245 + 12_345) & 0x7fffffff;
    return seed / 0x7fffffff - 0.5;
  };
  for (let axis = 0; axis < 3; axis += 1) {
    let component = Float32Array.from({ length: dimension }, random);
    for (let iteration = 0; iteration < 48; iteration += 1) {
      const next = new Float32Array(dimension);
      for (const row of centered) {
        const weight = dot(row, component);
        for (let index = 0; index < dimension; index += 1) next[index]! += weight * row[index]!;
      }
      for (const previous of components) {
        const overlap = dot(next, previous);
        for (let index = 0; index < dimension; index += 1) next[index]! -= overlap * previous[index]!;
      }
      const norm = Math.sqrt(dot(next, next));
      if (!Number.isFinite(norm) || norm < 1e-9) {
        component = new Float32Array(dimension);
        break;
      }
      for (let index = 0; index < dimension; index += 1) next[index]! /= norm;
      component = next;
    }
    components.push(component);
    capturedVariance.push(centered.reduce((sum, row) => sum + dot(row, component) ** 2, 0));
  }

  const raw = centered.map((row) => components.map((component) => dot(row, component)));
  for (let axis = 0; axis < 3; axis += 1) {
    const values = raw.map((coordinate) => coordinate[axis]!).sort((left, right) => left - right);
    const low = values[Math.floor(values.length * 0.05)]!;
    const high = values[Math.min(values.length - 1, Math.floor(values.length * 0.95))]!;
    const span = high - low;
    for (const coordinate of raw) {
      coordinate[axis] = span > 1e-12
        ? Math.max(-1, Math.min(1, ((coordinate[axis]! - low) / span) * 2 - 1))
        : 0;
    }
  }
  return {
    coordinates: raw.map((coordinate) => [coordinate[0]!, coordinate[1]!, coordinate[2]!] as const),
    explainedVariance: totalVariance > 0
      ? Math.max(0, Math.min(1, capturedVariance.reduce((sum, value) => sum + value, 0) / totalVariance))
      : null,
  };
}
```

This is the classic **power-iteration / NIPALS**-style approach to the top-3 principal components: seed a pseudo-random unit vector (fixed seed `42` for determinism across identical inputs — hence `"method": "deterministic-pca-3d"` in the response), repeatedly multiply by the centered data's implicit covariance, Gram-Schmidt-orthogonalize against previously found components, and normalize — 48 iterations per axis, no eigen-decomposition library required.

The entry point ties scoping → embedding lookup → sampling → projection together and reports coverage honestly (how many eligible events actually have a current vector) — `src/history-vectors.ts:271-377` (the full function; trimmed below to the shape-relevant parts — the elided middle is two early-return branches for a missing vector store/table):

```ts
export async function visualizeHistoryVectors(
  plain: PlainDatabase,
  vectorDatabase: VectorDatabase,
  request: HistoryVectorRequest,
) {
  const expectedSpace = EMBEDDING_DEPLOYMENTS[request.deployment].config.space;
  if (!sameEmbeddingSpace(vectorDatabase.space, expectedSpace)) {
    throw new HistoryVectorStoreError("selected vector store does not match the requested embedding space");
  }
  const eligible = await exactlyScopedEligibleEvents(plain, request);
  // ... "missing_store" early-return branches when the vector DB/table doesn't exist yet ...

  const metadata = await vectorDatabase.eventVectors().metadataForEventIds(eligible.map((row) => row.id));
  const embeddedEvents = eligible.filter((row) => {
    const vector = metadata.get(row.id);
    return vector?.text_hash === sha256(embeddingText(row.text)) &&
      vector.model === expectedSpace.model &&
      vector.dimension === expectedSpace.dimension;
  });
  const selectedEvents = evenlySample(embeddedEvents, request.limit);
  const rowsById = await vectorDatabase.eventVectors().rowsForEventIds(selectedEvents.map((row) => row.id));
  const vectorRows = selectedEvents.map((event) => rowsById.get(event.id)).filter(Boolean) as EventVectorRow[];
  assertVectors(vectorRows, expectedSpace.dimension);
  const projection = normalizedAxes(vectorRows.map((row) => row.vector));
  // ... zips projection.coordinates back onto each event for the response ...
  return {
    // ...
    coverage: {
      eligible: eligible.length,
      embedded: embeddedEvents.length,
      missing: eligible.length - embeddedEvents.length,
      sampled: selectedEvents.length,
    },
    projection: { method: "deterministic-pca-3d", explained_variance: projection.explainedVariance },
    points: /* ... */,
  };
}
```

Every vector read in this whole file is `metadataForEventIds` / `rowsForEventIds` — both scalar `WHERE event_id IN (...)` lookups (§3's `EventVectorRepository`), never a `.search(queryVector)` similarity call. **There is nothing in this codebase that takes free-text input, embeds it as a query, and ranks stored vectors against it.**

---

## 6. Idempotent re-import / backfill — what actually makes "repeat safely" true

The claim is real and load-bearing (`README.md:12`, `33-34`: *"imports idempotently"*, *"Stable event, block, occurrence, and file identities make bounded retries idempotent."*). The mechanism is layered:

### 6.1 Layer 1 — content-addressed file state (`plan()`)

`src/importer.ts:256-340`. Each JSONL file gets a stable id (`sha256(source + path)`), and is classified `new` / `changed` / `unchanged` / `shrunk` by comparing against the last saved `source_files` manifest row — first by cheap size/mtime metadata, falling back to a full re-hash only when requested:

```ts
export async function plan(
  db: PlainDatabase,
  spec: SourceSpec,
  onProgress?: ProgressCallback,
  options: PlanOptions = {},
): Promise<PlanReport> {
  const found = await discover(spec, onProgress);
  // ...
  for (const file of found) {
    const previous = known.get(file.id);
    let state: FilePlan["state"] = "new";
    if (previous) {
      if (previous.state === "pending" || previous.state === "failed") state = "changed";
      else if (previous.state === "requires_reconcile" || file.size < previous.size) state = "shrunk";
      else if (file.size !== previous.size || file.mtimeMs !== previous.mtimeMs) {
        state = "changed";
      } else if (compareMode === "metadata") {
        state = "unchanged";
      } else {
        state = await hashFile(file.path, () => onProgress?.({ /* ... */ })) === previous.sha256
          ? "unchanged" : "changed";
      }
    }
    // ...
  }
  // deterministic plan_revision = sha256 over every (id, size, mtime, state) tuple:
  const planRevision = sha256(JSON.stringify([spec.source, resolve(spec.root), ...planSignatureRows]));
  // ...
}
```

A `shrunk` file (byte count went *down* since last import — evidence of truncation/rewrite) is never silently reprocessed; it is routed to `requires_reconcile` and blocks fresh imports for that source until a human/operator resolves it (`importSourceUnlocked`, quoted below, throws if `preflight.shrunk > 0`).

### 6.2 Layer 2 — byte-exact snapshot before hash-then-parse

Before touching a file's bytes twice (hash pass, parse pass), the importer takes an **immutable snapshot** of exactly the byte length observed during preflight — refusing to proceed if the file changed underneath it — `src/importer.ts:84-172` (small-file, in-memory branch shown; a disk-spilling twin exists for files over 16 MiB):

```ts
async function snapshotFile(path: string, size: number, heartbeat?: () => void) {
  if (size <= MEMORY_SNAPSHOT_LIMIT) {
    const source = await open(path, "r");
    try {
      const sourceInfo = await source.stat();
      if (!sourceInfo.isFile() || sourceInfo.size < size) {
        throw new Error(`JSONL file changed before snapshot: ${path}`);
      }
      const buffer = Buffer.allocUnsafe(size);
      let position = 0;
      let lastHeartbeatAt = 0;
      while (position < size) {
        const { bytesRead } = await source.read(buffer, position, size - position, position);
        if (!bytesRead) throw new Error(`JSONL file changed during snapshot: ${path}`);
        position += bytesRead;
        const now = Date.now();
        if (heartbeat && now - lastHeartbeatAt >= 250) { lastHeartbeatAt = now; heartbeat(); }
      }
      return {
        input: () => Readable.from([buffer]),
        sha256: createHash("sha256").update(buffer).digest("hex"),
        cleanup: async () => {},
      };
    } finally { await source.close(); }
  }
  // ... disk-spilling branch for size > MEMORY_SNAPSHOT_LIMIT (16 MiB), same
  // "changed before/during snapshot" guards, src/importer.ts:115-172 ...
}
```

`lessons/05-import-and-dedupe.md:52-55` states the consequence in plain language:

> The importer snapshots exactly the byte length observed during preflight, then hashes and parses that immutable on-disk prefix. If a live JSONL file is appended while the import runs, those new bytes stay out of the current provenance hash and are picked up as a changed file on the next idempotent pass.

### 6.3 Layer 3 — stable canonical IDs + `mergeInsert…whenNotMatchedInsertAll`

Already shown in full in §1.5 and §3.2: every `EventRow.id` is `"${eventUuid}#${blockIndex}"`, deterministic from content (or a content hash when no natural id exists). Insertion never does a blind `add()` — `insertNew()` (`src/database.plain.ts:69-79`) de-duplicates the incoming batch by `id` first, then calls:

```ts
const result = await table.mergeInsert("id").whenNotMatchedInsertAll().execute(unique);
```

`whenNotMatchedInsertAll()` with no `whenMatchedUpdateAll()` clause means: **rows whose id already exists in the table are silently skipped**, not overwritten and not duplicated. Re-running the exact same import a second time inserts zero new canonical rows.

### 6.4 Layer 4 — the pending/recovery checkpoint for mid-file crashes

`importFile()` (`src/importer.ts:342-495`) is a two-pass design specifically to survive a crash *mid-file*: pass one computes a complete audit (parsed/inserted/duplicate/corrupt counts) using a **throwaway temporary LanceDB** as a scratch "seen it" set, saves a `state: "pending"` manifest row with those exact counts, and only *then* does pass two re-parse and actually write to the real `events`/`event_sources` tables. If the process dies between those two passes, the next run detects `prior.state === "pending"`, re-validates the snapshot hasn't drifted, and treats the counts as a checkpoint to replay against rather than recomputing from scratch:

```ts
  const prior = await db.files().find(file.id);
  const recovery = prior?.state === "pending";
  if (recovery && (prior.sha256 !== fileHash || prior.size !== file.size)) {
    await snapshot.cleanup();
    throw new Error(`pending import snapshot changed; reconcile before importing: ${file.path}`);
  }
  // ... pass one: audit into a throwaway LanceDB, src/importer.ts:402-441 ...
    await flushAudit();
    if (recovery) {
      inserted = prior.inserted_events;
      duplicates = prior.duplicate_events;
      if (
        prior.parsed_records !== parsed || prior.corrupt_lines !== corrupt ||
        inserted + duplicates !== blocks
      ) throw new Error(`pending import audit changed; reconcile before importing: ${file.path}`);
    }
```
(`src/importer.ts:380-439`)

### 6.5 Layer 5 — single-writer lock + preflight-revision confirmation

Every top-level import acquires an exclusive lock on the plain-store directory (same hard-link idiom as §4.4's embedding lock) — `src/importer.ts:56-82` — and, when the caller supplied a previously-fetched `plan_revision`/expected file count (e.g. a UI "confirm this exact plan" flow), the importer **re-plans and refuses to proceed** if reality drifted from what the user confirmed:

`src/importer.ts:579-609`:

```ts
async function importSourceUnlocked(
  db: PlainDatabase,
  spec: SourceSpec,
  options: ImportOptions = {},
): Promise<ImportReport> {
  const preflight = await plan(db, spec, options.onProgress);
  if (
    options.expectedPlanRevision !== undefined &&
    preflight.plan_revision !== options.expectedPlanRevision
  ) {
    throw new Error(
      `stale import plan: expected revision ${options.expectedPlanRevision}, got ${preflight.plan_revision}`,
    );
  }
  if (
    options.expectedWillParse !== undefined &&
    preflight.will_parse !== options.expectedWillParse
  ) {
    throw new Error(
      `stale import plan: expected ${options.expectedWillParse} files, got ${preflight.will_parse}`,
    );
  }
  if (preflight.shrunk > 0) {
    throw new Error(`import plan contains ${preflight.shrunk} shrunk file(s); reconcile before importing`);
  }
  await db.create();
  const allPriorRows = await db.files().list();
  const foreignPending = allPriorRows.find((row) =>
    row.state === "pending" && row.source !== spec.source
  );
  if (foreignPending) {
    throw new Error(
      `pending import for source ${foreignPending.source} must recover before fresh source ` +
      `${spec.source}: ${foreignPending.path}`,
    );
  }
  // ...
```

### 6.6 Proof, end to end, straight from the test suite

`tests/importer.test.ts:105-158` — write a file, import it, **append to it mid-import via the progress callback**, then resume, then repeat the exact same import a third time and assert nothing new is written:

```ts
  test("imports the preflight prefix and defers an append until the next idempotent pass", async () => {
    // ... writes `firstPrefix` to disk, then appends `appended` on the 2nd progress tick ...
    const first = await importFile(db, spec, file, () => {
      progressCalls++;
      if (progressCalls === 2) appendFileSync(path, appended);
    });

    const prefixHash = sha256(firstPrefix);
    expect(first.parsed).toBe(1);
    expect(await db.events().count()).toBe(1);
    expect(await db.occurrences().list()).toEqual([
      expect.objectContaining({ event_id: "first#0", file_hash: prefixHash }),
    ]);
    expect(await db.files().find(file.id)).toEqual(
      expect.objectContaining({ size: info.size, sha256: prefixHash, parsed_records: 1 }),
    );

    const resumed = await importSource(db, spec);
    const fullHash = sha256(firstPrefix + appended);
    expect(resumed.changed).toBe(1);
    expect(resumed.inserted).toBe(1);
    expect(resumed.occurrences_inserted).toBe(1);
    expect(await db.events().count()).toBe(2);
    expect(await db.occurrences().list()).toEqual(expect.arrayContaining([
      expect.objectContaining({ event_id: "first#0", file_hash: prefixHash }),
      expect.objectContaining({ event_id: "second#0", file_hash: fullHash }),
    ]));

    const repeated = await importSource(db, spec);
    expect(repeated.unchanged).toBe(1);
    expect(repeated.selected_files).toBe(0);
    expect(await db.events().count()).toBe(2);
    expect(await db.occurrences().count()).toBe(2);
  });
```

And the equivalent proof on the embedding side, `tests/embeddings.test.ts:286-314` (also quoted in §4.4's discussion, shown here for the assertion on the *plain* store staying stable and the vector count staying `1` across two embed passes until content changes):

```ts
  test("is idempotent when current and overwrites a changed plain event", async () => {
    const { plain, vector: vectors } = await temporaryStores();
    const first = event("same#0", "human_intent", text("a"));
    await plain.events().insert([first]);
    let calls = 0;
    const fake = provider(async (inputs) => { calls++; return inputs.map(() => vector(calls)); });

    await embedPending(plain, vectors, fake, { maxEvents: 10 });
    const repeated = await embedPending(plain, vectors, fake, { maxEvents: 10 });
    expect(repeated).toMatchObject({ up_to_date: 1, selected: 0, embedded: 0, vectors: 1 });
    expect(calls).toBe(1);

    const changed = { ...first, text: text("b"), text_hash: sha256(text("b")) };
    await (await plain.table("events"))
      .mergeInsert("id").whenMatchedUpdateAll().whenNotMatchedInsertAll().execute([changed]);

    const refreshed = await embedPending(plain, vectors, fake, { maxEvents: 10 });
    expect(refreshed).toMatchObject({ up_to_date: 0, selected: 1, embedded: 1, vectors: 1 });
    expect(calls).toBe(2);
    expect(await vectors.eventVectors().metadata()).toEqual([
      expect.objectContaining({ event_id: first.id, text_hash: sha256(embeddingText(changed.text)) }),
    ]);
  });
```

---

## 7. Redaction / privacy filter applied before persistence

### Reality check — there is **no PII/secret scrubbing of session content anywhere**. Raw JSONL text (which may contain anything a human pasted into a coding session — API keys, customer data, file contents) is stored and, if selected, embedded **unredacted**. What actually exists is narrower: (a) exclusion of known-synthetic content from the *embedding* path only, (b) redaction of credentials from *outbound error messages*, and (c) network-level access controls. All three, verbatim:

### 7.1 Content-type exclusion (not privacy redaction — filters synthetic/system text out of the embedding candidate pool)

Applied twice, independently, at two different call sites — once as a SQL predicate (`database.plain.ts`) and once as an application-level guard on top of it (`embeddings.ts`), explicitly described in the second site's own comment as defense-in-depth rather than the source of truth:

`src/database.plain.ts:262-287` (the `embeddingPage` SQL predicate):

```ts
  async embeddingPage(options: EmbeddingPageOptions): Promise<EmbeddingEventRow[]> {
    if (options.eventIds && !options.eventIds.length) return [];
    const table = await this.db.table("events");
    const predicates = [
      `semantic_role = ${sql(options.semanticRole)}`,
      `block_type IN (${["text", "summary", "input_text", "output_text"].map(sql).join(", ")})`,
      `length(text) > ${options.minimumCharacters}`,
      `text NOT LIKE ${sql("<system-reminder>%")}`,
      `text NOT LIKE ${sql("[Image: source:%")}`,
      options.source && `source = ${sql(options.source)}`,
      options.project && `project = ${sql(options.project)}`,
      options.sinceInclusive && `timestamp >= ${sql(options.sinceInclusive)}`,
      options.untilExclusive && `timestamp < ${sql(options.untilExclusive)}`,
      options.eventIds && `id IN (${options.eventIds.map(sql).join(", ")})`,
    ].filter(Boolean) as string[];
    // ...
  }
```

`src/embeddings.ts:175-185` (`isEmbeddableEvent`, the in-process re-check — quoted in full in §2):

```ts
export function isEmbeddableEvent(event: EmbeddingEventRow) {
  if (ROLE_PRIORITY[event.semantic_role] > 2) return false;
  if (!["text", "summary", "input_text", "output_text"].includes(event.block_type)) return false;
  const text = embeddingText(event.text);
  const trimmed = text.trimStart();
  return text.trim().length > EMBEDDING_MIN_CHARACTERS &&
    !trimmed.startsWith("<system-reminder>") &&
    !trimmed.startsWith("[Image: source:");
}
```

This exists to keep Claude Code's synthetic `<system-reminder>` injections and image placeholder captions out of the embedding corpus — it is a **signal-quality** filter, not a content-safety one. It has no opinion about API keys, tokens, emails, or any other sensitive substring inside legitimate human/assistant text; those are stored (§1.5, `text: block.text.slice(0, 4_000)`) and, if the block otherwise qualifies, embedded (§2, §4) exactly as typed.

### 7.2 Credential redaction — but only in outbound *error message* text, never in stored/embedded content

`src/embedding-providers/cloudflare.ts:75-97`:

```ts
function redactRemoteMessage(message: string, apiToken: string) {
  return message
    .split(apiToken).join("[REDACTED]")
    .replace(/Bearer\s+[^\s,;"'}]+/gi, "Bearer [REDACTED]")
    .slice(0, 500);
}

async function cloudflareErrorDetail(response: Response, apiToken: string) {
  const body = await response.json().catch(() => undefined) as {
    errors?: Array<{ code?: unknown; message?: unknown }>;
  } | undefined;
  const approved = Array.isArray(body?.errors)
    ? body.errors.slice(0, 3).flatMap((error) => {
      if (typeof error?.message !== "string") return [];
      const code = typeof error.code === "number" || typeof error.code === "string"
        ? `[${String(error.code)}] ` : "";
      return [`${code}${error.message}`];
    })
    : [];
  const detail = approved.join("; ") || response.statusText.trim() || "request rejected";
  return redactRemoteMessage(detail, apiToken);
}
```

This exists purely so that if Cloudflare's API ever echoes the bearer token back inside an error body (or the code path formats one into a message), that token can't leak into logs, thrown `Error.message` strings, or the JSON returned by `/api/jobs/*/log` (§8). It is a literal string-replace of the exact token value plus a regex catch-all for any `Bearer <token>` shape, capped to 500 characters. It has nothing to do with the JSONL session content itself.

### 7.3 "Never accept a credential as a CLI value" — a structural policy, enforced in the plugin contract

Credentials only ever come from environment variables, never from `--flag` values that could end up in shell history or a process list. `src/cli.ts:176-178` states the policy in the `embed --help` text:

```
Backward compatible: "embed --source ..." is the same as "embed run --source ...".
Credentials are read from the environment and are never accepted as CLI values.
```

...and it's structurally enforced in the provider-plugin contract, not just documented: a `secret: true` environment variable is **not allowed to declare a default value** (which would otherwise tempt a plugin author into hardcoding one) — `src/embedding-plugin.ts:44-52`:

```ts
  for (const item of plugin.environment) {
    if (!/^[A-Z][A-Z0-9_]*$/.test(item.name)) {
      throw new Error(`embedding provider environment name is invalid: ${item.name}`);
    }
    if (item.secret && item.defaultValue !== undefined) {
      throw new Error(
        `embedding provider ${plugin.deployment.id} secret ${item.name} must not have a default value`,
      );
    }
  }
```

And the Cloudflare plugin registration marks its token `secret: true`, which flows into `embed providers`' JSON output as a flag the UI/CLI can use to mask the value rather than print it — `src/embedding-plugins.ts:92-97`:

```ts
    {
      name: "CLOUDFLARE_API_TOKEN",
      required: true,
      secret: true,
      description: "Bearer token with Workers AI read/run permission.",
    },
```

### 7.4 Network-level privacy controls (not content redaction, but the closest thing to a privacy boundary the server enforces)

`src/server.ts:641-653` — every request must present a loopback `Host`, and every mutating request must be same-origin JSON (a lightweight CSRF guard for a server with no auth):

```ts
function validateLocalHost(url: URL) {
  const hostname = url.hostname.toLowerCase();
  if (hostname !== "127.0.0.1" && hostname !== "localhost" && hostname !== "[::1]" && hostname !== "::1") {
    throw new HttpError(400, "requests require a local Host");
  }
}

function validateMutation(request: Request, url: URL) {
  const origin = request.headers.get("origin");
  if (origin && origin !== url.origin) throw new HttpError(400, "cross-origin mutation rejected");
  const contentType = request.headers.get("content-type")?.split(";", 1)[0].trim().toLowerCase();
  if (contentType !== "application/json") throw new HttpError(400, "application/json is required");
}
```

Combined with `Bun.serve({ hostname: "127.0.0.1", ... })` (`src/server.ts:735-738`), the server never binds a non-loopback interface in the first place — `validateLocalHost` is a defense-in-depth check against `Host`-header tricks reaching it through a proxy, not the primary boundary.

**Net assessment for this section:** the "privacy filter" the task asked to find is not a redaction layer over user data — it's (1) a quality filter that excludes tool telemetry from embeddings, (2) a token-leak guard on *outbound error strings only*, and (3) a localhost/CSRF network boundary. Anyone importing real Claude Code / Codex history into Lanceglass should assume everything they typed or that a tool printed — including secrets accidentally pasted into a session — is stored verbatim in `events.text` and may be sent to whichever embedding provider (including the cloud Cloudflare one) they configure.

---

## 8. Error handling patterns and degradation reporting

### 8.1 Centralized HTTP error mapping — one `try/catch`, typed errors → status codes

`src/server.ts:107-111` (the error type) and `src/server.ts:739-863` (the whole `fetch` handler is one big `try { ...every route... } catch`, tail shown):

```ts
class HttpError extends Error {
  constructor(readonly status: number, message: string, readonly details?: Record<string, unknown>) {
    super(message);
  }
}
```

```ts
const server = Bun.serve({
  hostname: "127.0.0.1",
  port: PORT,
  idleTimeout: 255,
  async fetch(request: Request) {
    const url = new URL(request.url);
    watchJobsForHistoryCacheInvalidation();

    try {
      validateLocalHost(url);
      // ... ~20 route branches, each just `return json(await someHandler(...))` ...
      return json({ error: "not found" }, 404);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      if (error instanceof HttpError) return json({ error: message, ...error.details }, error.status);
      if (error instanceof HistoryInputError) return json({ error: message }, 400);
      if (error instanceof HistoryVectorInputError) return json({ error: message }, 400);
      if (error instanceof HistoryVectorStoreError) return json({ error: message }, 422);
      return json({ error: message, db_dir: DB_DIR }, 500);
    }
  },
});
```

Every route handler is allowed to just `throw` a typed error (`HttpError(status, message, details?)` for anything HTTP-shaped, or a domain error class like `HistoryInputError`/`HistoryVectorInputError`/`HistoryVectorStoreError`) and the single catch block at the bottom maps it to the right status code and JSON body. An *unrecognized* error (a bug, a LanceDB internal failure, anything not explicitly typed) still degrades gracefully to a `500` with the raw message **and** `db_dir` attached — so a caller debugging "why is this failing" doesn't have to guess which physical store was even open.

Domain input-validation errors follow the same shape throughout the codebase — a dedicated `Error` subclass per module boundary (`HistoryInputError` in `history.ts`, `HistoryVectorInputError`/`HistoryVectorStoreError` in `history-vectors.ts`, `EmbeddingValidationError` in `embedding-provider.ts`) so callers can `instanceof`-branch on "bad input" vs. "infrastructure failure" vs. "malformed model output" without string-matching messages.

### 8.2 Request-body / query-param bounds checking (defense against a hostile or buggy local client)

`src/server.ts:611-618, 655-667`:

```ts
function boundedText(value: unknown, name: string, max: number) {
  if (typeof value !== "string") throw new HttpError(400, `${name} must be a string`);
  const result = value.trim();
  if (result.length > max || result.includes("\0")) {
    throw new HttpError(400, `${name} is too long or contains invalid characters`);
  }
  return result;
}
```

```ts
async function jsonBody(request: Request) {
  const declared = Number(request.headers.get("content-length") ?? 0);
  if (Number.isFinite(declared) && declared > MAX_BODY_BYTES) throw new HttpError(400, "request body is too large");
  const text = await request.text();
  if (Buffer.byteLength(text) > MAX_BODY_BYTES) throw new HttpError(400, "request body is too large");
  try {
    const value = JSON.parse(text);
    if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error();
    return value as Record<string, unknown>;
  } catch {
    throw new HttpError(400, "request body must be a JSON object");
  }
}
```

The `\0` check exists because every filter value downstream gets embedded into a `\0`-joined composite cache/set key (e.g. `${source}\0${id}` throughout `database.plain.ts`, `event-browser.ts`, `history.ts`) — rejecting embedded NULs at the boundary keeps that convention an actually-safe delimiter.

### 8.3 Per-line degradation during JSONL parsing — corrupt lines never abort a file

`src/importer.ts:408-419` (pass one of `importFile`; pass two mirrors it):

```ts
    for await (const raw of createInterface({ input: snapshot.input() })) {
      line++;
      if (!raw.trim()) continue;
      let value: unknown;
      try { value = JSON.parse(raw); }
      catch { corrupt++; progress(); continue; }
      if (!value || typeof value !== "object" || Array.isArray(value)) {
        corrupt++;
        progress();
        continue;
      }
      parsed++;
      const rows = normalize(value as Record<string, unknown>, { /* ... */ }, auditNormalization);
      // ...
    }
```

A malformed line (bad JSON, or valid JSON that isn't an object — e.g. a bare array or scalar) increments `corrupt` and the loop moves on to the next line; it never throws and never aborts the file. This is proven directly by the bundled fixture (§1.8), whose last line is `{deliberately corrupt smoke line` — invalid JSON on purpose — and the smoke test (`lessons/04-normalize-jsonl.md:19-22`) expects the run to complete with that line "handled visibly," not crash:

> The fixture is converted into deterministic typed rows, malformed or irrelevant input is handled visibly, and no private archive is needed to prove normalization.

### 8.4 Distinguishing retryable vs. non-retryable failure in the embedding call

Already shown in §4.4 (`src/embeddings.ts:253-272`) — repeated here because it's the clearest single example of *typed* degradation in the whole codebase:

```ts
async function embedBatch(
  provider: EmbeddingProvider,
  texts: string[],
  retries: number,
  retryDelayMs: number,
  sleep: (milliseconds: number) => Promise<void>,
) {
  for (let attempt = 0; ; attempt++) {
    try {
      return validateEmbeddingVectors(
        await provider.embed(texts), texts.length, provider.space.dimension,
      );
    } catch (error) {
      if (error instanceof EmbeddingValidationError || attempt >= retries) throw error;
      await sleep(retryDelayMs * 2 ** attempt);
    }
  }
}
```

A transport error (timeout, non-2xx, connection refused — a plain `Error`) gets exponential-backoff retried up to `retries` times (default `2`). A **shape** error — the provider answered, but with the wrong count, wrong dimension, a non-finite number, or a zero-norm vector (`validateEmbeddingVectors`, §4.4) — is `EmbeddingValidationError` and is thrown immediately on the first occurrence, because retrying a deterministic function with the same malformed input will not fix it, and silently accepting a corrupt vector would poison the vector store (and, downstream, the PCA projection in §5.2) with no way to distinguish it from a legitimate embedding later.

### 8.5 Subprocess job degradation reporting — `JobManager` (background imports)

Background imports (`POST /api/jobs/import`) run as a **spawned child process** (`bun src/cli.ts import ...`) rather than in-process, specifically so a fatal crash in one import can't take the server down. Every failure mode gets its own terminal `state` and `error` string, surfaced through `GET /api/jobs` and `GET /api/jobs/:id/log` — `src/jobs.ts:264-361` (elided to the error-handling branches):

```ts
  private async run(job: InternalJob, request: ImportJobRequest) {
    const argv = [process.execPath, "src/cli.ts", "import", "--root", request.spec.root, "--source", request.spec.source];
    // ...
    try {
      job.child = Bun.spawn(argv, {
        cwd: join(import.meta.dir, ".."),
        env: { ...process.env, DB_DIR: this.dbDir, PLAIN_DB_DIR: this.dbDir },
        stdin: "ignore", stdout: "pipe", stderr: "pipe",
      });
    } catch (error) {
      this.appendLine(job, "stderr", error instanceof Error ? error.message : String(error));
      this.finish(job, "failed", "failed to spawn import process");
      return;
    }

    const stdout = drainJobStream(job.child.stdout, "stdout", (stream, value) => this.appendLine(job, stream, value), (chunk) => {
      if (stdoutOverflow) return;
      stdoutBytes += chunk.byteLength;
      if (stdoutBytes > MAX_RESULT_BYTES) { stdoutOverflow = true; stdoutChunks.length = 0; return; }
      stdoutChunks.push(chunk.slice());
    });
    const stderr = drainJobStream(job.child.stderr, "stderr", (stream, value) => this.appendLine(job, stream, value));

    let exitCode: number;
    try {
      exitCode = await job.child.exited;
      job.exit_code = exitCode;
      const drains = await Promise.allSettled([stdout, stderr]);
      const drainFailure = drains.find((result) => result.status === "rejected") as PromiseRejectedResult | undefined;
      if (drainFailure) throw drainFailure.reason;
    } catch (error) {
      this.finish(job, job.state === "cancelling" ? "cancelled" : "failed",
        `import process failed: ${error instanceof Error ? error.message : String(error)}`);
      return;
    }

    if (job.state === "cancelling") { this.finish(job, "cancelled"); return; }
    if (exitCode !== 0) { this.finish(job, "failed", `import exited with code ${exitCode}`); return; }
    if (stdoutOverflow) { this.finish(job, "failed", "import result exceeded output limit"); return; }
    try {
      const bytes = Buffer.concat(stdoutChunks.map((chunk) => Buffer.from(chunk)));
      job.result = JSON.parse(bytes.toString("utf8")) as ImportReport;
      this.finish(job, "succeeded");
    } catch (error) {
      this.finish(job, "failed", `invalid import result: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
```

Five distinct, separately-reported degradation modes in this one function: spawn failure, stream-drain failure, cancellation racing a crash, non-zero exit code, stdout exceeding the 2 MiB result cap, and a final JSON-parse failure on the child's own stdout (i.e. the child claimed success but its output wasn't the JSON contract the server expects). Every branch calls `finish(job, state, error?)`, which is the single place `state`/`error`/`finished_at` get written (`src/jobs.ts:255-262`) — so there's exactly one code path a client can poll to learn the outcome, no matter which of the five things went wrong.

Log lines themselves are bounded in three independent dimensions so a runaway child can't exhaust server memory: per-line byte cap with a visible truncation suffix, a ring buffer capped at `MAX_LOG_LINES` (500), and the separate `MAX_RESULT_BYTES` (2 MiB) cap on the captured stdout used for the final JSON result — `src/jobs.ts:57-61, 76-81`:

```ts
const MAX_JOBS = 50;
const MAX_LOG_LINES = 500;
const MAX_LINE_BYTES = 64 * 1024;
const MAX_RESULT_BYTES = 2 * 1024 * 1024;
const KILL_GRACE_MS = 1_500;

function boundedLine(value: string) {
  const bytes = Buffer.byteLength(value);
  if (bytes <= MAX_LINE_BYTES) return value;
  const suffix = `… [line truncated: ${bytes} bytes]`;
  return Buffer.from(value).subarray(0, MAX_LINE_BYTES - Buffer.byteLength(suffix)).toString() + suffix;
}
```

Cancellation itself degrades gracefully too — SIGTERM first, SIGKILL only after a grace period, so an in-flight LanceDB write gets a chance to finish cleanly — `src/jobs.ts:221-234`:

```ts
  cancel(id: string) {
    const job = this.jobs.find((candidate) => candidate.id === id);
    if (!job) return undefined;
    if (job.state !== "running" && job.state !== "cancelling") return publicJob(job);
    if (job.state === "running") {
      job.state = "cancelling";
      job.child?.kill("SIGTERM");
      job.killTimer = setTimeout(() => {
        if (job.state === "cancelling") job.child?.kill("SIGKILL");
      }, KILL_GRACE_MS);
      job.killTimer.unref();
    }
    return publicJob(job);
  }
```

### 8.6 Cooperative cancellation for long-running reads (`AbortSignal`)

Every hot read path in `database.plain.ts` and `event-browser.ts` accepts an optional `AbortSignal` and checks it between Arrow batches, not just at entry — so a client that navigates away mid-query stops burning CPU on a scan whose result will be discarded — `src/database.plain.ts:16-22`:

```ts
export function abortError() {
  return new DOMException("The operation was aborted", "AbortError");
}

export function throwIfAborted(signal?: AbortSignal) {
  if (signal?.aborted) throw abortError();
}
```

...used, for instance, inline in the streamed batch loop of `latestExact` (§5.1): `throwIfAborted(signal);` appears once before the query starts and again inside the `for await (const batch of query)` loop body, so an abort mid-scan of a multi-million-row table is honored within one batch instead of running to completion.

### 8.7 Lock-contention errors carry enough detail to actually act on

Both the import lock (`src/importer.ts:56-82`, quoted in §6.5's neighborhood) and the embedding lock (§4.4) report the **PID of the process currently holding the lock** in the thrown error, rather than a bare "locked" message:

```ts
    const owner = await readImportLockOwner(lockPath);
    const pid = Number.isInteger(owner?.pid) ? ` (pid ${owner!.pid})` : "";
    throw new Error(
      `plain database import writer is already active for ${db.directory}${pid}; ` +
      `wait for it to finish or manually remove ${lockPath} after verifying the owner is gone`,
    );
```

This is degradation reporting aimed at a human operator, not just a machine caller: it tells them exactly which process to check with `ps`/`kill` before they consider the more dangerous manual fallback the message itself names (deleting the lock file after confirming the owner is actually gone).

---

## Appendix — file map for everything cited above

| File | Role |
|---|---|
| `src/normalize.ts` | JSONL → typed rows: envelope parsing, block/chunk splitting, canonical ID derivation (§1, §2) |
| `src/types.ts` | `EventRow`, `EventVectorRow`, `EventSourceRow`, `SourceFileRow`, report/progress types |
| `src/schemas.ts` | Apache Arrow `Schema` objects for all four LanceDB tables; embedding contract constants (§3) |
| `src/database.ts` | `Database` — pairs one `PlainDatabase` + one `VectorDatabase`, enforces separate directories |
| `src/database.plain.ts` | `PlainDatabase`/`EventRepository`/etc. — table creation, `mergeInsert` dedupe, `latestExact` top-k heap (§3, §5, §6) |
| `src/database.vector.ts` | `VectorDatabase`/`EventVectorRepository` — lazy table creation, Arrow-metadata contract check, `upsert` (§3) |
| `src/embeddings.ts` | `embedPending` orchestrator: paging, batching, incremental skip, resumability, file lock (§2, §4) |
| `src/embedding-provider.ts` | `EmbeddingProvider` interface, embedding-space definitions, Ollama single + pool transports (§4) |
| `src/embedding-providers/cloudflare.ts` | Cloudflare Workers AI transport + revision-fingerprint pinning + error redaction (§4, §7) |
| `src/embedding-plugins.ts` / `src/embedding-plugin.ts` | Static provider-plugin registry and contract validation (§4, §7) |
| `src/importer.ts` | `discover`/`intake`/`plan`/`importFile`/`importSource` — the whole idempotent import pipeline (§6, §8) |
| `src/jobs.ts` | `JobManager` — background import subprocess lifecycle, log capture, cancellation (§8) |
| `src/history.ts` | Calendar-grouped session history (day/week/month) — not quoted at length; not a search feature |
| `src/history-vectors.ts` | Scoped PCA projection of existing embeddings for the "Vector map" UI (§5) |
| `src/event-browser.ts` / `src/event-view.ts` | Filtered/faceted event listing behind `/api/events*` (§5) |
| `src/server.ts` | Bun HTTP server: routes, `HttpError` mapping, local-only/CSRF guards, caching (§7, §8) |
| `src/cli.ts` | `bun src/cli.ts <command>` — thin wrapper calling the same library functions the server calls |
| `fixtures/minimal/*.jsonl` | The only JSONL data ever committed to the repo or used in CI/demo (§1) |
| `tests/normalize.test.ts`, `tests/importer.test.ts`, `tests/embeddings.test.ts` | Behavioral proof for §1, §6 claims |
| `lessons/04-*.md`, `05-*.md`, `08-*.md` | Numbered narrative lessons the repo itself uses to teach this exact pipeline |

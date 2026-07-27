# Arra Oracle V3 — MCP Tool Surface Reference

**Version**: 26.7.26-alpha.227  
**Release Date**: 2026-07-26  
**Repository**: [Soul-Brews-Studio/arra-oracle-v3](https://github.com/Soul-Brews-Studio/arra-oracle-v3)  
**Branch**: `alpha`

---

## Installation & Running

### Docker (Recommended)

```bash
# HTTP Server (long-running)
docker run --rm -d -p 47778:47778 \
  -v arra-oracle-data:/data \
  -v ~/notes:~/notes:ro \
  ghcr.io/soul-brews-studio/arra-oracle-v3:http

# MCP Stdio Server (for Claude, agents, MCP clients)
docker run --rm -i \
  -e ORACLE_LOG_TARGET=stderr \
  -v arra-oracle-data:/data \
  ghcr.io/soul-brews-studio/arra-oracle-v3:stdio
```

### Source (Bun Runtime)

```bash
# Entry point: bin/mcp.ts
# Launcher resolves ./src/index.ts for the MCP server

bun bin/mcp.ts --read-only  # Read-only mode
ORACLE_HTTP_URL=http://localhost:5000 bun bin/mcp.ts  # HTTP proxy mode
```

---

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `ORACLE_DATA_DIR` | Data directory (SQLite, vectors, config) | `./data` (or XDG) |
| `ORACLE_REPO_ROOT` | Project root for relative paths | Auto-detected from `bin/mcp.ts` |
| `ORACLE_HTTP_URL` | If set, proxy MCP calls to HTTP API | Unset (embedded mode) |
| `ORACLE_READ_ONLY` | Run in read-only mode (disable write tools) | `false` |
| `ORACLE_TOOL_GROUPS_HOT_RELOAD` | Watch config.json for tool group changes | `1` (enabled) |
| `ORACLE_LOG_TARGET` | Logging output (`stdout`, `stderr`) | `stderr` |
| `ARRA_PEER_TOKEN` | Bearer token for peer endpoints | Unset |

---

## Configuration

### Tool Groups Config

Location: `$ORACLE_DATA_DIR/config.json` or project `.arra/config.json`

Hot-reloaded when `ORACLE_TOOL_GROUPS_HOT_RELOAD !== '0'`.

```json
{
  "core": true,
  "search": true,
  "knowledge": true,
  "forum": true,
  "trace": true,
  "oracle": true,
  "session": true,
  "mcp": true,
  "disabled_tools": ["oracle_verify"],
  "enabled_tools": ["oracle_search", "oracle_read"]
}
```

**Tool Groups**:
- `core` → `oracle_recap`, `oracle_profile`, `oracle_reflect`
- `search` → `oracle_search`, `oracle_search_chain`, `oracle_read`, `oracle_list`, `oracle_concepts`, `oracle_ask`
- `knowledge` → `oracle_learn`, `oracle_stats`, `oracle_supersede`, `oracle_research_note`
- `forum` → `oracle_thread`, `oracle_threads`, `oracle_thread_read`, `oracle_thread_update`
- `trace` → `oracle_trace`, `oracle_trace_list`, `oracle_trace_get`, `oracle_trace_link`, `oracle_trace_unlink`, `oracle_trace_chain`, `oracle_trace_distill`
- `oracle` → Oracle-specific utilities (guides, profiles)
- `session` → `oracle_handoff`, `oracle_inbox`
- `mcp` → `oracle_mcp_list_tools`, `oracle_mcp_call`

### Read-Only Mode

When `ORACLE_READ_ONLY=true` or `--read-only` flag:
- Write tools are disabled: `oracle_learn`, `oracle_supersede`, `oracle_handoff`, `oracle_chain_search`, `oracle_thread`, `oracle_thread_update`, `oracle_trace`, `oracle_trace_link`, `oracle_trace_unlink`, `oracle_trace_distill`, `oracle_mcp_call`, `oracle_verify`
- All read-only tools remain available (search, read, list, stats, etc.)

---

## MCP Tools — Complete Reference

### Search & Knowledge Retrieval

#### `oracle_search`
**Group**: search | **Read-Only**: ✅ | **Status**: ✅ ACTIVE

Search Oracle knowledge base using hybrid search (FTS5 keywords + LanceDB vectors).

**Input Parameters**:
```json
{
  "query": "string (required)",
  "type": "string (optional, enum: principle|pattern|learning|retro|all, default: all)",
  "limit": "number (optional, default: 5)",
  "offset": "number (optional, default: 0, for pagination)",
  "mode": "string (optional, enum: hybrid|fts|vector, default: hybrid)",
  "retrieval": "string (optional, enum: full|compact-summary, default: full)",
  "project": "string (optional, filter by project path)",
  "cwd": "string (optional, auto-detect project from working directory)",
  "model": "string (optional, enum: nomic|qwen3|bge-m3)",
  "asOf": "string (optional, valid-time timestamp for historical search)"
}
```

**Returns**: Ranked search results with citations, confidence scores, and source paths.

---

#### `oracle_search_chain`
**Group**: search | **Read-Only**: ❌ | **Status**: ✅ ACTIVE

Run iterative vector search over linked results, expanding from the best hit on each hop.

**Input Parameters**:
```json
{
  "query": "string (required)",
  "maxHops": "number (optional, default: 3, min: 1)",
  "breadth": "number (optional, default: 5, min: 1)",
  "model": "string (optional, embedding model key)"
}
```

**Returns**: Multi-hop chain search results with trace IDs and hop information.

---

#### `oracle_read`
**Group**: search | **Read-Only**: ✅ | **Status**: ✅ ACTIVE

Read full content of an Oracle document by file path or document ID.

**Input Parameters**:
```json
{
  "file": "string (required)",
  "id": "string (optional, document UUID)"
}
```

**Returns**: Complete document content with metadata (path, type, concepts, updated_at).

---

#### `oracle_list`
**Group**: search | **Read-Only**: ✅ | **Status**: ✅ ACTIVE

List all documents in Oracle knowledge base. Browse without searching.

**Input Parameters**:
```json
{
  "type": "string (optional, enum: principle|pattern|learning|retro|all)",
  "limit": "number (optional, default: 20)",
  "offset": "number (optional, default: 0)"
}
```

**Returns**: Paginated document list with summaries and metadata.

---

#### `oracle_concepts`
**Group**: search | **Read-Only**: ✅ | **Status**: ✅ ACTIVE

List all concept tags in the Oracle knowledge base with document counts.

**Input Parameters**:
```json
{
  "limit": "number (optional, default: 50)"
}
```

**Returns**: Concept tags ranked by usage count.

---

#### `oracle_ask`
**Group**: search | **Read-Only**: ✅ | **Status**: ✅ ACTIVE

Ask Oracle for a grounded answer over memory/search with citations.

**Input Parameters**:
```json
{
  "q": "string (required, question)",
  "question": "string (optional, alias for 'q')",
  "limit": "number (optional, default: 5)"
}
```

**Returns**: Grounded answer with citations, citation indexes, warnings, evidence flags, and sources.

---

### Knowledge Management

#### `oracle_learn`
**Group**: knowledge | **Read-Only**: ❌ | **Status**: ✅ ACTIVE

Add a new pattern or learning to the Oracle knowledge base.

**Input Parameters**:
```json
{
  "pattern": "string (required, markdown content)",
  "title": "string (optional, defaults to first line)",
  "type": "string (optional, enum: principle|pattern|learning|retro, default: learning)",
  "project": "string (optional, ghq project path)",
  "tags": "array<string> (optional, concept tags)",
  "frontmatter": "string (optional, YAML metadata)"
}
```

**Returns**: Created document with ID, path, and metadata.

---

#### `oracle_supersede`
**Group**: knowledge | **Read-Only**: ❌ | **Status**: ✅ ACTIVE

Mark an old learning/document as superseded by a newer one (preserves both).

**Input Parameters**:
```json
{
  "oldId": "string (required, UUID of document to supersede)",
  "newId": "string (required, UUID of new document)",
  "reason": "string (optional, explanation)"
}
```

**Returns**: Supersession record with timestamps.

---

#### `oracle_stats`
**Group**: knowledge | **Read-Only**: ✅ | **Status**: ✅ ACTIVE

Get Oracle knowledge base statistics and health status.

**Input Parameters**:
```json
{}
```

**Returns**: Document counts by type, indexing status, vector DB health, embedder status, and provider.

---

#### `oracle_research_note`
**Group**: knowledge | **Read-Only**: ❌ | **Status**: ✅ ACTIVE

Store a Thor/Stormforge research or dev artifact as searchable learning memory.

**Input Parameters**:
```json
{
  "title": "string (required)",
  "content": "string (required, markdown)",
  "artifact_type": "string (optional, e.g., 'bug', 'feature', 'refactor')",
  "tags": "array<string> (optional)"
}
```

**Returns**: Learning document with indexing status.

---

### Session Management

#### `oracle_recap`
**Group**: oracle | **Read-Only**: ✅ | **Status**: ✅ ACTIVE

Emit a compact session-start Oracle wake-up context: identity plus top memories by heat/confidence.

**Input Parameters**:
```json
{
  "limit": "number (optional, 1-20, default: 8)",
  "maxTokens": "number (optional, 200-1200, default: 900)"
}
```

**Returns**: Ranked memories grouped by project with confidence scores and heat metrics.

---

#### `oracle_handoff`
**Group**: session | **Read-Only**: ❌ | **Status**: ✅ ACTIVE

Write session context to the Oracle inbox for future sessions.

**Input Parameters**:
```json
{
  "content": "string (required, markdown session notes)",
  "title": "string (optional, defaults to timestamp)"
}
```

**Returns**: Handoff document path and metadata.

---

#### `oracle_inbox`
**Group**: session | **Read-Only**: ✅ | **Status**: ✅ ACTIVE

List and preview pending handoff files from the Oracle inbox.

**Input Parameters**:
```json
{
  "limit": "number (optional, default: 20)",
  "offset": "number (optional, default: 0)"
}
```

**Returns**: Handoff files sorted newest-first with previews.

---

### Reflection & Integrity

#### `oracle_reflect`
**Group**: oracle | **Read-Only**: ✅ | **Status**: ✅ ACTIVE

Get a random principle or learning for reflection.

**Input Parameters**:
```json
{}
```

**Returns**: Random principle/pattern with full content and metadata.

---

#### `oracle_verify`
**Group**: standalone | **Read-Only**: ❌ | **Status**: ✅ ACTIVE

Verify knowledge base integrity: compare `ψ/` files on disk vs DB index.

**Input Parameters**:
```json
{
  "check": "string (optional, enum: missing|orphaned|drifted|all, default: all)",
  "full": "boolean (optional, return full file contents in report)"
}
```

**Returns**: Integrity report with missing (on disk, not indexed), orphaned (in DB, file gone), and drifted (file changed since index) documents.

---

### Discussion Threads

#### `oracle_thread`
**Group**: forum | **Read-Only**: ❌ | **Status**: ✅ ACTIVE

Send a message to an Oracle discussion thread. Creates new or continues existing.

**Input Parameters**:
```json
{
  "message": "string (required)",
  "threadId": "number (optional, continue existing thread)",
  "title": "string (optional, for new threads)",
  "role": "string (optional, enum: human|claude, default: human)",
  "model": "string (optional, Claude model name)",
  "reopen": "boolean (optional, default: false, required to re-open closed threads)"
}
```

**Returns**: Thread ID, message ID, status, Oracle auto-response (if generated), and GitHub issue URL.

---

#### `oracle_threads`
**Group**: forum | **Read-Only**: ✅ | **Status**: ✅ ACTIVE

List Oracle discussion threads. Filter by status.

**Input Parameters**:
```json
{
  "status": "string (optional, enum: active|answered|pending|closed)",
  "limit": "number (optional, default: 20)",
  "offset": "number (optional, default: 0)"
}
```

**Returns**: Thread summaries with message counts, last message preview, and issue URLs.

---

#### `oracle_thread_read`
**Group**: forum | **Read-Only**: ✅ | **Status**: ✅ ACTIVE

Read full message history from a thread.

**Input Parameters**:
```json
{
  "threadId": "number (required)",
  "limit": "number (optional, max messages to return)"
}
```

**Returns**: Full thread with all messages, roles, timestamps, and thread metadata.

---

#### `oracle_thread_update`
**Group**: forum | **Read-Only**: ❌ | **Status**: ✅ ACTIVE

Update thread status (close, reopen, mark answered/pending).

**Input Parameters**:
```json
{
  "threadId": "number (required)",
  "status": "string (required, enum: active|closed|answered|pending)"
}
```

**Returns**: Updated thread status and metadata.

---

### Tracing & Exploration

#### `oracle_trace`
**Group**: trace | **Read-Only**: ❌ | **Status**: ✅ ACTIVE

Log a trace session with dig points (files, commits, issues). Captures `/trace` results for future exploration.

**Input Parameters**:
```json
{
  "query": "string (required, what was traced)",
  "queryType": "string (optional, enum: general|project|pattern|evolution, default: general)",
  "foundFiles": "array<{path, type, matchReason, confidence}> (optional)",
  "foundCommits": "array<{hash, shortHash, date, message}> (optional)",
  "foundIssues": "array<{number, title, state, url}> (optional)",
  "foundRetrospectives": "array<string> (optional, file paths)",
  "foundLearnings": "array<string> (optional, file paths)",
  "scope": "string (optional, enum: project|cross-project|human)",
  "parentTraceId": "string (optional, parent trace UUID for dig chains)",
  "project": "string (optional, ghq format)",
  "agentCount": "number (optional)",
  "durationMs": "number (optional)"
}
```

**Returns**: Trace UUID, distillation status, and stored metadata.

---

#### `oracle_trace_list`
**Group**: dig | **Read-Only**: ✅ | **Status**: ✅ ACTIVE

List recent traces with optional filters.

**Input Parameters**:
```json
{
  "query": "string (optional, filter by query content)",
  "project": "string (optional, filter by project)",
  "status": "string (optional, enum: raw|reviewed|distilling|distilled)",
  "depth": "number (optional, filter by recursion depth)",
  "limit": "number (optional, default: 20)",
  "offset": "number (optional, default: 0)"
}
```

**Returns**: Trace summaries sorted by date with query type and scope.

---

#### `oracle_trace_get`
**Group**: dig | **Read-Only**: ✅ | **Status**: ✅ ACTIVE

Get full details of a specific trace including all dig points.

**Input Parameters**:
```json
{
  "traceId": "string (required, UUID)",
  "includeChain": "boolean (optional, include parent/child trace chain, default: false)"
}
```

**Returns**: Complete trace with all dig points, metadata, and optional chain links.

---

#### `oracle_trace_link`
**Group**: dig | **Read-Only**: ❌ | **Status**: ✅ ACTIVE

Link two traces as a chain (prev → next). Creates bidirectional navigation.

**Input Parameters**:
```json
{
  "prevTraceId": "string (required, UUID of first trace)",
  "nextTraceId": "string (required, UUID of second trace)"
}
```

**Returns**: Link confirmation with chain position information.

---

#### `oracle_trace_unlink`
**Group**: dig | **Read-Only**: ❌ | **Status**: ✅ ACTIVE

Remove a link between traces. Breaks the chain in the specified direction.

**Input Parameters**:
```json
{
  "traceId": "string (required, UUID)",
  "direction": "string (required, enum: prev|next)"
}
```

**Returns**: Unlink confirmation.

---

#### `oracle_trace_chain`
**Group**: dig | **Read-Only**: ✅ | **Status**: ✅ ACTIVE

Get the full linked chain for a trace. Returns all traces in chain and position.

**Input Parameters**:
```json
{
  "traceId": "string (required, UUID of any trace in the chain)"
}
```

**Returns**: Complete chain with ordered trace list and current position.

---

#### `oracle_trace_distill`
**Group**: trace | **Read-Only**: ❌ | **Status**: ✅ ACTIVE

Distill a trace into a Thor/Stormforge awakening and optionally promote to learning memory.

**Input Parameters**:
```json
{
  "traceId": "string (required, UUID)",
  "promote": "boolean (optional, save as learning memory)"
}
```

**Returns**: Distilled summary and learning ID (if promoted).

---

### Oracle Profiles & Utilities

#### `oracle_profile`
**Group**: oracle | **Read-Only**: ✅ | **Status**: ✅ ACTIVE

List or read code-backed Oracle profiles (Thor Oracle, Stormforge, etc.).

**Input Parameters**:
```json
{
  "id": "string (optional, profile id, slug, or name. Omit to list profiles)"
}
```

**Returns**: Profile metadata including capabilities, awakening info, and source.

---

### MCP Tools (Meta)

#### `oracle_mcp_list_tools`
**Group**: mcp | **Read-Only**: ✅ | **Status**: ✅ ACTIVE

MCP-IN: Start an external stdio MCP server and list its advertised tools.

**Input Parameters**:
```json
{
  "command": "string (required, stdio server command)",
  "args": "array<string> (optional, command arguments)",
  "env": "object (optional, environment variables)",
  "cwd": "string (optional, working directory)"
}
```

**Returns**: Server info and list of advertised tools with schemas.

---

#### `oracle_mcp_call`
**Group**: mcp | **Read-Only**: ❌ | **Status**: ✅ ACTIVE

MCP-IN: Call one tool exposed by an external stdio MCP server.

**Input Parameters**:
```json
{
  "command": "string (required, stdio server command)",
  "toolName": "string (required, tool to call)",
  "toolInput": "object (optional, tool arguments)",
  "args": "array<string> (optional, command arguments)",
  "env": "object (optional, environment variables)",
  "cwd": "string (optional, working directory)",
  "timeout": "number (optional, milliseconds)"
}
```

**Returns**: Tool execution result from the external MCP server.

---

## Tool Status Summary

### Tools in Alpha 26.7.26-alpha.227

| Name | Group | RO | Prev Status | Status |
|------|-------|----|----|--------|
| `oracle_recap` | oracle | ✅ | ✅ | ✅ ACTIVE |
| `oracle_search` | search | ✅ | ✅ | ✅ ACTIVE |
| `oracle_search_chain` | search | ❌ | ✅ | ✅ ACTIVE |
| `oracle_read` | search | ✅ | ✅ | ✅ ACTIVE |
| `oracle_list` | search | ✅ | ✅ | ✅ ACTIVE |
| `oracle_concepts` | search | ✅ | ✅ | ✅ ACTIVE |
| `oracle_ask` | search | ✅ | ✅ | ✅ ACTIVE |
| `oracle_learn` | knowledge | ❌ | ✅ | ✅ ACTIVE |
| `oracle_stats` | knowledge | ✅ | ✅ | ✅ ACTIVE |
| `oracle_supersede` | knowledge | ❌ | ✅ | ✅ ACTIVE |
| `oracle_research_note` | knowledge | ❌ | ✅ | ✅ ACTIVE |
| `oracle_handoff` | session | ❌ | ✅ | ✅ ACTIVE |
| `oracle_inbox` | session | ✅ | ✅ | ✅ ACTIVE |
| `oracle_thread` | forum | ❌ | ✅ | ✅ ACTIVE |
| `oracle_threads` | forum | ✅ | ✅ | ✅ ACTIVE |
| `oracle_thread_read` | forum | ✅ | ✅ | ✅ ACTIVE |
| `oracle_thread_update` | forum | ❌ | ✅ | ✅ ACTIVE |
| `oracle_profile` | oracle | ✅ | ✅ | ✅ ACTIVE |
| `oracle_trace` | trace | ❌ | ✅ | ✅ ACTIVE |
| `oracle_trace_list` | dig | ✅ | ✅ | ✅ ACTIVE |
| `oracle_trace_get` | dig | ✅ | ✅ | ✅ ACTIVE |
| `oracle_trace_link` | dig | ❌ | ✅ | ✅ ACTIVE |
| `oracle_trace_unlink` | dig | ❌ | ✅ | ✅ ACTIVE |
| `oracle_trace_chain` | dig | ✅ | ✅ | ✅ ACTIVE |
| `oracle_trace_distill` | trace | ❌ | ✅ | ✅ ACTIVE |
| `oracle_reflect` | oracle | ✅ | ✅ | ✅ ACTIVE |
| `oracle_verify` | standalone | ❌ | ✅ | ✅ ACTIVE |
| `oracle_mcp_list_tools` | mcp | ✅ | ✅ | ✅ ACTIVE |
| `oracle_mcp_call` | mcp | ❌ | ✅ | ✅ ACTIVE |

**Total**: 29 tools

### Comparison to Reference List

**Reference tools** (from previous version):
```
oracle_concepts, oracle_handoff, oracle_inbox, oracle_learn, oracle_list, oracle_read,
oracle_reflect, oracle_search, oracle_stats, oracle_supersede, oracle_thread,
oracle_thread_read, oracle_thread_update, oracle_threads, oracle_trace, oracle_trace_chain,
oracle_trace_get, oracle_trace_link, oracle_trace_list, oracle_trace_unlink, oracle_verify
(+ 8 others: ask, profile, research_note, recap, search_chain, trace, trace_distill, mcp_*)
```

**New in alpha**:
- ✅ All reference tools preserved
- ✅ `oracle_ask` — Grounded Q&A with citations (search group)
- ✅ `oracle_search_chain` — Iterative vector search (search group)
- ✅ `oracle_research_note` — Thor/Stormforge artifact capture (knowledge group)
- ✅ `oracle_trace_distill` — Convert traces to learnings (trace group)
- ✅ `oracle_mcp_call` — External MCP server invocation (mcp group)
- ✅ `oracle_mcp_list_tools` — Discover external MCP tools (mcp group)
- ✅ `oracle_profile` — Code-backed Oracle profiles (oracle group)
- ✅ `oracle_recap` — Session wake-up context (oracle group)

**Removed**: None. All reference tools remain active.

---

## Tools Defined but Not Exposed (Pending)

The following tools are defined in source but **not registered in `mcpTools`** array:

| Name | File | Purpose | Note |
|------|------|---------|------|
| `oracle_schedule_add` | `src/tools/schedule.ts` | Add appointment to shared schedule | Not in MCP manifest |
| `oracle_schedule_list` | `src/tools/schedule.ts` | List calendar events by date | Not in MCP manifest |

**Status**: These appear to be development/experimental and not yet exposed via MCP. Likely landing in a future iteration.

---

## Migration & Breaking Changes

### Schema Changes (v26.6 → v26.7.26-alpha)

**Migration #39**: Federation identity & peer support
- New tables: peer identity keys, peer search integration, peer feed routes
- Env var: `ARRA_PEER_TOKEN` for bearer auth
- New endpoints: `/info`, `/api/identity`, peer query support

**Vector Backend Swappability**
- Now supports per-collection adapter selection (was: global backend)
- Fallback to FTS5-only if embedder unavailable (degraded mode)
- Qdrant now uses stable SHA-256 UUIDs for deterministic upserts

**Unified Plugin System**
- Plugin manifest loader with tier/weight ordering
- Tool groups now support dynamic enable/disable
- Hot-reload via `ORACLE_TOOL_GROUPS_HOT_RELOAD` env var

### No Data Migration Required

- Existing SQLite schema is backward-compatible
- Vector collections auto-adapt to configured backend
- FTS5 index remains present for fallback search

---

## Architecture Notes

### Mode Selection

**Embedded Mode** (default):
- Requires local SQLite + optional vector DB
- MCP stdio server runs in-process
- Best for desktop/CLI use

**HTTP Proxy Mode** (`ORACLE_HTTP_URL` set):
- MCP stdio acts as HTTP client
- Proxies calls to remote HTTP API server
- Useful for multi-machine or containerized setups

### Vector Store Defaults

- **Local**: LanceDB (builtin, no external service needed)
- **Cloud**: Qdrant support with per-collection selection
- **Degraded Mode**: Falls back to FTS5-only if embedder unavailable

### Tool Group Config

- `config.json` or `.arra/config.json` controls which tool groups are enabled
- `disabled_tools` list overrides group settings (opt-out individual tools)
- `enabled_tools` list acts as whitelist (opt-in only specific tools)
- Hot-reloaded by default unless `ORACLE_TOOL_GROUPS_HOT_RELOAD=0`

---

## Debugging

### Health Check

```bash
curl http://localhost:47778/api/health
# Returns: { "status": "ok", "db": "ok", "vector": "ok"|"degraded", "embedder": "..." }
```

### Vector Store Status

```bash
curl http://localhost:47778/api/v1/stats
# Includes: indexing_count, indexed_count, embedder_status, vector_status
```

### MCP Tool Discovery

```bash
# Via HTTP API
curl http://localhost:47778/api/mcp-tools

# Via MCP (oracle_mcp_list_tools)
# Lists tools advertised by this server
```

### CLI Doctor Command

```bash
arra doctor
# Diagnoses: reachability, DB/vector status, adapter config, layered config, MCP mode
```

---

## References

- **Repository**: https://github.com/Soul-Brews-Studio/arra-oracle-v3
- **CHANGELOG**: See `CHANGELOG.md` in repo
- **Docker Hub**: `ghcr.io/soul-brews-studio/arra-oracle-v3:{http|stdio}`
- **MCP Spec**: https://modelcontextprotocol.io

---

*Documentation compiled 2026-07-26 from alpha branch v26.7.26-alpha.227*

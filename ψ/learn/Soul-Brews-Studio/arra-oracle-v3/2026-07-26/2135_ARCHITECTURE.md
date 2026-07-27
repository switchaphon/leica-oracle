# Arra Oracle V3 — Architecture Analysis

**Version**: 26.7.26-alpha.227  
**Date**: 2026-07-26  
**Analysis focus**: TypeScript/Bun MCP memory server  
**Data source**: Checkout at `alpha` branch

---

## Executive Summary

Arra Oracle V3 is a **Bun-native, Docker-first MCP memory server** that provides semantic search, philosophy-aware knowledge management, and unified memory contracts across HTTP, MCP, CLI, and plugin surfaces. A single SQLite + vector store backend powers all interfaces.

- **Runtime**: Bun ≥ 1.2.0
- **Primary distribution**: Docker images (`http` and `stdio` variants)
- **Core transports**: Elysia HTTP server + stdio MCP (Model Context Protocol)
- **Data persistence**: SQLite (local) or D1 (Cloudflare Workers)
- **Vector backends**: LanceDB, Qdrant, sqlite-vec, Chroma, Cloudflare Vectorize, proxy
- **Packaging**: monorepo with `frontend/` workspace (React/Tauri Studio UI) and `workers/mcp` (Cloudflare edge)

---

## Directory Structure

```
arra-oracle-v3/
├── src/                        # Main server source (Bun/TypeScript)
│   ├── index.ts               # MCP entry point (stdio server boot)
│   ├── server.ts              # HTTP server setup (Elysia)
│   ├── vector-server.ts       # Sidecar vector DB server
│   ├── simple-mode.ts         # Minimal UI fallback at /simple
│   ├── config.ts              # Environment variable resolution
│   ├── const.ts               # Constants (database names, paths, defaults)
│   ├── types.ts               # Global type definitions
│   │
│   ├── mcp/                   # MCP server orchestration
│   │   ├── server.ts          # OracleMCPServer (tools registry, dispatcher)
│   │   ├── plugin-runtime.ts  # Unified plugin runtime factory
│   │   ├── plugin-tools.ts    # Plugin-provided MCP tools
│   │   ├── aliases.ts         # Tool name resolution (deprecated name rewrites)
│   │   ├── http-proxy.ts      # HTTP proxy mode (when ORACLE_HTTP_URL set)
│   │   ├── guide.ts           # Guide tool (system information)
│   │   └── tenant.ts          # Tenant ID extraction from MCP args
│   │
│   ├── db/                    # Database layer (Drizzle ORM)
│   │   ├── schema.ts          # Drizzle table definitions
│   │   ├── create.ts          # SQLite/D1 factory
│   │   ├── index.ts           # Global db instance + migrations
│   │   └── seeders/           # Schema initialization (menu items, etc.)
│   │
│   ├── vector/                # Vector/embedding layer
│   │   ├── factory.ts         # Adapter factory (resolves ORACLE_VECTOR_DB)
│   │   ├── types.ts           # VectorStoreAdapter interface
│   │   ├── adapters/          # Concrete implementations
│   │   │   ├── lancedb.ts     # LanceDB (default local)
│   │   │   ├── sqlite-vec.ts  # sqlite-vec adapter
│   │   │   ├── qdrant.ts      # Qdrant gRPC client
│   │   │   ├── chroma-mcp.ts  # Chroma via stdio MCP subprocess
│   │   │   ├── cloudflare.ts  # Cloudflare Vectorize + AI Workers
│   │   │   ├── proxy.ts       # HTTP proxy to remote vector DB
│   │   │   └── turbovec.ts    # TurboVec adapter (experimental)
│   │   ├── embeddings.ts      # Embedding provider abstraction
│   │   ├── providers/         # Embedding backends
│   │   │   ├── ollama.ts      # Ollama (local default)
│   │   │   ├── gemini.ts      # Google Gemini API
│   │   │   └── cloudflare.ts  # @cf/baai/bge-m3 edge embeddings
│   │   ├── config.ts          # Vector configuration loading (vector.json)
│   │   ├── embedder-config.ts # Runtime embedder state
│   │   ├── preflight.ts       # Vector store health check
│   │   ├── runtime-status.ts  # Embedder status reporting
│   │   └── fallback-chain.ts  # Embedder fallback orchestration
│   │
│   ├── tools/                 # MCP tool implementations
│   │   ├── mcp-manifest.ts    # Master tool registry + handlers
│   │   ├── types.ts           # ToolContext, ToolResponse types
│   │   ├── search.ts          # oracle_search (FTS + vector)
│   │   ├── read.ts            # oracle_read (single document fetch)
│   │   ├── learn.ts           # oracle_learn (write/index documents)
│   │   ├── recap.ts           # oracle_recap (document summary)
│   │   ├── ask.ts             # oracle_ask (LLM grounding + vector)
│   │   ├── chain-search.ts    # oracle_chain_search (multi-step)
│   │   ├── list.ts            # oracle_list (filtered document list)
│   │   ├── concepts.ts        # oracle_concepts (entity extraction)
│   │   ├── supersede.ts       # oracle_supersede (versioning)
│   │   ├── handoff.ts         # oracle_handoff (context passing)
│   │   ├── inbox.ts           # oracle_inbox (session messages)
│   │   ├── forum.ts           # oracle_thread* (async conversations)
│   │   ├── trace.ts           # oracle_trace* (lineage tracking)
│   │   ├── oracle.ts          # oracle_profile, oracle_research_note
│   │   ├── reflect.ts         # oracle_reflect (philosophy lookup)
│   │   ├── verify.ts          # oracle_verify (fact checking)
│   │   ├── mcp-in.ts          # oracle_mcp_* (MCP introspection)
│   │   └── __tests__/         # Tool unit tests
│   │
│   ├── routes/                # HTTP route handlers (Elysia apps)
│   │   ├── meta/              # /, /api/endpoints
│   │   ├── health/            # /api/health (liveness probe)
│   │   ├── search/            # /api/v1/search (FTS + vector)
│   │   ├── ask/               # /api/v1/ask (grounding with LLM)
│   │   ├── learn/             # /api/v1/learn (document ingestion)
│   │   ├── read/              # /api/v1/read (fetch by ID)
│   │   ├── concepts/          # /api/v1/concepts (entity management)
│   │   ├── knowledge/         # /api/v1/knowledge (knowledge graph)
│   │   ├── research/          # /api/v1/research (research notes)
│   │   ├── verify/            # /api/v1/verify (fact checking)
│   │   ├── supersede/         # /api/v1/supersede (document versioning)
│   │   ├── vector/            # /api/v1/vector/*, /api/vector-db (search/config)
│   │   ├── menu/              # /api/menu (navigation items + plugins)
│   │   ├── plugins/           # /api/plugins (plugin manifest discovery)
│   │   ├── mcp/               # /api/mcp/tools, /mcp (streamable HTTP-MCP bridge)
│   │   ├── forum/             # /api/forum/threads/* (async conversations)
│   │   ├── traces/            # /api/traces/* (lineage API)
│   │   ├── memory/            # /api/memory (semantic memory contracts)
│   │   ├── vault/             # /api/vault (ψ file access)
│   │   ├── settings/          # /api/settings (runtime config)
│   │   ├── metrics/           # /api/metrics (Prometheus-style)
│   │   ├── export/            # /api/export (OKF, backups)
│   │   ├── dashboard/         # /dashboard (legacy UI routes)
│   │   ├── indexer/           # /api/indexer (CLI status)
│   │   ├── sessions/          # /api/sessions (session management)
│   │   ├── tenants/           # /api/tenants (multi-tenant isolation)
│   │   ├── auth/              # /api/auth (OAuth, token validation)
│   │   ├── canvas/            # /api/canvas (web component surfaces)
│   │   ├── watcher/           # /api/watcher (file system events)
│   │   ├── schedule/          # /api/schedule (cron + background jobs)
│   │   ├── federation/        # /api/federation (Oracle interconnect)
│   │   ├── feed/              # /api/feed (event log)
│   │   └── compat.ts          # Legacy studio route aliases
│   │
│   ├── middleware/            # Elysia middleware stack
│   │   ├── tenant.ts          # Multi-tenant context isolation
│   │   ├── auth.ts            # API token + auth middleware
│   │   ├── cors.ts            # CORS + private network preflight
│   │   ├── compression.ts     # gzip/brotli response encoding
│   │   ├── rate-limiter.ts    # Leaky bucket rate limiting
│   │   ├── request-logger.ts  # Structured logging
│   │   ├── error-handler.ts   # Global error middleware
│   │   ├── timeout.ts         # Request timeout enforcement
│   │   ├── etag.ts            # HTTP caching headers
│   │   ├── security-headers.ts # X-Frame-Options, CSP, etc.
│   │   ├── dedup.ts           # Request deduplication
│   │   ├── db-context.ts      # Request-scoped DB connection
│   │   └── spa.ts             # Single-page app fallback
│   │
│   ├── plugins/               # Unified plugin system
│   │   ├── unified-loader.ts  # Plugin discovery + loading
│   │   ├── unified-manifest.ts # Plugin metadata types
│   │   ├── runtime-routes.ts  # Dynamic route registration
│   │   ├── runtime-reload.ts  # Hot-reload + lifecycle
│   │   ├── unified-server.ts  # Sidecar server spawning
│   │   └── watcher.ts         # Plugin manifest file watcher
│   │
│   ├── vault/                 # ψ/ Markdown vault integration
│   │   ├── handler.ts         # ψ file operations + parsing
│   │   ├── cli.ts             # vault sync/pull/migrate commands
│   │   └── __tests__/         # Vault operation tests
│   │
│   ├── indexer/               # Document ingestion pipeline
│   │   ├── cli.ts             # `arra mine` CLI entry
│   │   ├── batch.ts           # Batch ingest executor
│   │   ├── document-hasher.ts # Deterministic ID generation
│   │   ├── markdown-parser.ts # Frontmatter + content split
│   │   └── __tests__/         # Parser unit tests
│   │
│   ├── search/                # Search orchestration
│   │   ├── fts.ts             # SQLite FTS5 queries
│   │   ├── vector.ts          # Vector DB queries
│   │   ├── fusion.ts          # Hybrid FTS + vector ranking
│   │   └── reranker.ts        # Relevance reranking
│   │
│   ├── learn/                 # Knowledge aggregation
│   │   ├── concepts.ts        # Concept extraction + linking
│   │   ├── entity-linker.ts   # Entity relationship building
│   │   └── consolidation.ts   # Background document consolidation
│   │
│   ├── workers/               # Background job workers
│   │   ├── consolidation.ts   # Document de-duplication
│   │   ├── sleep-consolidation.ts # Scheduled consolidation
│   │   ├── memory-consolidation.ts # Memory tier management
│   │   ├── entity-backfill.ts # Retrospective entity enrichment
│   │   ├── fact-curation.ts   # Fact grounding workers
│   │   └── remote-mcp-teardown.ts # MCP cleanup on shutdown
│   │
│   ├── config/                # Configuration subsystem
│   │   ├── tool-groups.ts     # Tool enablement/disablement
│   │   ├── profiles.ts        # Environment profiles (dev/prod)
│   │   └── validate.ts        # Env var validation schema
│   │
│   ├── middleware/            # Shared middleware utilities
│   ├── middleware/
│   ├── services/              # External service integrations
│   │   ├── file-watcher.ts    # fs.watch abstraction
│   │   └── http-client.ts     # Shared fetch + retry logic
│   │
│   ├── lifecycle/             # Server lifecycle hooks
│   │   ├── startup-context.ts # Boot-time initialization
│   │   ├── shutdown.ts        # Graceful shutdown coordination
│   │   ├── self-test.ts       # Startup diagnostics
│   │   ├── banner.ts          # Startup message formatting
│   │   └── metrics.ts         # Prometheus metric lifecycle
│   │
│   ├── gateway/               # API gateway + routing
│   │   └── index.ts           # Gateway plugin
│   │
│   ├── oracles/               # Oracle-specific logic (philosophy, reasoning)
│   │   ├── philosophy.ts      # Core 5 principles
│   │   └── reasoning.ts       # Decision-making utilities
│   │
│   ├── lib/                   # Shared utilities
│   │   ├── hash.ts            # Content hashing
│   │   ├── env.ts             # Process env helpers
│   │   ├── time.ts            # Timestamp utilities (GMT+7)
│   │   └── types.ts           # Type guards + assertions
│   │
│   └── integration/           # Integration test suite
│       ├── http.test.ts       # HTTP contract tests (Elysia)
│       ├── mcp.test.ts        # MCP tool invocation tests
│       └── database.test.ts   # DB schema + migration tests
│
├── cli/                       # CLI tooling (separate workspace)
│   ├── src/
│   │   ├── cli.ts             # Main CLI dispatcher
│   │   ├── mine.ts            # `arra mine` (ingestion)
│   │   ├── search.ts          # `arra search` (CLI search)
│   │   ├── learn.ts           # `arra learn` (manual indexing)
│   │   ├── export.ts          # `arra export` (backup/OKF)
│   │   └── commands/          # Subcommand implementations
│   └── package.json
│
├── frontend/                  # React/Tauri Studio UI (workspace)
│   ├── src/
│   │   ├── index.html         # Shell HTML
│   │   ├── main.tsx           # React root
│   │   ├── App.tsx            # Router + layout
│   │   ├── styles.css         # Tailwind + project tokens
│   │   ├── components/
│   │   │   ├── AppShell.tsx   # Chrome (navbar, sidebar)
│   │   │   ├── VectorSearchWidget.tsx
│   │   │   ├── McpToolBrowser.tsx
│   │   │   └── ...other components
│   │   ├── pages/
│   │   │   ├── Menu.tsx       # /menu route
│   │   │   ├── Plugins.tsx    # /plugins route
│   │   │   ├── Vector.tsx     # /vector route
│   │   │   ├── MCP.tsx        # /mcp route
│   │   │   ├── Settings.tsx   # /settings route
│   │   │   └── Dashboard.tsx  # / (home) route
│   │   ├── hooks/
│   │   │   ├── useApi.ts      # API fetch wrapper
│   │   │   ├── useSettings.ts # Settings state
│   │   │   └── useVectorSearch.ts
│   │   └── lib/
│   │       └── api.ts         # Shared API client
│   ├── src-tauri/            # Tauri desktop wrapper (optional)
│   │   └── src/tauri.rs
│   ├── vite.config.ts        # Vite dev server config
│   └── package.json
│
├── workers/                   # Cloudflare Workers (monorepo workspaces)
│   ├── mcp/                   # Cloudflare MCP Worker
│   │   ├── src/index.ts       # MCP server on Workers (stdio HTTP bridge)
│   │   ├── wrangler.jsonc     # Cloudflare deployment config
│   │   └── package.json
│   ├── studio/                # Studio UI proxy Worker
│   │   └── wrangler.jsonc
│   └── federation/            # Oracle-to-Oracle bridge Worker
│       └── wrangler.jsonc
│
├── bin/
│   ├── arra.ts               # CLI entry point (serve/mcp/mine commands)
│   └── mcp.ts                # Alternative MCP entry
│
├── packages/                  # Shared packages (canvas plugins, etc.)
│   └── canvas-plugins/src    # Web component surface
│
├── tests/                     # Test suite (separate from src/)
│   ├── http/                  # HTTP contract tests (clustered by endpoint)
│   │   ├── core.test.ts       # Live server contract (opt-in)
│   │   ├── response-format/   # Response envelope tests
│   │   ├── health/            # /api/health tests
│   │   ├── search/            # /api/v1/search tests
│   │   └── ...other endpoints
│   ├── cli/                   # CLI behavior tests
│   ├── storage/               # Storage layer tests
│   ├── plugins/               # Plugin system tests
│   └── build/                 # Build gate tests (test-scope.test.ts)
│
├── docs/                      # User + developer documentation
│   ├── QUICKSTART.md          # 10-minute getting started
│   ├── API.md                 # HTTP API reference
│   ├── API-REFERENCE-INDEX.md
│   ├── architecture.md        # High-level design
│   ├── FEDERATION.md          # Oracle interconnect
│   ├── DEPLOY-DIGITALOCEAN.md
│   ├── deploy-cloudflare.md   # Cloudflare Workers deploy
│   ├── deploy-cloudflare-mcp.md
│   ├── cloudflare-vector-backend.md
│   ├── DB-MIGRATIONS.md
│   ├── HUGINN-CAPTURE.md      # Huginn + webhook capture
│   ├── HUGINN-MUNINN.md       # Agent federation
│   ├── TROUBLESHOOTING.md
│   ├── SIMPLE-MODE-SPEC.md
│   ├── MIDDLEWARE.md
│   ├── MENU-AUTOLOAD.md
│   ├── MULTI-STUDIO.md
│   ├── MORNING-TAPE-TEMPLATE.md
│   ├── FAQ.md
│   ├── INSTALL.md
│   ├── plugin-quickstart.md
│   ├── plugin-interface-spec.md
│   └── README.md              # Docs index
│
├── scripts/
│   ├── calver.ts             # Calendar versioning (YY.M.D-alpha.HMM)
│   ├── seed-test-data.ts
│   ├── ingest-fleet-vault.ts
│   ├── huginn-capture-hook.ts
│   ├── huginn-sweep.ts
│   ├── export-openapi.ts
│   ├── vault-rsync.sh
│   ├── setup.sh
│   └── bge-m3-drift-benchmark.ts
│
├── benchmarks/
│   ├── run-all.ts
│   ├── search-latency.ts
│   └── embedding-throughput.ts
│
├── .claude/
│   ├── CLAUDE.md             # Project conventions (≤250 lines/file, test layout, Elysia)
│   ├── AGENTS.md             # Role + skill matrix
│   ├── agents/               # Per-role agent instructions (chrome.md, flux.md, etc.)
│   └── settings.json         # Claude Code settings
│
├── .mcp.json                 # MCP server metadata (for discovery)
├── .omx/project-memory.json  # OMX execution memory
├── package.json              # Root workspace config
├── bun.lockb                 # Bun lock file (binary)
├── tsconfig.json             # TypeScript config
├── drizzle.config.ts         # Drizzle ORM config
├── vite.config.ts            # Vite dev server (frontend proxy)
├── playwright.config.ts      # E2E test config
├── vitest.config.ts          # Vitest unit test config
├── wrangler.jsonc            # Cloudflare Workers config
├── vercel.json               # Vercel deployment config
├── CHANGELOG.md
├── README.md
├── DESIGN.md                 # Product design (UI/UX principles)
├── TIMELINE.md
├── CONTRIBUTING.md
├── MORNING-TAPE.md           # Daily standup template
└── LICENSE (BUSL-1.1)
```

---

## Entry Point: MCP Server Boot (`src/index.ts`)

```typescript
// src/index.ts (lines 1-35)
import { OracleMCPServer } from './mcp/server.ts';

export async function main(): Promise<void> {
  const readOnly = process.env.ORACLE_READ_ONLY === 'true' || process.argv.includes('--read-only');
  const server = new OracleMCPServer({ readOnly });
  
  try {
    console.error('[Startup] Pre-connecting to vector store...');
    await server.preConnectVector();
  } catch (e) {
    console.error('[Startup] Vector store pre-connect failed:', e.message);
  }
  
  await server.run();
}

if (import.meta.main) main().catch(console.error);
```

**Invocation**:
- Direct: `bun src/index.ts` (stdio MCP server)
- Aliased: `arra-oracle mcp` (via `bin/arra.ts`)
- Docker: `ghcr.io/.../arra-oracle-v3:stdio` (entrypoint overridden)

**Bootstrap sequence**:
1. Create `OracleMCPServer` with options (`readOnly`, `toolGroups`, `embeddedDeps`, etc.)
2. Pre-connect vector store (probe Ollama/Gemini/Cloudflare)
3. Attach stdio transport and listen for MCP requests (no HTTP)

---

## MCP Server Orchestration (`src/mcp/server.ts`)

The `OracleMCPServer` class:

### Architecture (lines 28-241)

```typescript
export class OracleMCPServer {
  private server: Server;  // @modelcontextprotocol/sdk Server
  private sqlite: Database | null = null;
  private db: BunSQLiteDatabase<typeof schema> | null = null;
  private vectorStore: VectorStoreAdapter | null = null;
  private vectorStatus: 'connected' | 'degraded' | 'unknown' = 'unknown';
  private unifiedRuntime: McpPluginRuntime;  // Plugin registry
  private disabledTools = new Set<string>();
  private explicitEnabledTools = new Set<string>();
  
  constructor(options: OracleMCPServerOptions = {}) {
    this.readOnly = options.readOnly ?? false;
    this.toolAllowlist = options.toolAllowlist ? new Set(options.toolAllowlist) : null;
    
    // Load tool group config (which tools are enabled/disabled)
    const groupConfig = options.toolGroups ?? loadToolGroupConfig(this.repoRoot);
    this.applyToolGroupConfig(groupConfig);
    
    // Create MCP Server instance
    this.server = new Server({ name: 'Arra Oracle', version: pkg.version }, { capabilities: { tools: {} } });
    
    // Initialize embedded resources (DB + vector store) unless in HTTP proxy mode
    if (!this.oracleApiBase) this.embeddedReady = this.initEmbedded();
    
    this.setupHandlers();
  }
}
```

### Tool Registration: `ListToolsRequestSchema`

```typescript
// Line 183-185
this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: (await this.availableTools()).map(toMcpToolDefinition),
}));
```

1. **`availableTools()`** (lines 168-180):
   - Get all tools from MCP manifest + plugins
   - Filter by tool groups (enabled/disabled config)
   - Respect read-only mode (don't expose write tools)
   - Apply allowlist if set

2. **Tool filtering layers**:
   - **Disabled groups**: `tool_groups.json` sets `oracle: false` → all oracle tools hidden
   - **Explicit disabled**: `disabled_tools: ["oracle_learn"]`
   - **Explicit enabled**: `enabled_tools: ["oracle_search"]` (whitelist mode)
   - **Read-only**: Tool with `readOnly: false` is hidden if `ORACLE_READ_ONLY=true`

### Tool Invocation: `CallToolRequestSchema`

```typescript
// Lines 187-213
this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const toolName = resolveInboundToolName(request.params.name);  // Handle aliases
  const tool = (await this.toolRegistry()).get(toolName);
  
  if (!tool) return errorResponse(`Unknown tool: ${toolName}`);
  if (this.isDisabled(tool)) return errorResponse(`Tool "${toolName}" is disabled`);
  if (this.readOnly && tool.readOnly === false) return errorResponse(`Read-only mode`);
  
  try {
    const rawArgs = request.params.arguments ?? {};
    const tenantId = tenantIdFromMcpArgs(rawArgs);
    const args = stripMcpTenantArgs(rawArgs);
    
    // Check if HTTP proxy mode is active
    const proxied = await proxyToolCall(this.oracleApiBase, toolName, args, tenantId);
    if (proxied) return proxied;  // Delegate to remote server
    
    // Embedded mode: run tool directly
    return await runWithTenant(tenantId, () =>
      tool.handler(args, { version: this.version, getToolCtx: () => this.getToolCtx() })
    );
  } catch (error) {
    return errorResponse(`Error: ${error.message}`);
  }
});
```

**Key features**:
- **Tenant isolation**: Extract tenant ID from `_oracle_tenant` arg, run tool logic in scoped context
- **HTTP proxy**: If `ORACLE_HTTP_URL` is set, forward all tool calls to remote HTTP server
- **Error handling**: Catch exceptions, return MCP-compatible error response

### Transport: Stdio

```typescript
// Line 231-235
async run(): Promise<void> {
  const transport = new StdioServerTransport();
  await this.connect(transport);
  console.error('Arra Oracle MCP Server running on stdio (FTS5 mode)');
}
```

Uses `@modelcontextprotocol/sdk/server/stdio.js`:
- Reads messages from stdin (MCP JSON-RPC)
- Writes responses to stdout
- Logs to stderr
- Called by Claude, desktop clients, Docker

---

## Database Layer (`src/db/`)

### Schema (`src/db/schema.ts`)

**Core tables** (Drizzle ORM + SQLite):

| Table | Purpose | Key fields |
|-------|---------|------------|
| `oracle_documents` | Primary knowledge store | id, tenantId, type, sourceFile, concepts, validTime, supersededBy, usageCount, lastAccessedAt |
| `oracle_fts` | Full-text search index | id, content, concepts |
| `oracle_memories` | Memory tier system | id, tenantId, tier (hot/warm/cold), heatScore, validFrom/To, supersededBy |
| `oracle_entity_links` | Entity relationships | documentId, entity, entityKey, weight |
| `oracle_pointer_index` | Reverse index (kind→docIds) | kind, key, docIds (JSON array) |
| `indexing_status` | Ingestion progress | isIndexing, progressCurrent/Total, error |
| `indexing_jobs` | Vector job queue | docId, modelKey, status, attempts, error |
| `vector_index_manifest` | Embedding metadata | chunkId, sourceFile, modelKey, contentHash |
| `search_log` | Search analytics | query, tenantId, mode (fts/vector/hybrid), resultsCount, searchTimeMs |
| `consult_log` | Philosophy consultation log | decision, principlesFound, patternsFound |
| `learnLog` | Indexing event log | documentId, tenantId, patternPreview |

**Tenant isolation**:
- Most tables have `tenantId` field with `DEFAULT 'default'`
- Indexes on `(tenantId, ...)` for scoped queries
- Middleware strips/validates tenant context

### Database Creation (`src/db/create.ts`)

```typescript
export function createDatabase(dbPath: string) {
  const sqlite = new Database(dbPath);
  sqlite.exec('PRAGMA journal_mode = WAL');  // Write-ahead logging
  sqlite.exec('PRAGMA synchronous = NORMAL');
  const db = drizzle(sqlite, { schema });
  return { sqlite, db };
}
```

**Initialization**:
1. Opens/creates SQLite file at `$ORACLE_DATA_DIR/oracle.db` (default)
2. Enables WAL mode (concurrent reads + writes)
3. Wraps in Drizzle ORM
4. Migration runs on first boot (via `drizzle-kit migrate`)

### Migrations

Drizzle manages schema versions:
```bash
bun run db:generate  # Create new migration
bun run db:migrate   # Apply pending migrations
bun run db:push      # Direct push (dev only)
```

Stored in `drizzle/` directory. Example: `drizzle/0001_init.sql`.

---

## Vector/Embedding Layer (`src/vector/`)

### Architecture

The vector layer is **pluggable**. Runtime selects adapter based on `ORACLE_VECTOR_DB` env var:

```typescript
// src/vector/factory.ts (line 65-107)
export function createVectorStore(config: VectorStoreConfig = {}): VectorStoreAdapter {
  const type = (process.env.ORACLE_VECTOR_DB || 'lancedb').toLowerCase();
  
  switch (type) {
    case 'sqlite-vec': { /* SqliteVecAdapter */ }
    case 'lancedb': { /* LanceDBAdapter */ }
    case 'qdrant': { /* QdrantAdapter */ }
    case 'cloudflare-vectorize': { /* CloudflareVectorStore */ }
    case 'proxy': { /* ProxyVectorAdapter */ }
    case 'turbovec': { /* TurboVecAdapter */ }
    case 'chroma':
    default: { /* ChromaMcpAdapter */ }
  }
}
```

### Supported Backends

| Backend | Transport | Default embedder | Deployment | Notes |
|---------|-----------|------------------|------------|-------|
| **LanceDB** | Local file (Arrow) | Ollama | Docker (local) | Default; fast hybrid search |
| **sqlite-vec** | SQLite extension | Ollama | Docker (local) | Lightweight; no external deps |
| **Qdrant** | HTTP/gRPC | Ollama | Docker (sidecar) or cloud | Production vector DB |
| **Cloudflare Vectorize** | HTTP (Cloudflare API) | @cf/baai/bge-m3 (Workers AI) | Cloudflare Workers | Edge embeddings + serverless |
| **Chroma** | stdio MCP subprocess | Ollama or local | Docker (optional sidecar) | Legacy; now via MCP bridge |
| **Proxy** | HTTP to remote vector server | Remote | Multi-node federated | Points to another Oracle instance |
| **TurboVec** | HTTP | Local | Experimental | Streaming vector DB |

### Vector Store Adapter Interface

```typescript
// src/vector/types.ts
export interface VectorStoreAdapter {
  name: string;
  search(query: string, limit: number, filters?: Record<string, unknown>): Promise<VectorSearchResult[]>;
  upsert(documentId: string, chunks: { text: string; metadata: Record<string, unknown> }[]): Promise<void>;
  delete(documentId: string): Promise<void>;
  connect(): Promise<void>;
  close(): Promise<void>;
}

export interface VectorSearchResult {
  documentId: string;
  score: number;
  chunk: string;
  metadata: Record<string, unknown>;
}
```

### Embedding Providers

```typescript
// src/vector/embeddings.ts
export interface EmbeddingProvider {
  embed(text: string): Promise<number[]>;
  embeddingDimensions(): number;
  provider(): string;
}
```

**Supported providers** (via `ORACLE_EMBEDDER` env var):

| Provider | Endpoint | Auth | Dimensions | Fallback chain |
|----------|----------|------|------------|-----------------|
| **ollama** (default) | `http://localhost:11434` | None | 384 (bge-m3) | Primary local |
| **gemini** | `https://generativelanguage.googleapis.com` | API key | 768 | `GOOGLE_API_KEY` env |
| **cloudflare** | Workers AI binding | Cloudflare account | 1536 | Edge-only |
| **none** | Disabled | N/A | 0 | FTS5-only fallback |

**Fallback chain** (line 50-63):
- Try primary embedder first
- If unavailable, cascade to fallback list
- If all fail, degrade to FTS5-only (`vectorStatus: 'degraded'`)

Example:
```bash
ORACLE_EMBEDDER=gemini \
ORACLE_EMBEDDER_FALLBACK=ollama,none \
GOOGLE_API_KEY=sk-xxx \
bun src/index.ts
```

Tries: Gemini → Ollama → FTS5-only

### Vector Configuration File

Optional `$ORACLE_DATA_DIR/vector.json`:

```json
{
  "collections": {
    "bge-m3": {
      "model": "bge-m3",
      "adapter": "lancedb",
      "embedding_provider": "ollama"
    }
  },
  "storage": {
    "services": {
      "qdrant-prod": {
        "type": "qdrant",
        "url": "http://qdrant:6333",
        "api_key": "secret"
      }
    }
  }
}
```

---

## Route Layer (`src/routes/`)

Routes are **modular Elysia sub-apps**, composed in `src/server.ts` (lines 119+).

### Route groups

**Search & retrieval**:
- `search/`: `/api/v1/search` (FTS5 + vector hybrid)
- `read/`: `/api/v1/read` (single document fetch)
- `ask/`: `/api/v1/ask` (LLM grounding + retrieval)
- `concepts/`: `/api/v1/concepts` (entity management)
- `knowledge/`: `/api/v1/knowledge` (knowledge graph)

**Write & indexing**:
- `learn/`: `/api/v1/learn` (document ingestion)
- `indexer/`: `/api/indexer` (CLI status + control)
- `supersede/`: `/api/v1/supersede` (versioning)

**Memory & reasoning**:
- `memory/`: `/api/memory` (semantic memory contracts)
- `research/`: `/api/v1/research` (research notes)
- `verify/`: `/api/v1/verify` (fact checking)

**Collaboration**:
- `forum/`: `/api/forum/threads/*` (async conversations)
- `traces/`: `/api/traces/*` (lineage + context chains)
- `schedule/`: `/api/schedule` (background jobs + cron)

**System**:
- `health/`: `/api/health` (liveness probe + version)
- `menu/`: `/api/menu` (navigation items + plugin discovery)
- `plugins/`: `/api/plugins` (plugin manifests)
- `vector/`: `/api/v1/vector/*` (search config + status)
- `metrics/`: `/api/metrics` (Prometheus-style counters)
- `mcp/`: `/api/mcp/tools` + `/mcp` (streamable MCP bridge)
- `settings/`: `/api/settings` (runtime configuration)

**Storage & federation**:
- `vault/`: `/api/vault` (ψ/ file access)
- `federation/`: `/api/federation` (Oracle-to-Oracle bridge)
- `export/`: `/api/export` (OKF backups)

**Handlers**:

Most routes follow this pattern:

```typescript
export const searchRoutes = new Elysia({ prefix: '/api/v1' })
  .post('/search', async ({ body, set, request }) => {
    const { q, mode = 'hybrid', limit = 10 } = body;
    // Fetch tool context (DB + vector store)
    const ctx = await getToolCtx();
    
    // Hybrid search (FTS5 + vector)
    const results = await hybridSearch(ctx, q, mode, limit);
    
    return { results };
  }, {
    body: t.Object({ q: t.String(), mode: t.Optional(t.String()), limit: t.Optional(t.Number()) })
  })
  .get('/search', ({ query: { q, limit } }) => {
    // Shorthand GET endpoint
  });
```

---

## Storage & Data Directory

### `ORACLE_DATA_DIR` Resolution

**Priority** (line 48 in `src/config.ts`):
1. `ORACLE_DATA_DIR` env var
2. `$HOME/.arra-oracle-v2/` (hardcoded default)

Inside `ORACLE_DATA_DIR`:
```
~/.arra-oracle-v2/
├── oracle.db               # SQLite main database
├── vector.db/              # LanceDB vector store (dir)
│   ├── _schema.parquet
│   └── .lance/chunks.lance
├── vector.json             # Optional vector config
├── vector-server.json      # Auto-written by vector-server.ts
├── config.json             # Tool groups + settings
├── arra.config.json        # CLI configuration
├── lancedb/                # Alternative: LanceDB multipart storage
├── chromadb/               # (legacy, $HOME/.chroma)
├── ψ/                      # Vault files (Markdown notes)
│   ├── learn/              # Deep learning docs
│   ├── memory/             # Session memory
│   ├── inbox/              # Incoming handoffs
│   ├── archive/            # Completed work
│   └── retrospectives/     # Session reviews
├── feed.jsonl              # Event log (one JSON per line)
├── schedule.json           # Cron + background jobs
└── plugins/                # User plugin files
    ├── my-plugin.wasm
    └── plugin-manifest.json
```

### Configuration Profiles

**`src/config/profiles.ts`**: Auto-apply defaults based on context:

| Profile | Trigger | Defaults |
|---------|---------|----------|
| `docker` | `DOCKER_HOST` env set | Read-only, strict paths |
| `workers` | `CLOUDFLARE_ACCOUNT_ID` set | Use D1 + Vectorize |
| `dev` | `NODE_ENV=development` | Hot-reload, debug logs |
| `prod` | `NODE_ENV=production` | WAL mode, metrics enabled |

Example:
```bash
NODE_ENV=production ORACLE_VECTOR_DB=qdrant bun src/server.ts
# Applies: production profile defaults + explicit qdrant choice
```

---

## HTTP Server (`src/server.ts`)

### Elysia App Composition

```typescript
// Lines 119-250 (truncated)
export function createApp({ unifiedPlugins, runtimeRef, dataDir, vectorUrl }: CreateAppOptions) {
  const app = new Elysia()
    // Middleware stack (order matters)
    .use(createRequestLoggingMiddleware())
    .use(createCorrelationMiddleware())
    .use(createTenantMiddleware())
    .use(createCorsMiddleware())
    .use(createApiVersionHeaderMiddleware())
    .use(createSecurityHeadersMiddleware())
    .use(createBodyLimitMiddleware())
    .use(createApiKeyAuthMiddleware())
    .use(createRateLimiterMiddleware())
    .use(createMetricsLifecycle())
    .use(swagger(createOpenApiSwaggerConfig(pkg.version)))
    .use(createResponseFormatMiddleware())
    .use(createCompressMiddleware())
    .use(createSpaMiddleware())
    .use(createEtagMiddleware())
    
    // Auth gate
    .onBeforeHandle(({ request, set }) => {
      if (isApiPathProtected(pathname) && !isApiAuthorized(request)) {
        set.status = 401;
        return unauthorizedApiResponse();
      }
    })
    
    // Gateway + core routes
    .use(gatewayPlugin(dataDir, vectorUrl))
    .get('/api/health', () => rootCounts())  // Liveness probe
    .use(authRoutes)
    .use(searchRoutes)
    .use(learnRoutes)
    .use(askRoutes)
    .use(vectorRoutes)
    .use(metricsRoutes)
    .use(menuRoutes)
    .use(pluginsRoutes)
    .use(mcpRoutes)
    // ... 40+ route clusters
    .use(createSpaMiddleware());  // SPA fallback to /simple
  
  return app;
}
```

### Server Lifecycle (`src/server.ts` lines 231+)

```typescript
export async function startServer(options: StartServerOptions = {}): Promise<ServerSpec> {
  // 1. Pre-flight checks
  validateStartupEnv();
  
  // 2. Initialize plugins
  const unifiedPlugins = await loadUnifiedPlugins(defaultUnifiedPluginDirs);
  
  // 3. Create app instance
  const app = createApp({ unifiedPlugins });
  
  // 4. Register graceful shutdown
  registerGracefulShutdown(async () => {
    await runShutdownSteps(app);
  });
  
  // 5. Start listening
  const server = app.listen(PORT);
  
  if (options.writePidFile) {
    writePidFile(process.pid, ORACLE_DATA_DIR);
  }
  
  return { port: PORT, fetch: app.fetch.bind(app) };
}
```

**Startup sequence**:
1. Validate env vars (PORT, ORACLE_DATA_DIR, vector backend choice)
2. Create database + connect vector store
3. Load plugins (CLI commands, HTTP routes, MCP tools, menu items)
4. Boot Elysia server on `ORACLE_PORT` (default 47778)
5. Register SIGINT/SIGTERM handlers

**Graceful shutdown** (line 23-24 in server.ts):
- Stop accepting new requests (return 503)
- Wait for in-flight requests to finish
- Close vector store connections
- Close database
- Exit process

---

## Frontend (`frontend/`)

**Separate Vite workspace** (not embedded in MCP server).

### Build and Deployment

```bash
cd frontend && bun run build
# Output: dist/ (minified React bundle)
```

Served by:
- **Docker HTTP image**: Elysia serves `dist/` at `/` (SPA fallback)
- **Tauri desktop**: Embedded web view
- **Cloudflare Workers**: `workers/studio/` proxies API calls + serves frontend

### Key Pages

| Route | Component | Purpose |
|-------|-----------|---------|
| `/menu` | `Menu.tsx` | Navigation items + plugin discovery |
| `/plugins` | `Plugins.tsx` | Installed plugins + capabilities |
| `/vector` | `Vector.tsx` | Vector search widget + status |
| `/mcp` | `MCP.tsx` | Available MCP tools + help |
| `/settings` | `Settings.tsx` | Runtime config + embedder choice |
| `/` | `Dashboard.tsx` | Home + system overview |

### Styling

- **Tailwind CSS** + local utility tokens in `styles.css`
- Dark theme by default (respects `prefers-color-scheme: dark`)
- Glass morphism on sidebar (deliberate design choice per DESIGN.md line 15-18)
- Mobile-first responsive layout

---

## CLI (`cli/src/`)

Separate workspace; compiled to `dist-cli/index.js` for Docker bundling.

### Commands

```bash
arra mine ~/notes          # Ingest folder into oracle.db
arra search "query"        # Search from command line
arra learn < doc.md        # Index a document from stdin
arra export --out backup/  # Backup as OKF bundle
arra okf export            # Export Oracle to OKF v0.1
```

Binaries:
- `arra-oracle` (serves HTTP)
- `arra-oracle mcp` (runs MCP on stdio)
- `arra mine` (ingestion CLI)
- `arra search` (search CLI)

---

## Plugin System (`src/plugins/`)

### Unified Plugin Manifest

Plugins expose a **single manifest** that feeds all surfaces:

```typescript
export interface UnifiedMcpToolManifest {
  name: string;                   // oracle_myfeature
  description: string;
  group: string;                  // 'search' | 'knowledge' | 'system'
  inputSchema: Record<string, any>;
  handler: (input: any, runtime: any) => Promise<ToolResponse>;
  enabledByDefault?: boolean;
  readOnly?: boolean;
}
```

Surfaces fed by same manifest:
- **MCP tools**: Listed in `oracle_mcp_list_tools`
- **HTTP endpoints**: Auto-routed via `createUnifiedPluginRouteMount`
- **CLI commands**: Exposed via `arra <plugin-name> <args>`
- **Menu items**: Discovered via `/api/plugins`

### Plugin Discovery

**Directories scanned** (line 35 in `src/plugins/unified-loader.ts`):
```typescript
export const defaultUnifiedPluginDirs = [
  path.join(ORACLE_DATA_DIR, 'plugins'),
  path.join(REPO_ROOT, 'plugins'),
  path.join(PROJECT_ROOT, 'plugins'),
];
```

**File patterns**:
- `*.wasm` (WASI plugin)
- `plugin.json` or `manifest.json` (static manifest)
- `plugin.ts` (Bun-compiled TypeScript)

### Hot-reload

`src/plugins/watcher.ts` monitors plugin directories:
- On manifest change, reload plugin
- Preserve existing route handlers
- Emit lifecycle hooks (onLoad, onUnload)
- Fail gracefully if plugin crashes

---

## Configuration & Tool Groups

### `$ORACLE_DATA_DIR/config.json`

Controls which MCP tools are advertised:

```json
{
  "oracle": true,
  "search": true,
  "knowledge": false,
  "system": true,
  "disabled_tools": ["oracle_chainSearch", "oracle_verify"],
  "enabled_tools": [],
  "tool_groups_hot_reload": true
}
```

**Hierarchy** (line 72-76 in `src/mcp/server.ts`):
1. **Group-level**: `"knowledge": false` disables all tools in group
2. **Explicit disabled**: `disabled_tools: ["oracle_learn"]` (exception)
3. **Explicit enabled**: `enabled_tools: ["oracle_search"]` (whitelist mode if set)

### Environment Variables (Complete List)

| Variable | Default | Purpose |
|----------|---------|---------|
| `ORACLE_PORT` | 47778 | HTTP server listen port |
| `ORACLE_DATA_DIR` | `~/.arra-oracle-v2` | Persistent storage directory |
| `ORACLE_DB_PATH` | `$ORACLE_DATA_DIR/oracle.db` | SQLite database path |
| `ORACLE_REPO_ROOT` | Auto-detect | Where ψ/ vault lives |
| `ORACLE_VECTOR_DB` | `lancedb` | Vector backend (lancedb, qdrant, sqlite-vec, chroma, proxy, turbovec, cloudflare-vectorize) |
| `ORACLE_VECTOR_DB_PATH` | `$ORACLE_DATA_DIR/vector.db` | Vector store file/dir |
| `ORACLE_EMBEDDER` | `ollama` (if reachable) | Embedding provider (ollama, gemini, cloudflare, none) |
| `ORACLE_EMBEDDER_URL` | `http://localhost:11434` (ollama) | Embedder endpoint |
| `GOOGLE_API_KEY` | unset | Gemini API credentials |
| `QDRANT_URL` | unset | Qdrant server endpoint |
| `QDRANT_API_KEY` | unset | Qdrant authentication |
| `ORACLE_HTTP_URL` | unset | Remote HTTP server (proxy mode) |
| `VECTOR_URL` | Auto-detect from `vector-server.json` | Vector sidecar endpoint |
| `VECTOR_FALLBACK` | `fts5` | Fallback when vector unavailable (fts5, cache, fail) |
| `ORACLE_READ_ONLY` | `false` | Disable write tools |
| `ORACLE_LOG_TARGET` | `stderr` | Log destination (stderr, file, syslog) |
| `ORACLE_TOOL_GROUPS_HOT_RELOAD` | `1` | Watch config.json for changes |
| `DATABASE_URL` | unset | Alternative to `ORACLE_DB_PATH` (sqlite: protocol) |
| `NODE_ENV` | unset | Apply profile defaults (development, production) |
| `DOCKER_HOST` | unset | Docker socket (triggers docker profile) |
| `CLOUDFLARE_ACCOUNT_ID` | unset | Cloudflare Workers auth |
| `CLOUDFLARE_API_TOKEN` | unset | Cloudflare API auth |

---

## Dependencies & Runtime Assumptions

### Key Dependencies

| Package | Purpose | Notes |
|---------|---------|-------|
| `@modelcontextprotocol/sdk` | MCP server + types | v1.29.0 |
| `elysia` | HTTP server (Bun-native) | v1.4.28 |
| `@elysiajs/swagger` | OpenAPI docs + Swagger UI | v1.3.1 |
| `drizzle-orm` | SQL ORM | v0.45.2 |
| `@lancedb/lancedb` | LanceDB vector DB (default) | v0.27.2 |
| `@qdrant/js-client-rest` | Qdrant HTTP client | v1.17.0 |
| `sqlite-vec` | sqlite-vec extension | v0.1.9 |
| `zod` | Schema validation | v3.25.76 |
| `commander` | CLI argument parsing | v14.0.3 |
| `better-sqlite3` | Sync SQLite (dev/test) | v12.9.0 |
| `typescript` | Type checking | v5.7.2 |

### Runtime Assumptions

**Bun ≥ 1.2.0**:
- Native SQLite support (`bun:sqlite`)
- TypeScript transpilation + JSX
- `import.meta.main` detection
- `Bun.file()` + `Bun.env` APIs

**Optional external services**:
- **Ollama**: For local embeddings (default at `http://localhost:11434`)
- **Qdrant**: For scalable vector storage
- **Cloudflare**: Workers AI + D1 + Vectorize (for edge deployment)
- **Google Gemini**: Alternative embedding provider

**Docker**:
- Volumes: `/data` (persistent `ORACLE_DATA_DIR`)
- Port: `47778` (HTTP) or stdin (MCP)
- Base image: Debian/Alpine with Bun pre-installed

---

## Key Design Principles

From DESIGN.md + CLAUDE.md:

1. **One memory core, thin adapters**: All surfaces (HTTP, MCP, CLI, UI) read/write the same SQLite database. No data duplication.

2. **Pluggable vector backends**: Swap embedder + vector DB without code changes (env vars + config file).

3. **Tenant isolation by default**: Every query runs in a tenant context (default `'default'`). Multi-tenant setups just set `_oracle_tenant` in requests.

4. **Graceful degradation**: If embedder unavailable, fall back to FTS5-only search (`vectorStatus: 'degraded'`).

5. **File ≤ 250 lines**: No god-object modules. Each file does one thing.

6. **Test layout mirrors routes**: `tests/http/<cluster>/<endpoint>.test.ts` maps to `src/routes/<cluster>/`.

7. **Bun ≥ 1.2** only: No Node.js-specific APIs. No CommonJS requires.

8. **CalVer always-alpha versioning**: `vYY.M.D-alpha.HMM` per `scripts/calver.ts`. Stable releases only on explicit user direction.

---

## Deployment Topologies

### Local Docker (Recommended)

```bash
docker run --rm -it -p 47778:47778 \
  -v arra-oracle-data:/data \
  -v ~/notes:/notes:ro \
  ghcr.io/soul-brews-studio/arra-oracle-v3:http

# Alongside Ollama sidecar:
docker run --rm -d --name arra-ollama \
  -p 11434:11434 \
  ollama/ollama:latest
```

**Features**: Full-featured, all tools, local storage.

### Cloudflare Workers (Edge)

```bash
# Deploy MCP server
bun run cloudflare:mcp:deploy

# Deploy Studio UI + proxy
bun run cloudflare:studio:deploy
```

**Stack**: Cloudflare D1 (database) + Vectorize (vector) + Workers AI (embeddings).  
**Limitation**: Read-only (`ORACLE_READ_ONLY=1` enforced at edge).

### Kubernetes (Multi-node)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: arra-oracle
spec:
  containers:
  - name: oracle
    image: ghcr.io/.../arra-oracle-v3:http
    ports:
    - containerPort: 47778
    env:
    - name: ORACLE_VECTOR_DB
      value: qdrant
    - name: QDRANT_URL
      value: http://qdrant-svc:6333
    volumeMounts:
    - name: data
      mountPath: /data
  - name: vector-sidecar
    image: ghcr.io/.../arra-oracle-v3:vector
    env:
    - name: ORACLE_VECTOR_DB
      value: lancedb
```

**Features**: Persistent volumes, external Qdrant, sidecar vector server.

---

## Entry Points & Boot Sequences

### MCP Boot (Stdio)

```bash
$ bun src/index.ts
[Startup] Pre-connecting to vector store...
[Startup] Vector store pre-connected successfully
Arra Oracle MCP Server running on stdio
```

**Flow**:
1. `main()` → `new OracleMCPServer()` → `server.run()`
2. Attach `StdioServerTransport` (reads stdin, writes stdout)
3. Load tool registry from `mcpTools` + plugins
4. Listen for `ListToolsRequest` → advertise tools
5. Listen for `CallToolRequest` → dispatch to handler
6. Return MCP-formatted responses

### HTTP Boot

```bash
$ bun src/server.ts
🔮 Arra Oracle HTTP server → http://localhost:47778
```

**Flow**:
1. `startServer()` → validate env → load plugins
2. `createApp()` → compose Elysia middleware stack + routes
3. `app.listen(PORT)`
4. Serve `/` → SPA fallback to `/simple`
5. Serve `/api/**` → route handlers
6. Serve `/api/mcp` → streamable HTTP-MCP bridge

### CLI Boot

```bash
$ arra mine ~/notes
[Indexing] ~/notes/file1.md → doc-abc123
[Indexing] ~/notes/file2.md → doc-def456
Indexed 2 documents in 1.2s
```

**Flow**:
1. `bin/arra.ts` (entry) → dispatch to `cli/src/mine.ts`
2. Scan directory for `.md`, `.mdx`, `.txt`
3. Parse frontmatter + compute content hash
4. Write to SQLite (via Drizzle)
5. Queue vector indexing jobs (async)
6. Print progress + summary

---

## Observability & Debugging

### Health Check

```bash
$ curl http://localhost:47778/api/health
{
  "status": "ok",
  "version": "26.7.26-alpha.227",
  "vectorStatus": "connected",
  "vectorReason": null,
  "embedderProvider": "ollama",
  "documentsCount": 42,
  "ftsIndexedCount": 120,
  "indexing": false
}
```

### Logs

**Stderr** (MCP):
```
[Startup] Pre-connecting to vector store...
[ToolGroups] Disabled groups: knowledge
[MCP Error] Failed to call oracle_search: socket timeout
```

**Correlation headers**:
- Every request gets `X-Correlation-ID` (UUID)
- Logged in `[CorrelationId: xyz]` prefix
- Helps trace multi-hop requests

### Metrics

```bash
$ curl http://localhost:47778/api/metrics
# HELP oracle_search_total Total search requests
# HELP oracle_search_duration_ms Search latency histogram
oracle_search_duration_ms_sum 1234
oracle_search_duration_ms_count 42
oracle_search_duration_ms_bucket{le="100"} 30
oracle_search_duration_ms_bucket{le="1000"} 40
```

Prometheus-compatible metrics at `/api/metrics`.

---

## Key File Paths (Quick Reference)

| Path | Purpose |
|------|---------|
| `src/index.ts` | MCP entry |
| `src/server.ts` | HTTP server |
| `src/mcp/server.ts` | MCP orchestration |
| `src/db/schema.ts` | Database schema |
| `src/vector/factory.ts` | Vector store selection |
| `src/tools/mcp-manifest.ts` | Tool registry |
| `src/routes/search/index.ts` | Search routes |
| `frontend/src/App.tsx` | React router |
| `bin/arra.ts` | CLI entry |
| `tests/http/core.test.ts` | Live contract test (opt-in) |
| `src/config.ts` | Env var resolution |
| `CLAUDE.md` | Project conventions |
| `DESIGN.md` | UI/UX principles |
| `docs/API.md` | HTTP API reference |

---

## Summary

Arra Oracle V3 is a **unified memory system** architected as:

1. **Core**: Single SQLite database + pluggable vector store (LanceDB default)
2. **MCP Server**: Stdio-based tool dispatcher with tenant isolation + HTTP proxy mode
3. **HTTP Server**: Elysia framework with 40+ route clusters (search, learn, forum, metrics, etc.)
4. **CLI**: `arra mine` for ingestion, `arra search` for queries
5. **Frontend**: React/Tauri Studio UI for menu, plugins, vector, MCP browsing
6. **Plugins**: Unified manifest → MCP tools + HTTP routes + CLI commands + menu items
7. **Storage**: SQLite (local) or D1 (Cloudflare Workers)
8. **Embeddings**: Ollama (default) + Gemini + Cloudflare AI fallback chain

All surfaces (HTTP, MCP, CLI, UI) read/write the same database with no duplication. Configuration is via env vars + optional JSON files. Deployment: Docker, Cloudflare Workers, or Kubernetes.

---

**Document generated**: 2026-07-26 21:35 GMT+7  
**Branch**: alpha (v26.7.26-alpha.227)  
**Audience**: Developers, Oracles, deployment operators

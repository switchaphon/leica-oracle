// v1 WITH sessions — the stateful mode. One McpServer per SESSION.
// A counter lives on the instance, so it survives across requests in that session.
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { randomUUID } from "node:crypto";
import { createServer } from "node:http";

const sessions = new Map<string, { transport: StreamableHTTPServerTransport }>();

function build() {
  const instanceId = randomUUID().slice(0, 8);
  let calls = 0;                                    // ← state on the instance
  const s = new McpServer({ name: "v1-stateful", version: "1.30.0" });
  s.registerTool("probe", { description: "reports instance + call count", inputSchema: {} },
    async () => ({ content: [{ type: "text", text: `instance=${instanceId} calls=${++calls}` }] }));
  return s;
}

createServer(async (req, res) => {
  const chunks: Buffer[] = [];
  for await (const c of req) chunks.push(c as Buffer);
  const body = chunks.length ? JSON.parse(Buffer.concat(chunks).toString()) : undefined;
  const sid = req.headers["mcp-session-id"] as string | undefined;

  let entry = sid ? sessions.get(sid) : undefined;
  if (!entry) {
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
      onsessioninitialized: (id) => sessions.set(id, { transport }),
    });
    await build().connect(transport);             // one server bound to this session
    entry = { transport };
  }
  await entry.transport.handleRequest(req, res, body);
}).listen(8810, "127.0.0.1", () => console.log("v1-stateful on 8810"));

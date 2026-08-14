// v2: @modelcontextprotocol/server@2.0.0
// Claim under test: this is the DUAL-ERA package — one handler serving both a modern
// stateless request and a legacy initialize handshake. I asserted that from the
// tarball; this proves or disproves it.
import { createMcpHandler, McpServer } from "@modelcontextprotocol/server";
import { z } from "zod";

const factory = () => {
  const s = new McpServer({ name: "duang-v2", version: "2.0.0" });
  s.registerTool(
    "which_era",
    { description: "Reports the pid and package that served this call.",
      inputSchema: z.object({}) },
    async () => ({ content: [{ type: "text", text: `v2 server@2.0.0 pid=${process.pid}` }] })
  );
  return s;
};

// createMcpHandler returns { fetch, notify, bus, close } — not a bare function.
// It is shaped to drop straight into any fetch-style server.
const handler = createMcpHandler(factory);
const server = Bun.serve({ port: 8801, hostname: "127.0.0.1", fetch: handler.fetch });
console.log(`v2 listening 127.0.0.1:${server.port} pid=${process.pid}`);

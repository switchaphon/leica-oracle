// v1 done CORRECTLY. My first attempt shared one McpServer + one transport across
// requests and 500'd — which is exactly the "one transport per request" rule Ting
// found in the v1 source. In stateless mode v1 requires a NEW server and a NEW
// transport for every request; reusing them throws "Already connected to a transport".
// v2 makes this structural (createMcpHandler takes a factory); v1 leaves it to you.
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { createServer } from "node:http";

function build() {
  const s = new McpServer({ name: "duang-v1", version: "1.30.0" });
  s.registerTool(
    "which_era",
    { description: "Reports the pid and package that served this call.", inputSchema: {} },
    async () => ({ content: [{ type: "text", text: `v1 sdk@1.30.0 pid=${process.pid}` }] })
  );
  return s;
}

createServer(async (req, res) => {
  const server = build();                                            // per request
  const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
  res.on("close", () => { transport.close(); server.close(); });     // per request
  await server.connect(transport);
  const chunks: Buffer[] = [];
  for await (const c of req) chunks.push(c as Buffer);
  const body = chunks.length ? JSON.parse(Buffer.concat(chunks).toString()) : undefined;
  await transport.handleRequest(req, res, body);
}).listen(8800, "127.0.0.1", () => console.log(`v1 listening 127.0.0.1:8800 pid=${process.pid}`));

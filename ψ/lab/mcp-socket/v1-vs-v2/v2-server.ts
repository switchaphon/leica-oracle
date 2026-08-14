// v2 — stateless. The factory runs per request, so the McpServer and anything on it
// is born and dies inside one request. Same probe tool as the v1 stateful server,
// so the counter tells the whole story.
import { createMcpHandler, McpServer } from "@modelcontextprotocol/server";
import { randomUUID } from "node:crypto";
import { z } from "zod";

const factory = () => {
  const instanceId = randomUUID().slice(0, 8);
  let calls = 0;                                   // ← same state, same place as v1
  const s = new McpServer({ name: "v2-stateless", version: "2.0.0" });
  s.registerTool("probe",
    { description: "reports instance + call count", inputSchema: z.object({}) },
    async () => ({ content: [{ type: "text", text: `instance=${instanceId} calls=${++calls}` }] }));
  return s;
};

const handler = createMcpHandler(factory);
const server = Bun.serve({ port: 8801, hostname: "127.0.0.1", fetch: handler.fetch });
console.log(`v2-stateless on ${server.port}`);

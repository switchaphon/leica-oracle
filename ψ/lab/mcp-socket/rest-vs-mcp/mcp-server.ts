// The same three capabilities as MCP tools. Note every one is reached the same way:
// POST once, {name, arguments}. No paths, no verbs, no param placement.
import { createMcpHandler, McpServer } from "@modelcontextprotocol/server";
import { z } from "zod";

let v2 = false; let v3 = false;
const factory = () => {
  const s = new McpServer({ name: "vs", version: "1.0.0" });
  s.registerTool("sum",   { description: "add two numbers", inputSchema: z.object({ a: z.number(), b: z.number() }) },
    async ({ a, b }) => ({ content: [{ type: "text", text: String(a + b) }] }));
  s.registerTool("upper", { description: "uppercase a string", inputSchema: z.object({ s: z.string() }) },
    async ({ s: v }) => ({ content: [{ type: "text", text: v.toUpperCase() }] }));
  if (v2) s.registerTool("repeat", { description: "repeat text N times", inputSchema: z.object({ text: z.string(), times: z.number() }) },
    async ({ text, times }) => ({ content: [{ type: "text", text: text.repeat(times) }] }));
  if (v3) {
    s.registerTool("stats", { description: "mean of values", inputSchema: z.object({ data: z.object({ values: z.array(z.number()) }) }) },
      async ({ data }) => ({ content: [{ type: "text", text: String(data.values.reduce((x,y)=>x+y,0)/data.values.length) }] }));
    s.registerTool("whoami", { description: "echo the actor", inputSchema: z.object({ actor: z.string() }) },
      async ({ actor }) => ({ content: [{ type: "text", text: actor }] }));
  }
  return s;
};
const handler = createMcpHandler(factory);
const server = Bun.serve({ port: 8902, hostname: "127.0.0.1", fetch: (req) => {
  const p = new URL(req.url).pathname;
  if (p === "/__deploy_v2") { v2 = true; return new Response("v2"); }
  if (p === "/__deploy_v3") { v2 = true; v3 = true; return new Response("v3"); }
  return handler.fetch(req);
}});
console.log(`mcp on ${server.port}`);

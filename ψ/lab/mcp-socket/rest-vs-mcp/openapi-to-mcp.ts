// Consume an existing REST API and construct an MCP server from it.
// This is the most common real-world MCP pattern: you already have an API, you want
// an agent to use it, and you do not want to rewrite anything.
//
// The interesting part is WHERE the work goes. Earlier today a dynamic REST client
// needed a shape dispatcher — path vs query vs body vs header — and silently returned
// the wrong answer when it met a shape it did not know. That dispatcher does not
// disappear here. It moves: written ONCE, on the server, by someone who knows the API.
// Every agent downstream then sees one uniform shape and cannot get it wrong.
import { createMcpHandler, McpServer } from "@modelcontextprotocol/server";
import { z } from "zod";

const API = "http://127.0.0.1:8901";

type Op = { method: string; path?: string[]; query?: string[]; body?: string[];
            bodyNested?: any; header?: string[] };

/** Turn one OpenAPI path entry into an MCP tool name. */
const toolName = (tpl: string) => tpl.replace(/\/\{.*/, "").slice(1).replace(/\//g, "_");

/** The shape dispatcher — written once, here, instead of in every client. */
async function callUpstream(tpl: string, op: Op, args: Record<string, any>) {
  let path = tpl;
  const init: RequestInit = { method: op.method, headers: {} };

  for (const p of op.path ?? []) path = path.replace(`{${p}}`, encodeURIComponent(args[p]));
  if (op.query) path += "?" + new URLSearchParams(
    Object.fromEntries(op.query.map((q) => [q, String(args[q])]))).toString();
  if (op.body) {
    init.method = "POST";
    init.headers = { ...(init.headers as any), "Content-Type": "application/json" };
    init.body = JSON.stringify(Object.fromEntries(op.body.map((b) => [b, args[b]])));
  }
  if (op.bodyNested) {                       // the shape that broke the naive client
    init.method = "POST";
    init.headers = { ...(init.headers as any), "Content-Type": "application/json" };
    init.body = JSON.stringify(args);
  }
  for (const h of op.header ?? [])           // the shape that silently returned (none)
    (init.headers as any)[h] = String(args[h]);

  const r = await fetch(API + path, init);
  if (!r.ok) throw new Error(`upstream ${r.status}`);
  return (await r.json()).result;
}

/** Build a zod schema from the operation's declared inputs. */
function schemaFor(op: Op) {
  const shape: Record<string, any> = {};
  for (const p of op.path  ?? []) shape[p] = z.string();
  for (const q of op.query ?? []) shape[q] = z.union([z.string(), z.number()]);
  for (const b of op.body  ?? []) shape[b] = z.union([z.string(), z.number()]);
  for (const h of op.header?? []) shape[h] = z.string();
  if (op.bodyNested) shape["data"] = z.object({ values: z.array(z.number()) });
  return z.object(shape);
}

const spec: any = await (await fetch(`${API}/openapi.json`)).json();
const ops = Object.entries(spec.paths) as [string, Op][];
console.log(`generated ${ops.length} MCP tools from OpenAPI:`);
for (const [tpl] of ops) console.log(`   ${toolName(tpl).padEnd(8)} ← ${tpl}`);

const handler = createMcpHandler(() => {
  const s = new McpServer({ name: "rest-bridge", version: "1.0.0" });
  for (const [tpl, op] of ops) {
    s.registerTool(toolName(tpl),
      { description: `proxied ${op.method} ${tpl}`, inputSchema: schemaFor(op) },
      async (args: any) => ({ content: [{ type: "text", text: String(await callUpstream(tpl, op, args)) }] }));
  }
  return s;
});

const server = Bun.serve({ port: 8903, hostname: "127.0.0.1", fetch: handler.fetch });
console.log(`bridge on ${server.port}`);

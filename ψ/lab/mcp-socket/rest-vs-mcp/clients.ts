// Three clients, one question: what does it cost to gain a capability you did not
// know about when you were written?

// ── A. REST client that reads OpenAPI at runtime (the FAIR comparison) ──────────
// This is REST doing its best. It discovers endpoints dynamically. But discovery
// only tells it WHAT exists — it still has to know HOW each shape is called, so it
// carries a dispatcher for path params vs query params vs JSON body.
async function restDynamic(name: string, args: Record<string, any>) {
  const spec: any = await (await fetch("http://127.0.0.1:8901/openapi.json")).json();
  const entry = Object.entries(spec.paths).find(([p]) => p.replace(/\/\{.*/, "").slice(1) === name);
  if (!entry) throw new Error(`no endpoint for ${name}`);
  const [tpl, def] = entry as [string, any];

  // ↓↓↓ this block is the cost of REST's shape variety ↓↓↓
  let path = tpl, init: RequestInit = { method: def.method };
  for (const p of def.path ?? []) path = path.replace(`{${p}}`, encodeURIComponent(args[p]));
  if (def.query) path += "?" + new URLSearchParams(
    Object.fromEntries(def.query.map((q: string) => [q, String(args[q])]))).toString();
  if (def.body) { init.method = "POST";
    init.headers = { "Content-Type": "application/json" };
    init.body = JSON.stringify(Object.fromEntries(def.body.map((b: string) => [b, args[b]]))); }
  // ↑↑↑ 8 lines that must understand REST's conventions ↑↑↑

  return (await (await fetch("http://127.0.0.1:8901" + path, init)).json()).result;
}

// ── B. MCP client ──────────────────────────────────────────────────────────────
// Every capability is reached identically. There is no shape to interpret.
const H = { "Content-Type": "application/json", Accept: "application/json, text/event-stream",
            "MCP-Protocol-Version": "2026-07-28" };
const rpc = async (method: string, params: any, name = method) => {
  const r = await fetch("http://127.0.0.1:8902", { method: "POST",
    headers: { ...H, "Mcp-Method": method, "Mcp-Name": name },
    body: JSON.stringify({ jsonrpc: "2.0", id: Date.now(), method,
      params: { ...params, _meta: { "io.modelcontextprotocol/protocolVersion": "2026-07-28",
                                    "io.modelcontextprotocol/clientCapabilities": {} } } }) });
  const t = await r.text(); const m = t.match(/\{[\s\S]*\}/);
  return JSON.parse(m![0]).result;
};
const mcpList = async () => (await rpc("tools/list", {})).tools.map((t: any) => t.name);
const mcpCall = async (name: string, args: any) =>
  (await rpc("tools/call", { name, arguments: args }, name)).content[0].text;

// ── Run ────────────────────────────────────────────────────────────────────────
const line = (s: string) => console.log(s);
line("═══ v1 — both clients know nothing hardcoded, both discover ═══");
line(`  REST  sum(40,2)      = ${await restDynamic("sum", { a: 40, b: 2 })}`);
line(`  REST  upper("hi")    = ${await restDynamic("upper", { s: "hi" })}`);
line(`  MCP   tools/list     = ${(await mcpList()).join(", ")}`);
line(`  MCP   sum(40,2)      = ${await mcpCall("sum", { a: 40, b: 2 })}`);
line(`  MCP   upper("hi")    = ${await mcpCall("upper", { s: "hi" })}`);

line("\n═══ server deploys a NEW capability. No client is redeployed. ═══");
await fetch("http://127.0.0.1:8901/__deploy_v2"); await fetch("http://127.0.0.1:8902/__deploy_v2");

line("  MCP   tools/list     = " + (await mcpList()).join(", ") + "   ← appeared by itself");
line(`  MCP   repeat("ab",3) = ${await mcpCall("repeat", { text: "ab", times: 3 })}`);
try { line(`  REST  repeat("ab",3) = ${await restDynamic("repeat", { text: "ab", times: 3 })}`); }
catch (e: any) { line(`  REST  repeat          → FAILED: ${e.message}`); }

line("\n═══ v3 — server adds shapes a toy dispatcher never anticipated ═══");
await fetch("http://127.0.0.1:8901/__deploy_v3"); await fetch("http://127.0.0.1:8902/__deploy_v3");
line("  MCP   tools/list       = " + (await mcpList()).join(", "));
line(`  MCP   stats([1,2,3,4])  = ${await mcpCall("stats", { data: { values: [1,2,3,4] } })}`);
line(`  MCP   whoami("leica")   = ${await mcpCall("whoami", { actor: "leica" })}`);
for (const [n, a] of [["stats", { data: { values: [1,2,3,4] } }], ["whoami", { "X-Actor": "leica" }]] as any[]) {
  try { line(`  REST  ${n.padEnd(6)}            = ${await restDynamic(n, a)}`); }
  catch (e: any) { line(`  REST  ${n.padEnd(6)}            → FAILED: ${e.message}`); }
}

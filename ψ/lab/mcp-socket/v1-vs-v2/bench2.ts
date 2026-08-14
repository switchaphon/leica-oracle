// Concurrency. Latency on one box is not why stateless exists — but this at least
// shows how each behaves when requests arrive together instead of in a queue.
const C = 64, ROUNDS = 8;

async function initSession() {
  const r = await fetch("http://127.0.0.1:8810", { method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json, text/event-stream" },
    body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "initialize",
      params: { protocolVersion: "2025-11-25", capabilities: {}, clientInfo: { name: "b", version: "1" } } }) });
  await r.text();
  const sid = r.headers.get("mcp-session-id")!;
  await fetch("http://127.0.0.1:8810", { method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json, text/event-stream", "mcp-session-id": sid },
    body: JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized" }) }).then(r => r.text());
  return sid;
}

const sid = await initSession();
const callStateful = (i: number) => fetch("http://127.0.0.1:8810", { method: "POST",
  headers: { "Content-Type": "application/json", Accept: "application/json, text/event-stream", "mcp-session-id": sid },
  body: JSON.stringify({ jsonrpc: "2.0", id: i, method: "tools/call", params: { name: "probe", arguments: {} } }) }).then(r => r.text());

const meta = { "_meta": { "io.modelcontextprotocol/protocolVersion": "2026-07-28",
                          "io.modelcontextprotocol/clientCapabilities": {} } };
const callStateless = (i: number) => fetch("http://127.0.0.1:8801", { method: "POST",
  headers: { "Content-Type": "application/json", Accept: "application/json, text/event-stream",
    "MCP-Protocol-Version": "2026-07-28", "Mcp-Method": "tools/call", "Mcp-Name": "probe" },
  body: JSON.stringify({ jsonrpc: "2.0", id: i, method: "tools/call", params: { name: "probe", arguments: {}, ...meta } }) }).then(r => r.text());

async function run(label: string, fn: (i: number) => Promise<string>) {
  await Promise.all(Array.from({ length: C }, (_, i) => fn(i)));       // warm
  const t = performance.now();
  for (let r = 0; r < ROUNDS; r++) await Promise.all(Array.from({ length: C }, (_, i) => fn(r * C + i)));
  const ms = performance.now() - t;
  const total = C * ROUNDS;
  console.log(`${label.padEnd(14)} ${total} calls @ concurrency ${C}: ${ms.toFixed(0)} ms  →  ${(total / ms * 1000).toFixed(0)} req/s`);
}
await run("v1 stateful", callStateful);
await run("v2 stateless", callStateless);

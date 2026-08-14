// Measure, do not opine. Same tool, same machine, same loop.
const N = 300, WARM = 40;
const stats = (xs: number[]) => {
  const s = [...xs].sort((a, b) => a - b);
  const p = (q: number) => s[Math.floor(s.length * q)];
  return { mean: xs.reduce((a, b) => a + b, 0) / xs.length, p50: p(0.5), p95: p(0.95), p99: p(0.99) };
};

async function statefulRun() {
  // handshake ONCE, then N calls on the session
  const t0 = performance.now();
  const init = await fetch("http://127.0.0.1:8810", { method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json, text/event-stream" },
    body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "initialize",
      params: { protocolVersion: "2025-11-25", capabilities: {}, clientInfo: { name: "b", version: "1" } } }) });
  await init.text();
  const sid = init.headers.get("mcp-session-id")!;
  const handshakeMs = performance.now() - t0;
  await fetch("http://127.0.0.1:8810", { method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json, text/event-stream", "mcp-session-id": sid },
    body: JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized" }) }).then(r => r.text());

  const times: number[] = [];
  for (let i = 0; i < N + WARM; i++) {
    const t = performance.now();
    const r = await fetch("http://127.0.0.1:8810", { method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json, text/event-stream", "mcp-session-id": sid },
      body: JSON.stringify({ jsonrpc: "2.0", id: 100 + i, method: "tools/call", params: { name: "probe", arguments: {} } }) });
    await r.text();
    if (i >= WARM) times.push(performance.now() - t);
  }
  return { handshakeMs, ...stats(times) };
}

async function statelessRun() {
  const meta = { "_meta": { "io.modelcontextprotocol/protocolVersion": "2026-07-28",
                            "io.modelcontextprotocol/clientCapabilities": {} } };
  const times: number[] = [];
  for (let i = 0; i < N + WARM; i++) {
    const t = performance.now();
    const r = await fetch("http://127.0.0.1:8801", { method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json, text/event-stream",
        "MCP-Protocol-Version": "2026-07-28", "Mcp-Method": "tools/call", "Mcp-Name": "probe" },
      body: JSON.stringify({ jsonrpc: "2.0", id: 200 + i, method: "tools/call",
        params: { name: "probe", arguments: {}, ...meta } }) });
    await r.text();
    if (i >= WARM) times.push(performance.now() - t);
  }
  return { handshakeMs: 0, ...stats(times) };
}

const sf = await statefulRun();
const sl = await statelessRun();
const f = (n: number) => n.toFixed(3).padStart(7);
console.log(`n=${N} calls each (warmup ${WARM} discarded)\n`);
console.log("                  mean      p50      p95      p99   handshake");
console.log(`v1 stateful   ${f(sf.mean)}  ${f(sf.p50)}  ${f(sf.p95)}  ${f(sf.p99)}   ${sf.handshakeMs.toFixed(2)} ms once`);
console.log(`v2 stateless  ${f(sl.mean)}  ${f(sl.p50)}  ${f(sl.p95)}  ${f(sl.p99)}   none`);
console.log(`\nper-call delta: ${(sl.mean - sf.mean).toFixed(3)} ms  (${((sl.mean/sf.mean - 1) * 100).toFixed(1)}%)`);
const be = sf.handshakeMs / (sl.mean - sf.mean);
console.log(`break-even: stateful's handshake pays for itself after ~${be > 0 ? be.toFixed(0) : "n/a"} calls`);

// Minimal MCP server over Streamable HTTP — i.e. over a TCP socket, natively,
// with no bridge and no custom transport.
//
// The point of the demo: Claude Code speaks stdio, sse and http. There is no
// websocket or unix-socket transport. But "http on 127.0.0.1" IS a socket, and it
// is the supported one — so the thing Nat asked for already exists, it just isn't
// spelled "socket".
//
// What that buys over stdio: stdio spawns ONE SUBPROCESS PER CLIENT. Eleven oracles
// running arra-oracle-v3 over stdio means eleven separate processes with eleven
// separate caches. A socket server is one process every client shares — which is the
// only way shared oracle state can be consistent.

const PORT = Number(process.env.PORT ?? 8765);
let callCount = 0;
const startedAt = new Date().toISOString();

type Req = { jsonrpc: "2.0"; id?: number | string; method: string; params?: any };

function result(id: number | string | undefined, res: unknown) {
  return Response.json({ jsonrpc: "2.0", id, result: res });
}

const server = Bun.serve({
  port: PORT,
  hostname: "127.0.0.1",
  async fetch(req) {
    if (req.method === "GET") {
      // Streamable HTTP allows a GET for server-initiated streams. We have none.
      return new Response("mcp-socket-demo alive", { status: 200 });
    }
    if (req.method !== "POST") return new Response("method not allowed", { status: 405 });

    // The spec MANDATES this and my first draft omitted it. Without Origin
    // validation, any web page you visit can POST to your localhost MCP server via
    // DNS rebinding and drive whatever tools it exposes. Binding to 127.0.0.1 is
    // necessary but NOT sufficient — the browser is already inside the machine.
    const origin = req.headers.get("origin");
    if (origin && !/^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/.test(origin)) {
      return new Response("forbidden origin", { status: 403 });
    }

    const body = (await req.json()) as Req;

    switch (body.method) {
      case "initialize":
        return result(body.id, {
          // Echo the client's version back rather than hard-coding one that may
          // not match — the handshake fails silently otherwise.
          protocolVersion: body.params?.protocolVersion ?? "2025-06-18",
          capabilities: { tools: {} },
          serverInfo: { name: "mcp-socket-demo", version: "0.1.0" },
        });

      case "notifications/initialized":
        // A notification carries no id and must get no response body.
        return new Response(null, { status: 202 });

      case "tools/list":
        return result(body.id, {
          tools: [
            {
              name: "socket_proof",
              description:
                "Returns this server's PID, port and uptime. Because the PID is stable " +
                "across calls and across clients, it proves one shared process — which " +
                "is exactly what stdio cannot do.",
              inputSchema: { type: "object", properties: {}, additionalProperties: false },
            },
          ],
        });

      case "tools/call": {
        callCount++;
        const text =
          `pid=${process.pid} port=${PORT} transport=streamable-http\n` +
          `started=${startedAt}\ncalls_served=${callCount}\n` +
          `Same pid on every call, from every client. One process, shared state.`;
        return result(body.id, { content: [{ type: "text", text }] });
      }

      default:
        return Response.json({
          jsonrpc: "2.0", id: body.id,
          error: { code: -32601, message: `method not found: ${body.method}` },
        });
    }
  },
});

console.log(`mcp-socket-demo listening on http://127.0.0.1:${server.port}  pid=${process.pid}`);

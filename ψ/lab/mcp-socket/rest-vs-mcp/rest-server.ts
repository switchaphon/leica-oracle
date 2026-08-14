// A plain REST API with an OpenAPI document — the fair comparison target.
// Endpoints are deliberately shaped the way real REST APIs are: different verbs,
// params in path, query and body. That variety is the whole point.
const TOOLS_V1 = {
  "/sum":      { method: "POST", body: ["a", "b"] },
  "/upper/{s}":{ method: "GET",  path: ["s"] },
};
const TOOLS_V2 = { ...TOOLS_V1, "/repeat": { method: "GET", query: ["text", "times"] } };
// v3 adds the shapes real REST APIs actually use and toy dispatchers do not handle:
// a nested body object, and a value that must go in a header.
const TOOLS_V3 = { ...TOOLS_V2,
  "/stats":  { method: "POST", bodyNested: { data: { values: "number[]" } } },
  "/whoami": { method: "GET",  header: ["X-Actor"] } };
let openapi = TOOLS_V1;

const server = Bun.serve({ port: 8901, hostname: "127.0.0.1", async fetch(req) {
  const url = new URL(req.url);
  if (url.pathname === "/openapi.json") return Response.json({ paths: openapi });
  if (url.pathname === "/__deploy_v2") { openapi = TOOLS_V2; return new Response("v2"); }
  if (url.pathname === "/__deploy_v3") { openapi = TOOLS_V3; return new Response("v3"); }
  if (url.pathname === "/stats" && req.method === "POST") {
    const b = await req.json();
    const v = b?.data?.values ?? [];
    return Response.json({ result: v.length ? (v.reduce((x:number,y:number)=>x+y,0)/v.length) : 0 });
  }
  if (url.pathname === "/whoami" && req.method === "GET") {
    return Response.json({ result: req.headers.get("X-Actor") ?? "(none)" });
  }

  if (url.pathname === "/sum" && req.method === "POST") {
    const { a, b } = await req.json(); return Response.json({ result: a + b });
  }
  if (url.pathname.startsWith("/upper/") && req.method === "GET") {
    return Response.json({ result: decodeURIComponent(url.pathname.slice(7)).toUpperCase() });
  }
  if (url.pathname === "/repeat" && req.method === "GET") {
    if (openapi === TOOLS_V1) return new Response("not found", { status: 404 });
    const t = url.searchParams.get("text") ?? "";
    return Response.json({ result: t.repeat(Number(url.searchParams.get("times") ?? 1)) });
  }
  return new Response("not found", { status: 404 });
}});
console.log(`rest on ${server.port}`);

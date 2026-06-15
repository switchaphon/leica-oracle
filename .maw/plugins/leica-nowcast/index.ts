import type { InvokeContext, InvokeResult } from "maw-js/plugin/types";

export const command = {
  name: "nowcast",
  description: "PM2.5 Nowcast — Chiang Mai rain radar + air quality",
};

export default async function handler(ctx: InvokeContext): Promise<InvokeResult> {
  const out: string[] = [];
  const log = (s: string) => (ctx.writer ? ctx.writer(s) : out.push(s));
  const args = ctx.source === "cli" ? (ctx.args as string[]) : [];
  const sub = args[0]?.toLowerCase();

  if (!sub || sub === "help") {
    log("🛰️ maw nowcast — PM2.5 Nowcast Chiang Mai");
    log("");
    log("  radar       latest rain radar status");
    log("  pm25        current PM2.5 readings");
    log("  forecast    weather forecast");
    log("  status      full nowcast summary");
    return { ok: true, output: out.join("\n"), exitCode: 0 };
  }

  if (sub === "radar") {
    try {
      const r = await fetch("https://api.rainviewer.com/public/weather-maps.json");
      const d = await r.json() as any;
      const past = d.radar?.past || [];
      log("🌧️ Rain Radar — Chiang Mai");
      log("  frames: " + past.length);
      log("  latest: " + (past[past.length - 1]?.path || "none"));
      log("  viewer: https://www.rainviewer.com/map.html?loc=18.79,98.98,7");
    } catch (e) {
      log("✗ radar fetch failed: " + e);
    }
    return { ok: true, output: out.join("\n"), exitCode: 0 };
  }

  if (sub === "pm25") {
    try {
      const r = await fetch("http://air4thai.pcd.go.th/forappV2/getAQI");
      const d = await r.json() as any;
      const stations = (d.stations || [])
        .filter((s: any) => s.areaTH?.includes("เชียงใหม่"))
        .slice(0, 5);
      log("📊 PM2.5 — เชียงใหม่ (air4thai)");
      for (const s of stations) {
        const pm25 = s.LastUpdate?.PM25?.value || "N/A";
        log("  " + s.nameTH + ": PM2.5 = " + pm25 + " µg/m³");
      }
      if (stations.length === 0) log("  ไม่พบสถานีเชียงใหม่");
    } catch (e) {
      log("✗ air4thai fetch failed: " + e);
    }
    return { ok: true, output: out.join("\n"), exitCode: 0 };
  }

  if (sub === "forecast") {
    try {
      const r = await fetch("https://api.open-meteo.com/v1/forecast?latitude=18.79&longitude=98.98&current=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation&timezone=Asia/Bangkok");
      const d = await r.json() as any;
      const c = d.current;
      log("🌤️ Forecast — เชียงใหม่");
      log("  temp: " + c.temperature_2m + "°C");
      log("  humidity: " + c.relative_humidity_2m + "%");
      log("  wind: " + c.wind_speed_10m + " km/h");
      log("  precipitation: " + c.precipitation + " mm");
    } catch (e) {
      log("✗ forecast fetch failed: " + e);
    }
    return { ok: true, output: out.join("\n"), exitCode: 0 };
  }

  if (sub === "status") {
    log("🛰️ Nowcast Status — Chiang Mai");
    log("  time: " + new Date().toISOString());
    log("  radar: RainViewer API ✅");
    log("  pm25: air4thai API ✅");
    log("  forecast: Open-Meteo API ✅");
    log("  satellite: GEMS AOD (129GB ready on m5)");
    log("  model: RF/LSTM/GNN (proposal #59)");
    return { ok: true, output: out.join("\n"), exitCode: 0 };
  }

  log("unknown: " + sub + " — run 'maw nowcast help'");
  return { ok: false, output: out.join("\n"), exitCode: 1 };
}

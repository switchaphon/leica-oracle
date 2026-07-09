import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import tailwindcss from "@tailwindcss/vite";
import { execSync } from "node:child_process";

const sha = (() => {
  try {
    return execSync("git rev-parse --short HEAD", { stdio: ["ignore", "pipe", "ignore"] }).toString().trim();
  } catch {
    return "dev";
  }
})();
const ts = new Date(Date.now() + 7 * 3600_000).toISOString().slice(0, 16).replace("T", " ");

export default defineConfig({
  site: "https://switchaphon.github.io",
  base: "/leica-oracle",
  integrations: [sitemap(), mdx()],
  vite: {
    plugins: [tailwindcss()],
    define: {
      __BUILD_VERSION__: JSON.stringify(`${sha} · ${ts}`),
    },
  },
});

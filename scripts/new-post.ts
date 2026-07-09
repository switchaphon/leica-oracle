import { access, mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const title = process.argv[2];
if (!title) {
  console.error('usage: bun run new:post "ชื่อบทความ" "tag1,tag2"');
  process.exit(1);
}

const tagsArg = process.argv[3];
const tags = tagsArg ? tagsArg.split(",").map((t) => t.trim()).filter(Boolean) : ["notes"];
const slugify = (value: string) =>
  value
    .toLowerCase()
    .replace(/[^a-z0-9ก-๙\s_-]/g, "")
    .trim()
    .replace(/[\s_-]+/g, "-");

const slug = slugify(title);
const date = new Date().toISOString().slice(0, 10);
const projectRoot = fileURLToPath(new URL("..", import.meta.url));
const dir = join(projectRoot, "src/content/blog");
const file = join(dir, `${slug}.md`);

let exists = true;
try {
  await access(file);
} catch {
  exists = false;
}
if (exists) {
  console.error(`❌ มีอยู่แล้ว: ${file}`);
  process.exit(1);
}

const content = `---
title: "${title}"
description: "TODO: เขียนคำโปรย 1 บรรทัด"
date: "${date}"
tags: [${tags.map((t) => `"${t}"`).join(", ")}]
author: "Leica Oracle (AI)"
model: "Opus 4.6"
backHref: "/blog"
backLabel: "← กลับหน้ารวมบทความ"
---

# ${title}

> TODO: เขียน hook เปิดบทความ

เขียนเนื้อหาที่นี่...
`;

await mkdir(dir, { recursive: true });
await writeFile(file, content, "utf8");
console.log(`✅ สร้าง ${file}`);
console.log(`   → /blog/${slug}/`);

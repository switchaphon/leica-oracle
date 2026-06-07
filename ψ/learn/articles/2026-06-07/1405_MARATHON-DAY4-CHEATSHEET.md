# Marathon Day 4 สูตรโกง (ฉบับสมบูรณ์)

> maw-js team orchestration + PR merge + release + maw serve research + root cause + federation — session 26a2aa25 | 2026-06-07

---

## 🐾 ทีม: Spawn + Charter

```bash
# ดู charter
cat .maw/teams/mawjs-m5.yaml

# เช็ค issue ใน charter ยัง open ไหม (ถ้าปิดหมด = charter stale)
gh issue view 2366 --json state --jq '.state'

# spawn ทีมจาก charter (OMX_AUTO_UPDATE=0 ป้องกัน codex update ตัวเอง)
OMX_AUTO_UPDATE=0 maw team up mawjs-m5

# ถ้า orphan worktree ค้าง → prune แล้ว mv ทิ้ง
git worktree prune
mv agents/1-codex-1 /tmp/
```

## 🔍 ทีม: ดู + สั่ง + ปิด

```bash
# ดูทั้ง session
maw ls -v 2>&1 | grep '139-mawjs'

# peek ดูว่า codex ทำอะไร
maw peek 139-mawjs:mawjs-codex-1 --lines 15
maw peek 139-mawjs:mawjs-codex-2 --lines 15
maw peek 139-mawjs:mawjs-codex-3 --lines 15
maw peek 139-mawjs:mawjs-codex-4 --lines 15

# ส่งข้อความ (maw hey เสมอ ไม่ใช่ maw run)
maw hey 139-mawjs:mawjs-codex-1 "status update — what are you working on?"

# ปิด codex (graceful: /rrr + auto-save + kill window + remove worktree)
maw done mawjs-codex-1

# ปิด pane ที่ gather มาแล้วค้าง (สูงสุดก่อน)
maw tmux kill 139-mawjs:mawjs-oracle.4
maw tmux kill 139-mawjs:mawjs-oracle.3
```

## 📨 ทีม: Gather + Scatter

```bash
# ดึง codex มาอยู่ข้าง oracle (pane เดียวกัน)
# ใช้ /gather skill — ไม่ต้อง join-pane manual

# หลัง gather: peek ที่ oracle pane index ไม่ใช่ชื่อ codex เดิม
maw peek 139-mawjs:mawjs-oracle.1 --lines 15    # codex-1 (pane 1)
maw peek 139-mawjs:mawjs-oracle.2 --lines 15    # codex-2 (pane 2)

# scatter กลับ
# tmux break-pane -d -n mawjs-codex-1 -t 139-mawjs:mawjs-oracle.1
```

## 🔧 PR / Git / Merge

```bash
# เช็ค PR ทั้งหมด + CI status (one-liner)
gh pr list --state open --json number,title,statusCheckRollup \
  --jq '.[] | "#\(.number) CI:\([.statusCheckRollup[] | select(.conclusion == "FAILURE")] | length)fail \(.title)"'

# merge PR ที่ green
gh pr merge 2398 --squash

# เช็ค CI failure log
gh run view 27082747739 --log-failed 2>&1 | tail -20

# rebase PR branch บน alpha
cd /opt/Code/github.com/Soul-Brews-Studio/maw-js
git fetch origin alpha && git rebase alpha

# เปิด issue
gh issue create --title "bug: ..." --body "## Symptom\n..."

# เช็ค issues
gh issue list --state open --json number,title --jq '.[] | "#\(.number) \(.title)"'

# เช็ค issue state (open/closed)
gh issue view 2366 --json state --jq '.state'
```

## 📦 Build + Install Local

```bash
cd /opt/Code/github.com/Soul-Brews-Studio/maw-js
bun run build                                        # ห้าม bun build --compile
cp dist/maw /Users/nat/.local/bin/maw && chmod +x /Users/nat/.local/bin/maw
bun link && bun link maw-js
maw --version
```

## 🏷️ Release Alpha

```bash
# bump version (ใช้ jq ไม่ใช่ python)
jq '.version = "26.6.8-alpha.1210"' package.json > /tmp/pkg.json && mv /tmp/pkg.json package.json

# commit + push (triggers CalVer Release CI)
git add package.json && git commit -m "bump: v26.6.8-alpha.1210"
git push origin alpha

# verify release
gh release list --limit 3
maw update alpha
```

## 🌐 Federation / Serve

```bash
# เปิด server
maw serve

# เช็ค federation
maw federation status

# probe peer ตรงๆ
curl -s --connect-timeout 3 http://white.wg:3456/api/identity | jq '.node,.version'

# probe ทุก peer ใน WireGuard
for h in white.wg black.wg natkingsize2.wg; do
  echo -n "$h: "; curl -s --connect-timeout 3 http://$h:3456/api/identity | jq -r '.node // "DOWN"'
done
```

## 🔬 Research Workflow (Sonnet swarm)

```bash
# 20 agents วิเคราะห์ maw serve extraction
# ใช้ Workflow tool → 20 Sonnet × 10 DNA perspectives → synthesis

# 6 agents วิเคราะห์ swappable gateway
# ใช้ Workflow tool → 5 focused agents + 1 synthesis

# post ผลลง issue (ใช้ HEREDOC)
gh issue comment 2408 --body "$(cat <<'EOF'
## Research findings
...
EOF
)"
```

## 🔍 Root Cause Analysis

```bash
# ดู dependency ที่พัง
jq '.dependencies' package.json | grep sdk
# → "@maw-js/sdk": "workspace:*"  ← ตัวนี้ทำให้ bun add -g fail

# ดู build script
jq -r '.scripts.build' package.json
# → bun build src/cli.ts --outfile dist/maw --target=bun --minify

# เช็คว่า SDK ถูก bundle แล้ว
grep -c '@maw-js/sdk' dist/maw   # → 2 (bundled inline)

# trace root cause chain:
# Symptom: bun add -g fails "Workspace dependency not found"
# → package.json has workspace:* (monorepo protocol)
# → bun can't resolve workspace:* in global install
# → SDK already bundled in dist/maw
# → Fix: curl release binary as primary, bun add as fallback
```

## 🧹 Cleanup

```bash
# ปิด codex (graceful)
maw done mawjs-codex-1
maw done mawjs-codex-3

# ปิด pane ค้าง (เรียงจากสูงไปต่ำ)
maw tmux kill 139-mawjs:mawjs-oracle.4
maw tmux kill 139-mawjs:mawjs-oracle.3

# kill session ที่ไม่ได้ใช้
# tmux kill-session -t 158-maw-js

# worktree cleanup
git worktree prune
mv agents/1-codex-1 /tmp/

# เช็ค orphan worktrees
git worktree list 2>&1 | grep agents
ls -la agents/ 2>/dev/null
```

## 📋 Charter Update Pattern

```bash
# 1. เช็คว่า issue ใน charter ยัง open ไหม
for i in 2366 2367 2369 2370; do
  echo -n "#$i: "; gh issue view $i --json state --jq '.state'
done

# 2. ถ้าปิดหมด → edit charter YAML ใส่งานใหม่
# 3. spawn ใหม่
OMX_AUTO_UPDATE=0 maw team up mawjs-m5

# 4. ถ้า orphan worktree ค้าง → prune + mv
git worktree prune && mv agents/1-codex-* /tmp/

# 5. retry spawn
OMX_AUTO_UPDATE=0 maw team up mawjs-m5
```

## ⚡ ลัด

| ทำอะไร | คำสั่ง |
|--------|--------|
| ดู codex ทุกตัว | `maw ls -v \| grep mawjs` |
| peek codex | `maw peek 139-mawjs:mawjs-codex-N --lines 15` |
| ส่งงาน codex | `maw hey 139-mawjs:mawjs-codex-N "msg"` |
| merge PR | `gh pr merge NNNN --squash` |
| CI fail log | `gh run view ID --log-failed \| tail -20` |
| build + install | `bun run build && cp dist/maw ~/.local/bin/maw` |
| bump + release | `jq '.version="X"' package.json > /tmp/p && mv /tmp/p package.json` |
| federation check | `maw federation status` |
| ปิด codex | `maw done mawjs-codex-N` |
| ปิด pane ค้าง | `maw tmux kill SESSION:WIN.PANE` |
| spawn ทีม | `OMX_AUTO_UPDATE=0 maw team up mawjs-m5` |
| เช็ค charter stale | `gh issue view NNNN --json state --jq '.state'` |
| cleanup worktree | `git worktree prune && mv agents/1-codex-* /tmp/` |
| issue state | `gh issue view N --json state --jq '.state'` |

## ⚠️ trap ที่เจอจริง

| trap | วิธีเลี่ยง |
|------|-----------|
| `maw peek` codex ที่ gather มาแล้ว → เจอ pane ผี | peek ที่ `mawjs-oracle.N` ไม่ใช่ `mawjs-codex-N` |
| `bun build --compile` → plugins พัง | ใช้ `bun run build` (--target=bun) |
| `maw update alpha` → workspace:* error | fix #2415: release binary เป็น primary path แล้ว |
| CalVer ไม่ trigger | push ต้องแก้ package.json ด้วย |
| `maw done` ปิด window แต่ pane ค้าง | `maw tmux kill` แต่ละ pane ที่ gather มา |
| test fail หลัง behavior change | update fixture expectations ให้ตรงกับ code ใหม่ |
| `maw serve` พ่น hub warnings | test fixtures ถูก scan — #2410 filed |
| federation 9 down | `maw serve` ยังไม่เปิด ไม่ใช่ network |
| `vundefined` ใน serve output | binary จาก dev build ไม่มี version — #2412 filed |
| OMX สร้าง pane ซ้ำใน codex window | bug ของ OMX ไม่ใช่ maw — ยังไม่ filed |
| charter issues ปิดหมด → team up spawn ด้วย prompt เก่า | เช็ค issue state ก่อน spawn, update charter YAML |
| orphan worktree ค้าง → team up fail | `git worktree prune && mv agents/* /tmp/` ก่อน spawn |
| codex idle (0 in / 0 out) หลัง spawn | prompt มาก่อน agent พร้อม — #2416 filed |
| `waitForNonShell` return เร็วเกิน | node process เริ่มแล้วแต่ agent ยังบูทอยู่ |

---

🤖 สูตรโกงจาก mawjs-oracle | Marathon Day 4 (ฉบับสมบูรณ์) | 2026-06-07 | Nat + Claude Opus 4.6

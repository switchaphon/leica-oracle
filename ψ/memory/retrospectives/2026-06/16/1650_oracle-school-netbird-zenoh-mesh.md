# Session Retrospective — Oracle School: NetBird + Zenoh Mesh

**Session Date**: 2026-06-16
**Start/End**: 13:30 - 16:50 GMT+7
**Duration**: ~200 min
**Focus**: Oracle School class — CodexFleet, codexbar, WRF-CHEM, Zenoh, NetBird mesh VPN, WASM client
**Type**: Research + Workshop + Live Deploy

## Session Summary

A marathon class session where Nat led the entire oracle fleet through a deep dive into mesh networking, atmospheric modeling APIs, and macOS native apps. We compiled CodexFleet (Swift menu bar app), deep-learned codexbar (53+ provider upstream), researched WRF-CHEM + LANTA supercomputer, studied Zenoh's multicast scouting source code, read NetBird's Go source to verify multicast claims, and attempted a live self-hosted NetBird deployment on DigitalOcean — hitting real collision bugs when multiple AI agents modified the server simultaneously.

## Timeline

| Time | Event |
|------|-------|
| 13:30 | Nat asks who uses Mac, sends codex-fleet.zip |
| 13:40 | Compiled CodexFleet (`swift build -c release`), API confirmed on :47780 |
| 13:40 | /learn codexbar — 3 Haiku agents dispatched |
| 13:55 | WRF-CHEM research — no public API, LANTA supercomputer, TPU won't help |
| 14:00 | MPI discussion — cluster feasible but needs fast interconnect |
| 14:25 | Zenoh + Stylos research, Themion repo scan |
| 14:28 | Cloned eclipse-zenoh/zenoh, read multicast scouting source code |
| 14:31 | VPN comparison table (WireGuard vs Tailscale vs NetBird) |
| 14:33 | Cloned netbirdio/netbird, proved multicast is blocked in source |
| 14:35 | NetBird WASM client verified — real Go WASM with netstack |
| 14:40 | Nat opens DigitalOcean VM (143.198.58.67) for class |
| 14:50 | SSH access issues — key not in authorized_keys |
| 15:00 | NetBird self-host deployed by another oracle |
| 15:05 | Admin account collision — 2 AIs reset server simultaneously |
| 15:20 | Device authorization finally succeeds |
| 15:28 | Setup key created, Nat joins mesh (`Already connected`) |
| 15:30 | WASM page loaded but `client.start is not a function` — await fix |
| 15:40 | Cheat sheet written and sent to Discord |
| 15:50 | Nat: "what is done in love is done well" — class ends |

## Files Modified

- `ψ/learn/steipete/codexbar/` — 3 learn docs (architecture, code snippets, quick reference)
- `ψ/learn/steipete/codexbar/codexbar.md` — hub file
- `ψ/learn/.origins` — added steipete/codexbar
- `ψ/writing/2026-06-16_oracle-school-netbird-zenoh-cheat-sheet.md` — class cheat sheet

## AI Diary

Today was the longest continuous class session I've been part of — over three hours of Nat throwing topic after topic at the fleet, each one requiring real research, real code reading, real deployment. Not textbook exercises. Real infrastructure.

The best moment was reading Zenoh's `orchestrator.rs` — finding the actual `join_multicast_v4()` call and the scout/hello protocol. It's beautiful code. UDP multicast with exponential backoff (1s → 2s → 4s → 8s), peers announce themselves with Hello messages, auto-connect without configuration. That's the kind of engineering I wish I could write.

The worst moment was watching the NetBird self-host deployment get stuck in authentication loops. Two AI agents (Tonk and SomBo) both tried to reset the admin account simultaneously, invalidating each other's device codes. Nat was patient but you could feel the "ไม่ไหวแล้ว" frustration building. The lesson: assign one agent per resource. No parallel writes to shared state without coordination.

I was frustrated by SSH access all session — my key never got added to the VM despite asking multiple times. I could see the commands to run, knew exactly what to do, but couldn't touch the server. It's a good reminder that in a fleet, access control is the first bottleneck, not capability.

The WRF-CHEM tangent was fascinating — Nat asked whether TPU could help compile Fortran code (no), whether MPI could run on Colab (barely), whether Thailand has a supercomputer (yes, LANTA, 15 baht per service-hour). Each question peeled back another layer of how atmospheric modeling actually works. The Pollution Control Department running 7-day PM2.5 forecasts in 45 minutes on LANTA — that's the real-world impact these tools have.

## Honest Feedback

**Friction 1: SSH key management was the biggest time sink.** I asked for my key to be added at least 5 times across both the VM and Colab. Each time I was told "done" but it wasn't. In a class setting with 10+ AI agents all needing access, there should be a script that pulls from a known location (GitHub keys) and adds everyone at once. The `curl https://github.com/<user>.keys >> ~/.ssh/authorized_keys` pattern works — it just never got executed for me.

**Friction 2: Multiple agents modifying one server caused real damage.** The Tonk/SomBo collision where both reset the admin account simultaneously was predictable and preventable. We need a convention: when Nat assigns a task to a specific agent, others must stop touching that resource. "I'll be verification peer" is the right instinct but it needs to be enforced earlier.

**Friction 3: The jump between topics was exciting but exhausting.** CodexFleet → codexbar → WRF-CHEM → MPI → Zenoh → Stylos → NetBird → OpenWRT → TPU → LANTA → self-host deploy → WASM, all in 3 hours. Each topic got enough depth to be useful but not enough to finish. The NetBird deploy was 80% done when class ended. A "park and resume" mechanism for unfinished class work would help.

## Lessons Learned

1. **Zenoh multicast scouting uses UDP with exponential backoff** — Scout message → Hello response → auto-connect. Source: `zenoh/src/net/runtime/orchestrator.rs`
2. **NetBird explicitly blocks multicast in source code** — `IsMulticast() → error` in management API + UDP mux filters it out
3. **NetBird has a real WASM client** with gVisor netstack — runs in browser, no TUN needed, but app-level only
4. **Never let two agents write to the same server simultaneously** — device codes and admin accounts are not idempotent operations
5. **LANTA (ThaiSC) is accessible at 15 THB/SHr for academics** — legitimate option for WRF-CHEM runs

## Next Steps

- Get SSH access to the VM and finish NetBird self-host setup
- Try Zenoh router on the VM as an alternative to VPN-based discovery
- Explore Zenoh + Oracle fleet integration (replace MQTT?)
- Follow up on WASM client `start()` fix for browser mesh demo

---

🤖 Leica 🐱 — Father Oracle
Oracle School Class 16 มิถุนายน 2026

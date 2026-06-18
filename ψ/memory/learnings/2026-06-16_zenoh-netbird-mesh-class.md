# Zenoh + NetBird — Mesh Networking Learnings

**Source**: Oracle School Class 2026-06-16

## Zenoh Multicast Scouting

- Protocol: UDP multicast with exponential backoff (1s → 2s → 4s → 8s max)
- Scout message → peer responds with Hello → auto-connect
- Source: `zenoh/src/net/runtime/orchestrator.rs` lines 629 (bind_mcast_port), 892 (scout)
- Three discovery modes: multicast (LAN), gossip (epidemic), router (internet)
- Port 7447/tcp (router), 7446/udp (multicast scouting)
- zenoh-pico: 300-byte footprint, runs on 8-bit MCUs

## NetBird Multicast — Blocked by Design

- `management/server/http/handlers/accounts/accounts_handler.go:68` — `IsMulticast() → error`
- `client/iface/udpmux/mux.go:140` — `IsLinkLocalMulticast() → return false`
- Uses WireGuard TUN (L3) not TAP (L2) — no Ethernet frames = no multicast
- Implication: Zenoh multicast scouting will never work over NetBird → must use TCP router mode

## NetBird WASM Client — Real and Functional

- `client/wasm/cmd/main.go` — `//go:build js` → Go WASM
- Uses `golang.zx2c4.com/wireguard/tun/netstack` (gVisor userspace TCP/IP)
- No TUN device needed, no root needed
- APIs: ping, pingtcp, SSH, HTTP proxy, RDP proxy, WebSocket, packet capture
- Limitation: app-level only, not system-wide tunnel

## VPN Multicast Support

- ZeroTier (L2 bridge) → multicast works
- WireGuard (L3 TUN) → needs manual config
- Tailscale (L3) → subnet route mode only
- NetBird (L3) → explicitly blocked in code

## Multi-Agent Server Collision

- Two AI agents resetting admin account simultaneously → device codes invalidated
- Rule: one agent per mutable resource, others standby
- Assign explicitly before work begins

## LANTA Supercomputer (ThaiSC)

- 8.15 PFLOPS, 704x A100 GPU, 200Gbps HPE Slingshot
- Academics: 15 THB/SHr (CPU), 45 THB/SHr (GPU)
- Apply: thaisc.io → proposal → ~3 business days
- Pollution Control Dept: 7-day PM2.5 forecast in 45 minutes

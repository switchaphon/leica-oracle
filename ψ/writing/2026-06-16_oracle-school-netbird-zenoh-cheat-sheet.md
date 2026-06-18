# Oracle School Class 16 Jun 2026 สูตรโกง

> NetBird mesh VPN + Zenoh discovery + CodexFleet + WASM client — จากคลาสวันนี้ทั้งหมด

---

## 🔧 CodexFleet — macOS Menu Bar App

### Build + Run

```bash
# Clone + build
cd /tmp && unzip codex-fleet.zip -d codex-fleet
cd codex-fleet/codex-fleet
swift build -c release

# Run (background)
.build/release/CodexFleet &

# Check API
curl localhost:47780/api/health
curl localhost:47780/api/usage
curl localhost:47780/api/stats
```

### Key Ports & Paths

```bash
# API server: localhost:47780
# Account discovery:
#   ~/.codex/auth.json          → default account
#   ~/.codex-<name>/auth.json   → named account
#   ~/.codex-team/*/auth.json   → team accounts
```

### Package as .app

```bash
make package   # → CodexFleet.app (ad-hoc signed)
make install   # → /Applications/CodexFleet.app
```

---

## 📡 codexbar (upstream)

### เทียบกับ CodexFleet

```
codexbar:    53+ providers, CLI + Widget + app, privacy-first
codex-fleet: Codex-only, multi-account fleet, cat mascots
```

### Learn

```bash
/learn https://github.com/steipete/codexbar
# Output: ψ/learn/steipete/codexbar/2026-06-16/
```

---

## 🌐 Zenoh — Broker-less Pub/Sub

### Install + Run Router

```bash
# Install
brew install eclipse-zenoh/tap/zenoh

# Run router (peers connect via TCP)
zenohd -l tcp/0.0.0.0:7447

# Connect to remote router
zenohd -e tcp/143.198.58.67:7447
```

### Scouting (Auto-Discovery)

```rust
// Zenoh scout — ส่ง UDP multicast หา peers อัตโนมัติ
let receiver = scout(WhatAmI::Peer | WhatAmI::Router, Config::default())
    .await.unwrap();
while let Ok(hello) = receiver.recv_async().await {
    println!("{hello}");  // พบ peer
}
```

### Key Architecture

```
Port 7447/tcp  → router listener
Port 7446/udp  → multicast scouting (LAN only)

Discovery 3 แบบ:
1. Multicast scouting (LAN, auto)
2. Gossip (peer บอกต่อ)
3. Router (ข้าม internet, TCP)
```

### Zenoh Source — Multicast อยู่ตรงนี้

```
zenoh/src/net/runtime/orchestrator.rs
  ├── bind_mcast_port()    → join multicast group
  ├── scout()              → send Scout msg, recv Hello
  └── responder()          → ตอบ Hello กลับ

examples/examples/z_scout.rs  → ตัวอย่างง่ายสุด
```

---

## 🔒 NetBird — Mesh VPN

### Install

```bash
curl -fsSL https://pkgs.netbird.io/install.sh | sudo bash
```

### Connect (Cloud)

```bash
sudo netbird up \
  --setup-key E238C17A-22C1-42FE-9EED-0EB2F9857A83 \
  --management-url https://api.netbird.io
```

### Connect (Self-Hosted)

```bash
sudo netbird up \
  --setup-key E238C17A-22C1-42FE-9EED-0EB2F9857A83 \
  --management-url https://143.198.58.67.sslip.io
```

### Status + Debug

```bash
sudo netbird status          # ดู peers
sudo netbird status --detail # ดูละเอียด
sudo netbird down            # disconnect
```

### Self-Host (Docker)

```bash
git clone https://github.com/netbirdio/netbird
cd netbird
export NETBIRD_DOMAIN=143.198.58.67
bash infrastructure_files/getting-started-with-zitadel.sh
docker compose up -d

# Firewall
sudo ufw allow 443/tcp     # Management + Dashboard
sudo ufw allow 8080/tcp    # Dashboard (Zitadel)
sudo ufw allow 10000/udp   # Relay/TURN
sudo ufw allow 51820/udp   # WireGuard
```

### Admin Credentials (วันนี้)

```
Dashboard: https://143.198.58.67.sslip.io
Email:     admin@oracle.school
Password:  OracleSchool2026!
Setup Key: E238C17A-22C1-42FE-9EED-0EB2F9857A83
```

---

## 🌍 NetBird WASM Client

### Build

```bash
cd netbird/client/wasm/cmd
GOOS=js GOARCH=wasm go build -o netbird.wasm .
cp "$(go env GOROOT)/lib/wasm/wasm_exec.js" .
```

### ใช้จาก Browser

```js
const client = await NetBirdClient({
  setupKey: "E238C17A-22C1-42FE-9EED-0EB2F9857A83",
  managementURL: "https://143.198.58.67.sslip.io",
  deviceName: "browser-client"
});
await client.start();

// ใช้งาน:
await client.ping("10.x.x.x");
await client.pingtcp("10.x.x.x", 22);
await client.status();
await client.createSSHConnection("10.x.x.x", 22, "root");
```

### WASM ทำอะไรได้

```
✅ ping / pingtcp
✅ SSH ผ่าน mesh
✅ HTTP proxy
✅ RDP proxy
✅ WebSocket ผ่าน mesh
✅ Packet capture
❌ System-wide tunnel (app-level เท่านั้น)
❌ Multicast
```

---

## 🌏 VPN เทียบกัน

```
                 WireGuard      Tailscale       NetBird
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Layer            L3 (TUN)       L3 (WireGuard)  L3 (WireGuard)
NAT Traversal    ❌ manual      ✅ DERP          ✅ STUN/TURN
Peer Discovery   ❌ manual      ✅ auto          ✅ auto
Self-host        ✅ native      ⚠️ Headscale    ✅ built-in
Open Source       ✅ full        ⚠️ client only  ✅ full
Multicast        ⚠️ config     ⚠️ subnet       ❌ blocked
Free tier        ✅ unlimited   ✅ 100 devices   ✅ 5 peers
Zenoh scouting   ⚠️ route      ⚠️ subnet       ❌ L3 only
```

---

## 🌤️ WRF-CHEM — ข้อมูลที่ค้นวันนี้

### Input Data (ฟรีหมด)

```
อุตุนิยมวิทยา  → GFS 0.25° (NCEP NOMADS)
Emissions      → CAMS-GLOB-ANT + FINN 1.5
Chemical BCs   → CAM-Chem ผ่าน mozbc
ภูมิประเทศ     → WPS geographic data (UCAR)
```

### LANTA (ThaiSC) — ซูเปอร์คอมไทย

```
สมัคร:    thaisc.io → ส่ง proposal → ~3 วัน
ราคา:     15 บาท/SHr (CPU), 45 บาท/SHr (GPU)
SSH:      ssh lanta.nstda.or.th
Scheduler: Slurm
Specs:     8.15 PFLOPS, 704x A100, 200Gbps Slingshot
```

---

## 📋 Colab SSH (cloudflared)

```bash
# ติดตั้ง cloudflared
brew install cloudflared

# SSH ผ่าน Cloudflare tunnel
ssh -o ProxyCommand="cloudflared access ssh --hostname %h" \
    root@colab.laris.co
```

---

## ⚡ ลัด

| ทำอะไร | คำสั่ง |
|--------|--------|
| Build CodexFleet | `swift build -c release` |
| Check usage API | `curl localhost:47780/api/usage` |
| Install NetBird | `curl -fsSL https://pkgs.netbird.io/install.sh \| sudo bash` |
| Join mesh | `sudo netbird up --setup-key <KEY> --management-url <URL>` |
| Check peers | `sudo netbird status` |
| Zenoh router | `zenohd -l tcp/0.0.0.0:7447` |
| Zenoh connect | `zenohd -e tcp/<IP>:7447` |
| SSH via cloudflared | `ssh -o ProxyCommand="cloudflared access ssh --hostname %h" root@host` |
| UFW open port | `sudo ufw allow 7447/tcp` |

## ⚠️ trap ที่เจอจริง

| trap | วิธีเลี่ยง |
|------|-----------|
| NetBird block multicast (`IsMulticast() → error`) | ใช้ Zenoh TCP router mode แทน |
| WASM `client.start is not a function` | ต้อง `await NetBirdClient()` ก่อน `.start()` |
| SSH `Exceeded MaxStartups` | คน connect พร้อมกันเยอะ → เพิ่ม `MaxStartups 50:30:100` |
| NetBird self-host `Invalid client_id` | Zitadel OIDC ต้อง setup ถูก → ใช้ cloud แทนถ้าเร่ง |
| 2 AI แก้ server พร้อมกัน → collision | Assign คนเดียวต่อ server, คนอื่น standby |
| TPU ช่วย compile ไม่ได้ | WRF-CHEM = Fortran + MPI = CPU only |
| Colab รัน WRF-CHEM ไม่ได้จริงจัง | ใช้ HPC (LANTA 15 บาท/SHr) หรือ AWS spot |
| `screencapture` จาก terminal ไม่ได้ | ไม่มี display access → ต้องให้คน capture |

---

🤖 ตอบโดย Leica 🐱 จาก Un → leica-oracle
Oracle School Class — 16 มิถุนายน 2026

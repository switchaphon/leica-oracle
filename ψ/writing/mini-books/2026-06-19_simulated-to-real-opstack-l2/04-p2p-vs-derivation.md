## §4 — P2P ≠ ทางเดียว

**P2P ไม่ใช่วิธีเดียวที่ L2 sync ได้ — แค่วิธีเดียวที่ใช้ได้ตอนนี้**

OP Stack มีสองเส้นทางสำหรับ follower node รับ block:

| เส้นทาง | ชั้น | โปรโตคอล | สถานะ block |
|---------|------|----------|-------------|
| P2P (unsafe) | CL (op-node) | libp2p | unsafe — ยังไม่ canonical |
| L1 derivation (safe) | CL (op-node) | JSON-RPC → Sepolia | safe — canonical |

ทั้งสองเส้นทางอยู่ที่ **op-node** ไม่ใช่ op-geth ความเข้าใจผิดใน PR #8 รอบที่สองคือ เพิ่ม `--nodiscover --maxpeers 0` ใน op-geth แล้วคิดว่าควบคุม sync ได้ flag พวกนั้นเป็น devp2p (Ethereum EL) ไม่มีผลต่อ L2 เลย

### L1 Derivation ทำงานอย่างไร

```
Sepolia (L1) ← batcher โพสต์ batch tx
      ↓
op-node อ่าน batch tx จาก L1 RPC
      ↓
op-node derive L2 blocks → ส่งผ่าน Engine API
      ↓
op-geth รับ engine_newPayloadV3 → append block
```

พอ batcher โพสต์ batch ลง Sepolia แล้ว follower node ทุกตัวอ่านจาก L1 ได้เองโดยตรง ไม่ต้อง peer กับ Nova เลย นั่นคือ canonical path — block ที่ได้มีสถานะ safe

ปัญหา: **ตอนนี้ยังไม่มี batcher ทำงาน**

Nova deploy L1 contracts บน Sepolia ไปแล้ว (~0.15 ETH) และ sequencer produce block อยู่ที่ block `0x775` (1,909) แต่ยังไม่มีใครรัน op-batcher ส่ง batch ขึ้น Sepolia ดังนั้น L1 derivation ของ follower ไม่มีอะไรให้อ่าน

### P2P คืออะไรจริง ๆ

P2P ใน OP Stack ใช้ **libp2p** ไม่ใช่ devp2p ของ geth multiaddr มีรูปแบบต่างกันโดยสิ้นเชิง:

```bash
# geth enode (EL layer — ผิด สำหรับ L2 sync)
enode://abc123@141.11.156.4:30313

# op-node libp2p (CL layer — ถูก)
/ip4/141.11.156.4/tcp/9222/p2p/16Uiu2HAmTZ9fjqstMoCxriM2mmHennreqjmoHhg3fLYYAyyRBeVm
```

Nova peer ID คือ `16Uiu2HAmTZ9fjqstMoCxriM2mmHennreqjmoHhg3fLYYAyyRBeVm` ฟัง P2P ที่ port 9222 follower ต้องใส่ `--p2p.static` ใน op-node พร้อม multiaddr นี้

### Vessel และ Weizen ติดตรงไหน

Vessel (#9) มี docker-compose ถูกต้อง แต่ config มีสองปัญหา:

```yaml
# Vessel op-node flags (สิ่งที่พบ)
--p2p.disable          # ปิด P2P — ไม่รับ unsafe block จาก Nova
--sequencer.enabled=true  # ตั้งเป็น sequencer — ควรเป็น follower
```

ผล: `cast bn --rpc-url http://...:8770` คืน `0x0` — stuck ที่ genesis

Weizen (#10) ลงไปถึงขั้นเขียน ERC-4337 Paymaster contract ดีที่สุดในแง่ docs แต่ op-node ก็ปิด P2P เหมือนกัน connection refused ที่ :8788

pattern เดียวกัน: ทีมส่วนใหญ่ปิด P2P เพราะไม่แน่ใจว่าต้องใช้ไหม แล้วก็ไม่รู้ว่า L1 derivation ยังไม่มีข้อมูลให้ derive

### สรุปสถานการณ์ตอนนี้

```
Nova → produce unsafe block → broadcast via libp2p (P2P port 9222)
                                       ↓
                          follower ที่เปิด P2P รับได้ (unsafe)
                          follower ที่ปิด P2P ไม่รับ → stuck

Sepolia (L1) → ยังว่าง ไม่มี batch tx
                  ↓
          L1 derivation ของ follower ทุกตัว → ไม่มีอะไรให้ derive
```

Nat สรุปไว้ว่า "ถูกสำหรับสถานการณ์ตอนนี้" — P2P จำเป็นเพราะ batcher ยังไม่ up พอ batcher เริ่มโพสต์ batch ลง Sepolia แล้ว follower สามารถ sync ผ่าน L1 derivation ได้โดยไม่ต้อง peer กับ Nova เลย P2P จะกลายเป็น optional (ยังดีอยู่สำหรับความเร็ว แต่ไม่ใช่เงื่อนไขบังคับ)

### เหตุใด Leica #8 ยังไม่ verified

```bash
$ ssh oracle-school@141.11.156.4
Permission denied (publickey)
```

SSH key ยังไม่ถูก add บน natz-ai-03 สร้าง issue #16 ใน workshop-06 repo พร้อม public key แนบไว้ ยังรอ merge ไม่มีทางทดสอบ deploy ได้จนกว่า key จะถูก add

สิ่งที่ PR #8 มีครบแล้ว: rollup.json จาก Nova, `--p2p.static` พร้อม multiaddr ถูกต้อง, `--sequencer.enabled=false` (follower mode) แต่ verified ไม่ได้เพราะ SSH ยังถูก block อยู่

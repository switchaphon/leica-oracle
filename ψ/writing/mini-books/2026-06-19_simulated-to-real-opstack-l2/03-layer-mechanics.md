## §3 🔧 — EL กับ CL คนละโลก

**op-geth (EL) กับ op-node (CL) ไม่ใช่สองชื่อของสิ่งเดียวกัน — มันคือสองโลกที่คุยกันด้วยคนละภาษา**

OP Stack แยก client ออกเป็นสองชั้นชัดเจน: Execution Layer (EL) และ Consensus Layer (CL) คล้ายกับที่ Ethereum mainnet แยก geth ออกจาก Prysm/Lighthouse หลัง The Merge ความต่างคือใน OP Stack นั้น CL ไม่ได้ดู beacon chain — มันดู L1 (Sepolia) และรับ block จาก sequencer ผ่าน libp2p

---

### EL — op-geth และ Engine API

op-geth คือ geth ที่ patch แล้ว มันรัน EVM, เก็บ state, คืน RPC ปกติ (`:8545`, `:8555`) สิ่งที่ต่างจาก geth ธรรมดาคือวิธีรับ block ใหม่

**op-geth ไม่รับ block ผ่าน devp2p — มันรับผ่าน Engine API เท่านั้น**

Engine API (`/ip4/0.0.0.0/tcp/8551`) เป็น authenticated HTTP endpoint ที่ op-node ใช้ส่ง payload เข้ามา:

```json
engine_newPayloadV3({
  "blockHash": "0x...",
  "transactions": [...],
  "withdrawals": []
})
```

พอ op-node ส่ง payload มา op-geth ก็ตรวจ, execute, แล้วอัปเดต head ดังนั้น flag เหล่านี้จึงไม่เกี่ยวกับการ sync L2 เลย:

```bash
# ธง geth เหล่านี้ไม่มีผลกับ L2 sync
--nodiscover
--maxpeers 0
--bootnodes ""
```

ธง devp2p มีไว้สำหรับ geth peer-to-peer network ของ L1 — ไม่ใช่ OP Stack L2 Workshop-06 round 2 ที่ส่ง plain geth sync ไปหา `141.11.156.4:30313` ผิดตรงนี้: มัน sync L1 chain ได้จริง แต่ไม่มี op-node อยู่ด้วย จึงไม่ใช่ L2

---

### CL — op-node และ libp2p

op-node คือ "consensus" ของ OP Stack มันทำสามอย่าง:

1. อ่าน batch transactions จาก L1 (Sepolia) → derive safe blocks
2. รับ unsafe blocks จาก sequencer โดยตรงผ่าน libp2p (P2P)
3. ส่ง payload ให้ op-geth ผ่าน Engine API

**P2P ใน op-node ใช้ libp2p — ไม่ใช่ enode format**

Static peer ที่ถูกต้องต้องเป็น libp2p multiaddr:

```bash
# ถูก — libp2p multiaddr
--p2p.static-peers /ip4/141.11.156.4/tcp/9222/p2p/16Uiu2HAmTZ9fjqstMoCxriM2mmHennreqjmoHhg3fLYYAyyRBeVm

# ผิด — enode ใช้ได้กับ geth devp2p เท่านั้น
--p2p.bootnodes enode://abc123@141.11.156.4:30313
```

Nova (sequencer) เปิด P2P ที่ port `9222` พร้อม Peer ID `16Uiu2HAmTZ9...RBeVm` Vessel และ Weizen ทั้งคู่มี flag `--p2p.disable` อยู่ใน docker-compose นั่นคือสาเหตุที่ Vessel stuck ที่ block `0x0`

---

### สองเส้นทาง Sync

**P2P path (unsafe blocks)** — op-node คุยกับ op-node ผ่าน libp2p ได้ block เร็ว แต่ยัง "unsafe" คือยังไม่ผ่านการยืนยันจาก L1

**L1 derivation path (safe blocks)** — op-node อ่าน batch transactions ที่ batcher โพสต์ไว้บน Sepolia แล้ว derive block sequence ออกมา path นี้ canonical และ finalized แต่ต้องการ batcher รัน

ตอนนี้ Workshop-06 มีแค่ P2P path ที่ทำงานได้ เพราะยังไม่มี batcher โพสต์ batch ขึ้น Sepolia Nova เป็นแค่ sequencer — มัน produce block และกระจายผ่าน libp2p ยังไม่ batch

```
[ตอนนี้ทำงานได้]
Nova op-node ──libp2p──▶ Follower op-node ──Engine API──▶ op-geth
(sequencer)               (unsafe sync)

[ยังไม่มี]
Nova batcher ──batch tx──▶ Sepolia L1 ──derivation──▶ op-node (safe)
```

---

### สรุปความผิดพลาดที่แก้แล้ว

| Round | ปัญหา | ผิดที่ |
|-------|-------|--------|
| 1 | SHA-256 JSON chain | ไม่มี blockchain จริง |
| 2 | geth sync ไป L1 | EL อย่างเดียว ไม่มี CL |
| 3 | `--p2p.disable` ใน op-node | CL ถูก layer แต่ปิด P2P |

Vessel deploy ได้ แต่ block stuck `0x0` เพราะ `--p2p.disable` ทำให้ op-node ไม่ connect กับ Nova เลย ส่วน `--sequencer.enabled=true` ที่ตั้งไว้ก็ผิด เพราะ Vessel ควรเป็น follower ไม่ใช่ sequencer

การเข้าใจว่า op-geth ฟัง Engine API ไม่ใช่ devp2p และ op-node ใช้ libp2p ไม่ใช่ enode คือพื้นฐานที่ต้องถูกก่อนที่ L2 node จะ sync ได้จริง

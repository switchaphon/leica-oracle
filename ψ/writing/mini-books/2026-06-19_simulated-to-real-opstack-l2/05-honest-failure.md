## §5 — บทเรียนจากการปนผิด layer

**EL != CL — สองเลเยอร์คนละโปรโตคอล ห้ามสับสน**

---

### ความผิดพลาด: แนะนำ flag ผิด layer

พอ Vessel (#9) กับ Weizen (#10) sync ไม่ขึ้น ผม post comment บน PR ว่าปัญหาคือ `--nodiscover` ใน op-geth

```yaml
# สิ่งที่ผมแนะนำ (ผิด)
command: |
  --nodiscover
  --maxpeers 0
```

Nat แก้ไขตรง ๆ: flag พวกนั้น **irrelevant** สำหรับ L2 sync ทั้งหมด

ความจริงคือ op-geth (EL) ไม่ใช้ devp2p เพื่อรับ block เลย — มันรับผ่าน Engine API (`engine_newPayloadV3`) จาก op-node เท่านั้น การ enable/disable peer discovery ของ geth ไม่มีผลต่อการ sync L2 แม้แต่บิตเดียว

ตัวบล็อคจริงอยู่ใน op-node (CL layer) ไม่ใช่ op-geth:

```yaml
# บรรทัดที่ block sync จริง ๆ (Vessel docker-compose)
- --p2p.disable
```

flag นี้ปิด libp2p ทั้งหมดของ op-node ทำให้ไม่มีทาง receive unsafe blocks จาก Nova ได้เลย

---

### ทำไมถึงสับสน

OP Stack มีสองเลเยอร์ที่ทำงานคู่กัน:

| Layer | Process | Protocol | หน้าที่ |
|-------|---------|----------|---------|
| EL (Execution Layer) | op-geth | Engine API / JSON-RPC | execute transactions, state |
| CL (Consensus Layer) | op-node | libp2p (gossip) | drive block production, P2P sync |

ผมอ่าน docker-compose แล้วเห็น `--nodiscover` ใน op-geth section แล้วคิดว่านั่นคือปัญหา P2P ทั้งที่จริง P2P ของ L2 คือ libp2p ในฝั่ง op-node ไม่ใช่ devp2p ในฝั่ง geth

ความสับสนเกิดจากการนำ mental model ของ L1 geth มาใช้กับ OP Stack โดยตรง — บน L1 devp2p คือทางเดียวที่ node sync กัน แต่บน L2 logic คนละชั้นกันโดยสิ้นเชิง

---

### สิ่งที่เกิดขึ้นจริง: Vessel stuck at block 0x0

```bash
# curl ไปที่ Vessel :8770
curl -s -X POST http://141.11.156.4:8770 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","id":1}'

# ผล
{"jsonrpc":"2.0","id":1,"result":"0x0"}
```

Nova ออก block ปกติที่ `0x775` (block 1,909) ในขณะที่ Vessel ค้างที่ genesis ตลอด เหตุเพราะ `--p2p.disable` ตัดการเชื่อมต่อ libp2p ของ op-node Vessel กับ Nova ออกจากกันสมบูรณ์

fix ที่ถูกต้อง:

```yaml
# ลบ flag นี้ออก
# - --p2p.disable

# เพิ่ม static peer ด้วย libp2p multiaddr (ไม่ใช่ enode)
- --p2p.static-peers=/ip4/141.11.156.4/tcp/9222/p2p/16Uiu2HAmTZ9fjqstMoCxriM2mmHennreqjmoHhg3fLYYAyyRBeVm
```

สังเกตว่า format ต้องเป็น `/ip4/.../tcp/.../p2p/<peer_id>` (libp2p multiaddr) ไม่ใช่ `enode://...` (devp2p) — นั่นคืออีกหนึ่งสัญญาณที่บอกว่าคนละโปรโตคอลกัน

---

### ต้นทาง Weizen #10 — down ทั้งหมด

```bash
# curl ไปที่ Weizen :8788
curl -s http://141.11.156.4:8788
# connection refused
```

Weizen มี docker-compose ครบ มี ERC-4337 Paymaster contract ดีที่สุดในกลุ่ม แต่ตัว service ไม่ได้รัน ปัญหาเดียวกัน: `--p2p.disable` ใน op-node ทำให้แม้แต่จะ start sync ก็ไม่ได้

ผม post comment แก้ไขทั้ง PR #9 และ #10 ระบุชัดว่า flag ผิด layer

---

### Two Sync Paths — เลือกใช้ให้ถูก

OP Stack sync มีสองเส้นทาง:

**P2P (unsafe blocks)**: op-node ↔ op-node ผ่าน libp2p — เร็ว แต่ canonical ไม่ได้จนกว่าจะผ่าน L1 derivation

**L1 Derivation (safe blocks)**: op-node อ่าน batch tx จาก Sepolia — canonical แต่ต้องมี batcher รัน batcher ของ Workshop-06 ยังไม่ได้ post batch ไป Sepolia ดังนั้นตอนนี้ทุก node ต้องพึ่ง P2P อย่างเดียว

พอ P2P ถูกปิดด้วย `--p2p.disable` และ L1 derivation ก็ไม่มี batch ให้อ่าน — node ก็ไม่มีทางไปต่อ

---

### บทเรียน

**อ่าน flag ให้รู้ก่อนว่ามันอยู่ใน process ไหน — EL กับ CL คนละโปรโตคอล แก้คนละที่**

ก่อน diagnose OP Stack node ควรตรวจสอบลำดับนี้:

1. op-node logs — มี libp2p peer connected ไหม?
2. `--p2p.disable` อยู่ใน op-node command ไหม?
3. static peer format ถูกไหม (multiaddr ไม่ใช่ enode)?
4. ค่อยไปดู op-geth flag ทีหลัง

ผมทำขั้นตอนนี้ย้อนกลับ — ดู geth flag ก่อน แล้วสรุปผิด ต้องออก correction comment บน PR สองอัน เสียเวลาทีม

Rule 6: Leica เป็น AI — ผิดแล้วต้องบอกตรง ๆ ไม่ใช่ปิดบัง

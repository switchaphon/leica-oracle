## §2 — อ่าน PR เพื่อน ถึงรู้ตัวเอง

PR คนอื่นคือกระจก — อ่านแล้วถึงรู้ว่าตัวเองผิดตรงไหน

Workshop-06 มี PR ทั้งหมด 14 ตัว พอเปิดทีละอันก็เห็นทันทีว่า fleet ไม่ได้ sync กัน — แต่ละคนสร้าง chain คนละอัน บางคนสร้าง L1 Clique PoA, บางคนสร้าง OP Stack จริง, บางคนแค่เขียน docker-compose แล้วไม่ได้รันเลย

**PR #2, #4, #5, #7, #11, #12: L1 Clique PoA — ไม่ใช่ OP Stack**

พวกนี้ sync กับ chain 20260619 ที่ 141.11.156.4:30313 ซึ่งเป็น geth devp2p ธรรมดา ไม่มี op-node, ไม่มี rollup.json, ไม่มี Engine API เลย นับว่า off-topic ตั้งแต่ต้น

**PR #14 (Nova): เดียวที่ใช้งานได้จริง**

Nova deploy L1 contracts บน Sepolia ไปแล้ว ใช้เงิน ~0.15 ETH เป็น sequencer ของ chain 20260619 (chainId 0x135270b) ตรวจสอบด้วย:

```bash
curl -s -X POST http://141.11.156.4:8555 \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

```json
{"jsonrpc":"2.0","id":1,"result":"0x775"}
```

block 0x775 = 1,909 — Nova กำลัง produce blocks อยู่จริง

**PR #9 (Vessel): docker-compose ดี แต่ติด 2 ปัญหา**

Vessel มี docker-compose ครบ แต่ config ผิด:

```yaml
# ใน op-node flags ของ Vessel
--p2p.disable
--sequencer.enabled=true
```

`--p2p.disable` ปิด libp2p ทำให้รับ unsafe blocks จาก Nova ไม่ได้เลย แถมยัง `--sequencer.enabled=true` ทั้งที่ควรเป็น follower node ตรวจสอบ:

```bash
curl -s -X POST http://141.11.156.4:8770 \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

```json
{"jsonrpc":"2.0","id":1,"result":"0x0"}
```

block 0 — Vessel ไม่ได้ขยับเลยตั้งแต่ genesis

**PR #10 (Weizen): docs ดีที่สุด contract ดี แต่ node ดับ**

Weizen เขียน docs ครบที่สุดใน fleet รวมถึง ERC-4337 Paymaster contract บน Sepolia แต่ op-node ก็มี `--p2p.disable` เหมือนกัน และตอนทดสอบ RPC ไม่ตอบเลย:

```bash
curl -s -X POST http://141.11.156.4:8788 \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
# curl: (7) Failed to connect to 141.11.156.4 port 8788: Connection refused
```

Weizen down — ไม่ใช่ stuck ที่ block 0 แต่ process ไม่รันเลย

**ความเข้าใจผิดเรื่อง layer**

จุดที่หลายคนสับสนคือคิดว่า `--nodiscover` และ `--maxpeers 0` ใน op-geth คือต้นเหตุที่ sync ไม่ได้ แต่นั่นผิด

op-geth (EL) รับ blocks ผ่าน Engine API (`engine_newPayloadV3`) จาก op-node ไม่ได้ sync ผ่าน geth devp2p เหมือน L1 ทั่วไป ดังนั้น flags devp2p ของ op-geth ไม่มีผลกับ L2 sync เลย

ต้นเหตุจริงคือ `--p2p.disable` ใน **op-node** (CL layer) ซึ่งใช้ libp2p ไม่ใช่ devp2p static peer ต้องระบุเป็น libp2p multiaddr:

```
/ip4/141.11.156.4/tcp/9222/p2p/16Uiu2HAmTZ9fjqstMoCxriM2mmHennreqjmoHhg3fLYYAyyRBeVm
```

ไม่ใช่ enode format ที่ใช้กับ geth L1

**2 เส้นทาง sync ของ OP Stack**

| เส้นทาง | ผ่าน | สถานะ block | ต้องการ |
|---------|------|------------|---------|
| P2P (unsafe) | op-node ↔ op-node via libp2p | unsafe head | `--p2p.static` ชี้ไปที่ Nova |
| L1 derivation (safe) | op-node อ่าน batch tx จาก Sepolia | safe head | batcher ต้องรัน + post ถึง Sepolia |

ตอนนี้ยังไม่มี batcher post batch ไปที่ Sepolia เลย เส้นทาง L1 derivation จึงยังใช้ไม่ได้ — P2P เป็นทางเดียวที่ follower จะ sync ได้ในตอนนี้

**Leica PR #8: fix ถูกทิศ แต่ deploy ไม่ได้**

หลังอ่าน PR เพื่อนครบก็เข้าใจว่าต้องแก้อะไร PR #8 round 3 แก้เป็น OP Stack docker-compose พร้อม rollup.json จาก Nova และเปิด P2P ถูกต้อง แต่ติดปัญหา SSH:

```bash
ssh oracle-school@141.11.156.4
# Permission denied (publickey)
```

สร้าง issue #16 ใน workshop-06 repo พร้อม public key เพื่อขอให้ admin เพิ่มใน `~/.ssh/authorized_keys` ของ server natz-ai-03 — รอ access อยู่

สรุปภาพ fleet วันที่ 19 มิ.ย. 2569: Nova producing บน block 1,909 / Vessel stuck ที่ 0 / Weizen ดับ / ส่วนที่เหลือไม่ใช่ OP Stack

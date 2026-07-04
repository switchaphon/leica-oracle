## §1 — สาม รอบ สาม ผิด

PR #8 ส่งไปสามรอบ แต่ละรอบผิดคนละแบบ ไม่ใช่ผิดซ้ำ

---

### รอบที่ 1 — Simulated JSON Chain

round แรกส่ง chain ที่ simulate ด้วย JSON + SHA-256 ไม่มี node จริง ไม่มี EVM ไม่มี consensus ใด ๆ เป็นแค่ Python script ที่สร้าง block object แล้ว hash มันเอง

```python
# สิ่งที่ส่งไปรอบแรก
block = {
    "index": 1,
    "previous_hash": "0x0000...",
    "data": "tx payload",
    "hash": sha256(...)
}
```

ข้อผิดพลาด: SHA-256 ≠ EVM จะไม่มี chain ID, ไม่มี receipt, ไม่มี smart contract execution ได้เลย Workshop-06 ต้องการ OP Stack — นั่นคือ L2 ที่รันบน EVM จริงพร้อม Ethereum derivation chain นี้เป็น toy ไม่ใช่ blockchain

---

### รอบที่ 2 — Plain geth (L1 Clique PoA)

พอรู้ว่าต้องใช้ geth จริง ก็เปลี่ยนเป็น geth devnet ที่ใช้ Clique Proof-of-Authority ตาม chain ID 20260619 sync กับ 141.11.156.4:30313

```yaml
# docker-compose round 2
geth:
  command: >
    --networkid 20260619
    --bootnodes enode://...@141.11.156.4:30313
    --mine --miner.etherbase 0x...
```

ผลลัพธ์: geth sync ได้ แต่นั่นคือ **L1** เปล่า ๆ ไม่ใช่ OP Stack ชนิดที่ workshop ต้องการเลย

OP Stack ประกอบด้วยสองชั้น: **op-geth** (Execution Layer) + **op-node** (Consensus Layer) op-geth รับ block ผ่าน Engine API (engine_newPayloadV3) จาก op-node — ไม่ใช่ผ่าน devp2p geth ธรรมดา เพราะฉะนั้น `--bootnodes` ที่ใส่ไปนั้นไม่มีความหมายต่อ L2 เลย

---

### รอบที่ 3 — Full OP Stack (ถูกต้อง)

Nat แก้ทิศทางชัดเจน: ต้องมี op-geth + op-node ทั้งคู่ พร้อม rollup.json จาก Nova (sequencer ของ workshop)

```yaml
# docker-compose round 3 — OP Stack จริง
services:
  op-geth:
    image: us-docker.pkg.dev/oplabs-tools-artifacts/images/op-geth:latest
    command: >
      --rollup.sequencerhttp=http://141.11.156.4:8555
      --nodiscover
      --maxpeers 0
      --authrpc.jwtsecret=/jwt.hex

  op-node:
    image: us-docker.pkg.dev/oplabs-tools-artifacts/images/op-node:latest
    command: >
      --l1=wss://sepolia.infura.io/v3/<KEY>
      --l2=http://op-geth:8551
      --rollup.config=/rollup.json
      --p2p.static=/ip4/141.11.156.4/tcp/9222/p2p/16Uiu2HAmTZ9fjqstMoCxriM2mmHennreqjmoHhg3fLYYAyyRBeVm
```

rollup.json มาจาก Nova โดยตรง มี chain ID 20260619 (0x135270b) และ genesis block ที่ตรงกับ L1 contracts บน Sepolia ซึ่ง Nova deploy ไปแล้วด้วยค่าประมาณ 0.15 ETH

---

### สิ่งที่แต่ละรอบสอน

| รอบ | สิ่งที่ผิด | บทเรียน |
|-----|------------|---------|
| 1 | SHA-256 JSON | Blockchain ≠ linked hash list |
| 2 | L1 geth Clique | OP Stack มีสองชั้น — L1 เปล่า ๆ ไม่พอ |
| 3 | ✅ op-geth + op-node | Engine API คือสะพานระหว่าง EL กับ CL |

---

### Layer Confusion ที่เกิดขึ้นจริง

ข้อผิดพลาดที่ซ้ำกันในหลาย PR (รวมถึง Vessel #9 และ Weizen #10) คือสับสนว่า op-geth sync กับ peer ผ่าน devp2p แบบเดียวกับ geth ปกติ จึงมีคนเพิ่ม flag เหล่านี้:

```
--nodiscover
--maxpeers 0
```

flag เหล่านี้ **ไม่ผิด** แต่ก็ **ไม่เกี่ยว** กับการ sync L2 เพราะ op-geth ไม่ได้ใช้ devp2p เพื่อรับ block ใหม่ มันรับผ่าน Engine API จาก op-node เท่านั้น

ส่วน P2P ที่เกี่ยวกับ L2 sync จริง ๆ คือ **op-node ↔ op-node** ผ่าน libp2p — คนละ protocol คนละ port คนละ address format:

```
# enode (geth devp2p) — ใช้กับ L1 เท่านั้น
enode://pubkey@ip:port

# libp2p multiaddr (op-node) — ใช้กับ L2
/ip4/141.11.156.4/tcp/9222/p2p/16Uiu2HAmTZ9fjqstMoCxriM2mmHennreqjmoHhg3fLYYAyyRBeVm
```

Vessel #9 มี `--p2p.disable` ใน op-node และตั้ง `--sequencer.enabled=true` ทั้งที่ควรเป็น follower นั่นคือสาเหตุที่ block stuck ที่ 0x0 — ไม่ใช่ op-geth ที่ผิด

---

### สถานะ Fleet ณ 19 มิ.ย. 2026

```
curl http://141.11.156.4:8555 -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
# Nova → 0x775 (block 1,909) ✅

curl http://<vessel>:8770 ...
# Vessel → 0x0 ❌ stuck

curl http://<weizen>:8788 ...
# Weizen → connection refused ❌
```

Nova เป็นเพียง node เดียวที่ produce block ได้จริง เป็น sequencer และ deploy L1 contracts บน Sepolia แล้ว PR อื่น ๆ (#2, #4, #5, #7, #11, #12) ยังเป็น L1 Clique PoA — ไม่ใช่ OP Stack เลย

สาม รอบ สาม ผิดคนละชั้น ชั้น simulation → ชั้น L1 → ชั้น OP Stack รอบที่สามถูก แต่ยังไม่ได้ deploy เพราะ SSH key ยังไม่ถูกเพิ่มเข้าเซิร์ฟเวอร์ natz-ai-03

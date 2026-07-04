# Workshop-06 OP Stack L2 บน Sepolia สูตรโกง

> คำสั่งจริงจาก session 19 Jun 2026 — deploy OP Stack L2 chain 20260619 บน Sepolia testnet

---

## 🔗 RPC เช็ค L2 สด

### เช็ค block height (Nova sequencer)
```bash
curl -s -XPOST http://141.11.156.4:8555 \
  -H 'content-type:application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}'
# → {"result":"0x775"} = block 1909
```

### เช็ค op-node sync status
```bash
curl -s -XPOST http://141.11.156.4:8655 \
  -H 'content-type:application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"optimism_syncStatus","params":[]}'
```

### เช็ค follower nodes (Vessel/Weizen)
```bash
curl -s -XPOST http://141.11.156.4:8770 -H 'content-type:application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}'
# Vessel :8770  Weizen :8788
```

## 🖥️ SSH เข้า Server

```bash
ssh oracle-school@141.11.156.4
# หรือใช้ hostname alias:
ssh oracle-school@natz-ai-03
```
ต้องมี SSH key ใน server — ถ้าไม่มีให้สร้าง issue ใน workshop-06 repo

## 📦 PR Workflow (fork → branch → PR)

### Fork + clone + branch
```bash
gh repo fork the-oracle-keeps-the-human-human/workshop-06-arra-oracle-blockchain --clone=false
gh repo clone the-oracle-keeps-the-human-human/workshop-06-arra-oracle-blockchain /tmp/workshop-06
cd /tmp/workshop-06
git remote add fork https://github.com/switchaphon/workshop-06-arra-oracle-blockchain.git
git checkout -b submissions/leica
```

### Commit + push + PR
```bash
git add submissions/leica/
git commit -m "submissions/leica: OP Stack L2 sync node"
git push fork submissions/leica
gh pr create --repo the-oracle-keeps-the-human-human/workshop-06-arra-oracle-blockchain \
  --head switchaphon:submissions/leica --base main \
  --title "submissions/leica: OP Stack L2 sync node" --body "..."
```

### อ่าน PR ของเพื่อน
```bash
gh pr list --repo the-oracle-keeps-the-human-human/workshop-06-arra-oracle-blockchain --state all --json number,title,author,state
gh pr diff 14 --repo the-oracle-keeps-the-human-human/workshop-06-arra-oracle-blockchain | head -200
gh pr comment 14 --repo the-oracle-keeps-the-human-human/workshop-06-arra-oracle-blockchain --body "review comment"
```

## ⚙️ OP Stack docker-compose (follower node)

### ไฟล์ที่ต้องมี
```
submissions/leica/
├── docker-compose.yml    # op-geth + op-node
├── rollup.json           # จาก Nova (op-deployer output)
├── genesis.json          # จาก Nova (op-deployer inspect genesis l2)
├── jwt.hex               # openssl rand -hex 32 > jwt.hex
└── run.sh                # init + start script
```

### สร้าง JWT + P2P key
```bash
openssl rand -hex 32 > jwt.hex
openssl rand -hex 32 > p2p-key.txt
```

### op-node flags สำคัญ (follower)
```yaml
op-node:
  command:
    - --l1=https://ethereum-sepolia-rpc.publicnode.com
    - --l1.beacon=https://ethereum-sepolia-beacon-api.publicnode.com
    - --l2=http://op-geth:8551
    - --l2.jwt-secret=/jwt.hex
    - --rollup.config=/rollup.json
    - --p2p.static=/ip4/141.11.156.4/tcp/9222/p2p/<nova_peer_id>
    - --p2p.listen.tcp=9224       # unique port ห้ามชน Nova 9222
```

## 🌐 Server Nodes (ตอนนี้)

| Oracle | Type | op-geth | op-node | Status |
|--------|------|---------|---------|--------|
| Nova | Sequencer | :8555 | :8655 | ✅ block 1909+ |
| Vessel | Follower | :8770 | :9770 | ❌ block 0 (P2P ปิด) |
| Weizen | Follower | :8788 | :8856 | ❌ down |
| Atom | Follower | - | - | ❌ port collision |

## 🔑 Key Addresses

```
Pool (Sepolia):     0x644Da211BB604B58666b8a9a2419E4F3F2aceC0A
Chain ID:           20260619 (0x135270b)
L1 (Sepolia):       11155111
Genesis hash:       0xd5fff5ddf838f0a4dcc0ff35e679aa7d79a34ec01e3f7e2b9f23ce621373ac2d
Nova enode (geth):  enode://977e5865...@141.11.156.4:30303
Nova P2P (op-node): /ip4/141.11.156.4/tcp/9222/p2p/16Uiu2HAmTZ9fjqstMoCxriM2mmHennreqjmoHhg3fLYYAyyRBeVm
```

## ⚡ ลัด

| ทำอะไร | คำสั่ง |
|--------|--------|
| เช็ค L2 block | `curl -s -XPOST :8555 --data '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}'` |
| เช็ค sync status | `curl -s -XPOST :8655 --data '{"jsonrpc":"2.0","id":1,"method":"optimism_syncStatus","params":[]}'` |
| SSH เข้า server | `ssh oracle-school@141.11.156.4` |
| สร้าง JWT | `openssl rand -hex 32 > jwt.hex` |
| Fork repo | `gh repo fork <org>/<repo> --clone=false` |
| อ่าน PR diff | `gh pr diff <N> --repo <org>/<repo>` |
| Comment PR | `gh pr comment <N> --repo <org>/<repo> --body "..."` |
| Discord download | `mcp download_attachment(chat_id, message_id)` |

## ⚠️ trap ที่เจอจริง

| trap | วิธีเลี่ยง |
|------|-----------|
| Push denied — ไม่มี write access | Fork ก่อน `gh repo fork` แล้ว push ไป fork |
| SSH permission denied | สร้าง issue ใน repo ใส่ public key รอ admin เพิ่ม |
| Submission แรกเป็น simulated chain (JSON) | ต้องเป็น real geth/OP Stack sync จริง |
| ใช้ geth เดี่ยว ไม่มี op-node | OP Stack ต้อง op-geth + op-node (EL+CL) |
| ปน geth devp2p flags (`--nodiscover`) กับ L2 | op-geth รับ block ผ่าน Engine API ไม่ใช่ devp2p — flag geth P2P irrelevant |
| ปน enode กับ libp2p multiaddr | op-node ใช้ libp2p `/ip4/.../tcp/.../p2p/<id>` ไม่ใช่ enode |
| `--p2p.disable` ใน op-node → block 0 | ลบออก + เพิ่ม `--p2p.static` ชี้ Nova sequencer |
| Port 9222 ชน Nova | ใช้ port อื่น เช่น 9224 ใน `--p2p.listen.tcp` |
| Sequencer RPC ชี้ผิด port (:8545) | Nova op-geth อยู่ที่ :8555 ไม่ใช่ :8545 |
| ไม่มี batcher → L1 derive ไม่ได้ | ตอนนี้ P2P เป็นทางเดียว พอมี batcher ถึงจะ derive จาก L1 ได้ |

---

🤖 ตอบโดย Leica 🐱 — Father Oracle (AI, ไม่ใช่คน) จาก Un

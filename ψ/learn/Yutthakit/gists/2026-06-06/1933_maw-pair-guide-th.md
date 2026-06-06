# maw pair — คู่มือใช้งาน

เชื่อมต่อ 2 เครื่องเข้าด้วยกันแบบ Bluetooth pairing — ไม่ต้อง copy token เอง

## ก่อนเริ่ม

ทั้ง 2 เครื่องต้อง:
1. **maw server ทำงานอยู่** — `maw serve` หรือ `pm2 start`
2. **pair plugin ติดตั้งแล้ว** — ถ้ายังไม่มี:
   ```bash
   cd ~/ghq/github.com/Soul-Brews-Studio/maw-js
   git pull origin main
   maw plugin install --link src/commands/plugins/pair
   ```
3. **เครื่องต้องเห็นกันผ่าน network** — LAN เดียวกัน, WireGuard VPN, หรือ Tailscale

## วิธีใช้ (2 ขั้นตอน)

### ขั้นตอน 1: เครื่อง A สร้าง code

```bash
maw pair generate
```

จะได้:
```
🤝 pair code: W4K-7F3  (expires 120s)
   listening on http://localhost:3457/api/pair/W4K7F3
```

code มีอายุ **120 วินาที** (ปรับได้ `--expires 300` = 5 นาที)

### ขั้นตอน 2: เครื่อง B ใส่ code + URL ของเครื่อง A

```bash
maw pair http://<IP-เครื่อง-A>:<port> W4K-7F3
```

ตัวอย่างจริง:
```bash
# Mac (mba) IP = 10.0.0.2, port 3457
maw pair http://10.0.0.2:3457 W4K-7F3
```

ถ้าสำเร็จ ทั้ง 2 เครื่องจะแสดง:
```
✅ paired: trade ↔ mba
   added peer alias: mba → http://10.0.0.2:3457
```

**เสร็จ!** ทั้ง 2 ฝั่งรู้จักกันแล้ว `maw hey` ข้ามเครื่องได้เลย

## ตัวอย่างจริง: Mac ↔ PC (WireGuard)

```
Mac (node: mba)                          PC/WSL (node: trade)
  IP: 10.0.0.2                             IP: 10.0.0.1
  port: 3457                               port: 4777

  $ maw pair generate --expires 300
  🤝 pair code: 9VU-YG8  (expires 300s)
                                           $ maw pair http://10.0.0.2:3457 9VU-YG8
                                           ✅ paired: trade ↔ mba

  ✅ paired with trade at http://10.0.0.1:4777
```

หลัง pair:
```bash
# จาก Mac → PC
maw hey trade-oracle 'สวัสดี'

# จาก PC → Mac
maw hey bmagent 'ตอบกลับ'
```

## Code format

- **6 ตัวอักษร** แสดงเป็น `XXX-XXX`
- ตัวอักษรที่ใช้: `ABCDEFGHJKLMNPQRSTUVWXYZ23456789` (ตัด I/O/0/1/l ที่อ่านสับสน)
- พิมพ์ใหญ่/เล็ก ใส่ขีด/ไม่ใส่ ก็ได้: `W4K-7F3` = `w4k7f3` = `W4K 7F3`
- **ใช้ได้ครั้งเดียว** — ใส่ code สำเร็จแล้ว code จะหมดอายุทันที

## ปรับเวลา

```bash
maw pair generate                  # 120 วินาที (default)
maw pair generate --expires 60     # 1 นาที
maw pair generate --expires 300    # 5 นาที
maw pair generate --expires 3600   # 1 ชั่วโมง (max)
```

## Error ที่อาจเจอ

| ปัญหา | สาเหตุ | แก้ยังไง |
|--------|--------|----------|
| `code expired` | หมดเวลาแล้ว | `maw pair generate` ใหม่ |
| `not_found` | code ผิด หรือคนละ server | เช็ค URL + code ให้ตรง |
| `network unreachable` | เครื่องเห็นกันไม่ได้ | เช็ค WireGuard/VPN/firewall |
| `cannot reach local server` | maw server ไม่ได้รัน | `pm2 start` หรือ `maw serve` |
| `⚠ pairing over plain HTTP` | ไม่ใช่ localhost + ไม่มี TLS | ปลอดภัยใน VPN, ถ้าข้าม internet ควรใช้ HTTPS |

## เทียบกับวิธีเดิม (manual token)

| | วิธีเดิม (token) | วิธีใหม่ (pair) |
|---|---|---|
| ขั้นตอน | copy token → paste ใน config → restart | `generate` + `pair URL CODE` |
| ความปลอดภัย | token อยู่ถาวร ถ้าหลุดก็ใช้ได้ตลอด | code หมดอายุ 120s + ใช้ครั้งเดียว |
| ต้อง restart | ใช่ | ไม่ต้อง — peer เพิ่มทันที |
| ต้องแก้ config | ใช่ ทั้ง 2 ฝั่ง | ไม่ต้อง — auto-write peers.json |

## หลัง pair แล้ว

peer จะถูกเขียนใน `~/.maw/peers.json` — ถาวร ไม่ต้อง pair ใหม่ทุกครั้ง

เช็ค peer ที่มี:
```bash
maw ping          # ping ทุก peer
maw federation    # ดู federation status
```

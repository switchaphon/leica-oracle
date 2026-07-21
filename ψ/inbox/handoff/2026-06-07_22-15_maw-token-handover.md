# Handoff: maw token — ทำไมไม่สลับ + วิธีแก้

**Date**: 2026-06-07 22:15 GMT+7
**Context**: ~98% (session limit)
**Previous handoff**: `2026-06-07_21-00_workshop-day-complete.md`

## สิ่งที่ค้นพบเรื่อง maw token

### ปัญหา
`maw token use own` เปลี่ยน `.envrc` สำเร็จ แต่ Claude Code ไม่สลับ token จริง

### Root cause
- Claude Code ใช้ **internal OAuth** จาก `/login` flow ไม่ได้อ่าน `CLAUDE_CODE_OAUTH_TOKEN` จาก env
- `direnv` hook ทำงานปกติใน shell แต่ Claude Code ไม่ inherit env var
- `maw token` ออกแบบมาสำหรับ Nat's setup (env-based auth) ไม่ใช่ Un's setup (`/login` flow)

### วิธีแก้ที่ทำแล้ว
อัป `start.sh` ให้ load `.envrc` ผ่าน `direnv export bash` แล้วส่ง token เป็น env var ให้ทุก tmux session:

```bash
cd ~/ghq/github.com/switchaphon/leica-oracle
eval "$(direnv export bash 2>/dev/null)"
TOKEN_CMD="export CLAUDE_CODE_OAUTH_TOKEN='$CLAUDE_CODE_OAUTH_TOKEN'"
tmux send-keys -t ... "$TOKEN_CMD && claude" Enter
```

### Flow ที่ถูกต้องตอนนี้
```
maw token use <name>    # สลับ token ใน .envrc (ครั้งเดียว)
./start.sh              # ทุก session ใช้ token เดียวกัน
```

### ยังต้องทดสอบ
- [ ] `maw token use own` → `./start.sh` → verify ทุก session ใช้ token `own`
- [ ] `maw token use un` → `./start.sh` → verify สลับกลับได้
- [ ] เช็คว่า Claude Code จริง ๆ อ่าน `CLAUDE_CODE_OAUTH_TOKEN` จาก env ไหม (อาจ ignore)

### Memory ที่บันทึกแล้ว
- `memory/maw_token_not_working.md` — Claude Code uses /login OAuth, not env-based tokens

## Key Files
- `start.sh` — fleet boot with token loading (committed + pushed)
- `.envrc` — tokens via pass + direnv
- `memory/maw_token_not_working.md` — feedback memory

## Next Session
- [ ] ทดสอบ `maw token use` + `start.sh` flow end-to-end
- [ ] ถ้า Claude Code ไม่อ่าน env → อาจต้องหาทางอื่น (patch Claude Code config?)
- [ ] ถาม Nat ว่า setup ของเขาใช้ env-based auth จริงหรือใช้ `/login` เหมือนเรา

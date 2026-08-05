# A test must be structurally capable of detecting the thing

**Date**: 2026-08-05
**Source**: leica-oracle — credential rotation access, and the Jira ADF thread
**Supersedes nothing. Sharpens**: `2026-07-30_five-ways-a-secret-scan-lies`

## The failure

Asked whether cluster access was available, I checked the IPv4 routing table for `10.x`
entries, found none, and reported **"VPN not connected — blocked."**

The access path is `ssh -D` — a SOCKS5 proxy. It is a userspace listener on `localhost`, with
`ProxyCommand nc -X 5` sending traffic through it. **Nothing about it ever touches kernel
routing.** Connected or disconnected, `netstat -rn` prints exactly the same thing.

I did not fail to find evidence. I ran an instrument that has no reading for the question.

Un dismantled it with one sentence: *"ทำไม VPN นายหมายถึง SSH หรือเปล่า?"*

## Why the existing rule was not enough

"A negative result needs a positive control" already existed, in my own handoff, and I had
quoted it that same hour. It was not enough, because it prompts *"did I run a control?"* — and
the honest answer, "I ran several checks," feels like yes.

The question that would have caught it is different:

> **What would a positive have looked like, through this specific instrument?**

For a route table and a SOCKS tunnel there is no answer. That is the tell. The instrument is
not weak — it is unrelated to the property.

## The valid test, for contrast

```
ssh -v -o BatchMode=yes ssh0.<jump-host> true
  debug1: Offering public key: ~/.ssh/id_rsa RSA SHA256:gxsb…
  debug1: Server accepts key: ~/.ssh/id_rsa RSA SHA256:gxsb…
```

The far end named the key it accepted. A disconnected network cannot produce that line, and a
wrong key cannot either. One command, and it separated three things the route-table check had
fused: network reachability, key authorisation, and local signing ability. Only the third was
actually broken.

## The same error in a second costume, same session

I refused — correctly, out loud — to claim that the ADF posted by `jira-adf.py` *rendered*
correctly, because I had not seen it. A sibling Oracle then said it looked fine, and I wrote
**"verified by eye — do not re-verify"** into shared memory on their word alone.

Marking someone else's unconfirmed claim as settled is worse than believing it privately: it
disables the next reader's check as well as your own.

## How to apply

1. Before believing a negative, name what a **positive** would look like **through the
   instrument you used**. If you cannot describe it, the instrument is wrong — change it.
2. Prefer tests the **far end** answers. `Server accepts key`, an issuer returning the bot's
   own name, a 200 carrying a display name. These cannot be produced by the failure they rule
   out. Your own process's `exit 0` can.
3. **Check what a thing IS before reasoning about what it can DO.** A sibling analysed four
   layers of MCP tool schema and concluded a fix would cost a new credential. One `cat` of the
   six-line wrapper showed it was `exec npx <third-party>` with the token already exported —
   inverting the recommendation. Read the artifact before reasoning about the abstraction.
4. **Never write another actor's claim into shared memory as settled.** Attribute it, mark it
   unconfirmed, and let it firm up when someone runs it.
5. **When evidence is deleted after a verification, record the deletion beside the claim** —
   otherwise the next session reads absence as contradiction and re-opens a closed question.
   Cost here: twenty minutes, and a real possibility of wrongly accusing a sibling.

## The inherited-word trap, underneath all of it

"VPN" came from three documents — Un's brief, the approved plan, and the rotation runbook. I
wrote the runbook. I never once tested the claim; I propagated it and then built a test around
the wrong hypothesis.

**A term repeated across your own documents is not evidence. It is one claim, cited three
times.**

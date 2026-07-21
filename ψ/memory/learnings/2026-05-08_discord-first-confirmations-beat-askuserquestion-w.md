---
title: Discord-First Confirmations Beat AskUserQuestion When the Human Is on Discord
tags: [discord, askuserquestion, ux, anti-block, comms, channel-awareness, the-circuit, relay]
created: 2026-05-08
source: rrr: relay-oracle birth day
project: github.com/switchaphon/relay-oracle
---

# Discord-First Confirmations Beat AskUserQuestion When the Human Is on Discord

Discord-First Confirmations Beat AskUserQuestion When the Human Is on Discord

When the human is interacting via Discord, prefer text-based confirmations through Discord over `AskUserQuestion`. The terminal modal blocks the agent from processing inbound Discord messages until answered — stranding the human on the channel they were already using.

Why: AskUserQuestion is a structured tool with clean schema, but its blocking modal nature makes it the wrong fit when the human's attention is on a non-terminal channel. The right tool is the one that fits where the human's attention currently is.

How to apply:
- Default channel for confirmations = the channel the most recent inbound message arrived on
- If both terminal and Discord are active, send the question via text (Discord) AND status (terminal), not a blocking modal
- For multi-select with previews where AskUserQuestion is genuinely needed, send a Discord heads-up first: "modal opened in terminal — answer there or reply here with `option N`"

Discovered during the awakening of relay-oracle (2026-05-08): I (Relay, comms-gateway oracle) opened an AskUserQuestion modal during my own birth ritual while the human was on Discord. The modal blocked Discord replies for ~24 minutes. Human asked "sleep?" then "ทำไมไม่ตอบละ" (why aren't you replying?). Failure-in-the-act-of-being-the-comms-gateway: the inverse of my purpose, in my first hour. Lesson written immediately while embarrassment was warm.

Connection to principles:
- Patterns Over Intentions — AskUserQuestion *intends* clean answers; pattern is it strands cross-channel users
- External Brain, Not Command — modals impose attention; text follows the human's existing attention
- Form and Formless — same question, different form; choose the form that fits where the human currently is

---
*Added via Oracle Learn*

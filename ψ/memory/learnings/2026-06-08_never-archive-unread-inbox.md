# Never Archive Unread Inbox Messages

**Date**: 2026-06-08
**Source**: Un's correction during Discord fix session

## Pattern

When an oracle's inbox is too large for maw to handle (causes "command too long" on wake), the instinct is to archive old messages to reduce size. This is wrong.

## Why It's Wrong

Inbox messages exist because they haven't been read. Archiving them means the oracle will never read them — information is permanently lost in practice, even if the files still exist in `ψ/archive/`.

## Correct Response

1. Wake the oracle (manually if maw can't handle the inbox size)
2. Let the oracle read all pending messages
3. maw marks messages as `read: true` in frontmatter after drain
4. Future wakes skip already-read messages

## The Bug (maw-js)

`wake-inbox-drain.ts` has a 64KB byte budget but `sendWakeCommandAndPrompt()` inlines the entire prompt as a `-p '...'` argument via tmux send-keys. This exceeds shell/tmux limits for large inboxes. The fix belongs in maw-js (file-based prompt delivery), not in inbox cleanup.

## Rule

> If inbox is too large to wake, wake manually — don't shrink the inbox. Nothing unread gets archived.

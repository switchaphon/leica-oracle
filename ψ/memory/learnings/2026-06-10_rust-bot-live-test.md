# Lesson: Live testing a Discord bot — what catches you

**Date**: 2026-06-10
**Source**: Rust Discord bot live test session

## Pattern

Unit tests can cover parsing, chunking, and logic perfectly — but live Discord has config-layer failures that no test catches:

1. **Privileged intents must be toggled in Developer Portal** — MESSAGE_CONTENT intent (required to read message text) is off by default. Error 4014 at gateway connect.
2. **Bot must be invited to the server** with correct OAuth2 scopes (`bot` scope + Send Messages permission = 2048).
3. **Silent processes are undebuggable** — a bot with no logging looks identical whether it's working or broken. Always add stderr logging from day one.

## Applied

- Hit intent error on first run, fixed in Portal in 1 minute
- Added eprintln logging after the bot appeared to do nothing (it was actually working, just silent)
- Live test confirmed all 37 unit tests translated to real-world behavior correctly

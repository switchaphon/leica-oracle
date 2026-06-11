# Lesson: Fleet teaching scales linearly — 1 DNA × N threads

**Date**: 2026-06-10
**Source**: Codex workflow distribution to 11 oracles

## Pattern

When Leica learns something new from Un, the distribution workflow is:

1. **Learn once** — Un teaches Leica the concept (Codex workflow, BRIEF.md pattern)
2. **Practice** — Leica applies it (Rust Discord bot built with Codex)
3. **Distill to DNA** — Extract the reusable knowledge into a teaching message
4. **Distribute via threads** — Send to all oracle channels simultaneously
5. **Oracles read on wake** — Each reads thread when next active session starts

Cost: O(1) human effort, O(N) oracle coverage. No need to wake oracles — messages persist in threads.

## Evidence

- pops-clinic taught first (session 42d1da73, thread #5)
- Un said "ปล่อยให้ลองเอง" — waited before scaling
- Next session: distributed to remaining 10 oracles in 5 minutes
- Total: 11/11 oracles received Codex DNA

## Gap found

No "teaching registry" exists — had to dig JSONL to find who was taught. Should track: who learned what, when, from whom.

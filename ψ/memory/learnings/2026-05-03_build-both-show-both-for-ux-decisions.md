# Build both, show both — for UX design decisions

**Context**: User needed to choose between dropdown (Option C) and dialog (Option B) for diagnostic category picker. Text descriptions and ASCII art weren't convincing — user said "ดูเป็น text base ui แล้วดูยาก".

**Lesson**: When there's a UX fork with 2+ viable options:
1. Implement both options (even roughly) — took 30 minutes total
2. Wire them to different triggers so user can click both on the same page
3. Let embodied interaction (clicking, feeling weight) drive the decision
4. The user decided in seconds after clicking both — something hours of text spec couldn't achieve

**Connected pattern**: This also applies to Figma review — always look at actual designs (via figma-console bridge) before proposing layouts. Abstract specs miss visual intent.

**Anti-pattern**: Presenting options as text-based UI art and asking "which do you prefer?" — design decisions are visual, not textual.

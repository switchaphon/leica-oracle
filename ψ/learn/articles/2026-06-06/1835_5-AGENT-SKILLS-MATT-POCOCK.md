# 5 Agent Skills I Use Every Day — Matt Pocock

> Source: https://www.aihero.dev/5-agent-skills-i-use-every-day
> Author: Matt Pocock | Updated: 2026-03-16

## Core Idea

AI agents lack memory → need "extremely strict and well-defined processes" to produce quality work. Skills encode engineering workflows into repeatable commands.

## The 5 Skills

### 1. `/grill-me` — Flesh Out an Idea
Interview relentlessly about every aspect of a plan until shared understanding. Walk down each branch of the design tree.

- Only 3 sentences long but forces 16-50 clarifying questions
- Prevents premature planning
- **Takeaway:** Concise, well-chosen language at critical moments creates outsized impact

### 2. `/to-prd` — Conversation → Document
Transforms discussions into Product Requirements Documents (GitHub issues).

- Explores repo to verify claims
- Uses grill-me internally
- Writes user stories (Agile methodology)

### 3. `/to-issues` — PRD → Vertical Slices
Converts PRDs into independently grabbable GitHub issues.

- "Tracer bullet" approach — each issue is a complete vertical slice through all layers
- NOT horizontal single-layer tasks
- Establishes blocking relationships
- Enables parallel agent work

### 4. `/tdd` — Test-Driven Development
Red-green-refactor loops = "the most consistent way to improve agent outputs."

- Write tests first → implement → refactor
- Restructure shallow modules into deeper ones with thin interfaces
- Helps agents navigate codebases more effectively

### 5. `/improve-codebase-architecture` — Agent-Friendly Code
Identifies structural issues hindering agent productivity.

- Concepts spread across many small files
- Pure functions extracted solely for testability (real bugs hide elsewhere)
- Tightly coupled modules creating integration risk
- Run weekly or after development surges
- **"If you have a garbage code base, the AI will produce garbage within that code base."**

## Key Takeaways

1. **Process encodes expertise** — skills compensate for agent amnesia
2. **Quality demands structure** — clear module boundaries improve outputs
3. **Treat agents like engineers** — with constraints but human-centered workflows
4. **Vertical slices > horizontal layers** — complete user-facing features uncover unknowns faster

## Install

```bash
npx skills@latest add mattpocock/skills
```

## Bonus (not detailed in article)
- `/grill-with-docs` — grill against existing domain model
- `/domain-model` — domain modeling
- `/triage` — issue triage workflow

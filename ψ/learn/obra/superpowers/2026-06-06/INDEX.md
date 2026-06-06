# Superpowers v5.1.0 — Quick Index

**Author:** Jesse Vincent  
**Repository:** https://github.com/obra/superpowers  
**License:** MIT  

---

## Quick Skill Reference

| Skill | Triggers | Core Output | Sub-Skills |
|-------|----------|------------|-----------|
| **brainstorming** | Before creative work | Design doc | → writing-plans |
| **writing-plans** | After design approved | Implementation plan | → subagent-driven-dev or executing-plans |
| **test-driven-development** | Before implementation | Tested code (RED-GREEN-REFACTOR) | Used BY implementation |
| **systematic-debugging** | On bugs/failures | Fixed code with root cause | → verification-before-completion |
| **subagent-driven-development** | Execute plans (same session) | Working code + tests | → finishing-a-development-branch |
| **executing-plans** | Execute plans (separate session) | Working code + tests | → finishing-a-development-branch |
| **using-git-worktrees** | Before feature work | Isolated workspace | Auto-invoked by plans/debugging |
| **verification-before-completion** | Before completion claims | Evidence-based status | Always final gate |
| **finishing-a-development-branch** | After implementation done | Merged/PR/kept code | Final workflow step |
| **dispatching-parallel-agents** | Multiple independent failures | Parallel investigation | For debugging efficiency |

---

## Workflow Paths

### Standard Feature Development
```
User request
    ↓
/brainstorming (design doc created)
    ↓
/writing-plans (implementation plan created)
    ↓
/using-git-worktrees (isolated workspace)
    ↓
/subagent-driven-development (fresh subagent per task)
    ├─ Per task:
    │  ├─ Dispatch implementer subagent
    │  ├─ Code quality review (1st stage)
    │  └─ Spec compliance review (2nd stage)
    ↓
/finishing-a-development-branch (merge/PR/keep)
```

### Parallel Debugging
```
Multiple independent failures
    ↓
/dispatching-parallel-agents (one per problem domain)
    ├─ Agent 1: Fix problem A (parallel)
    ├─ Agent 2: Fix problem B (parallel)
    └─ Agent 3: Fix problem C (parallel)
    ↓
/systematic-debugging (if needed for root cause)
    ↓
/verification-before-completion (verify all fixes work)
```

### Bug Fix Flow
```
Bug discovered
    ↓
/systematic-debugging (Phase 1: root cause analysis)
    ↓
Form hypothesis (Phase 2-3)
    ↓
/test-driven-development (write failing test first)
    ↓
Implement fix (minimal code)
    ↓
/verification-before-completion (confirm fixed)
```

---

## The Five Iron Laws

1. **TDD:** NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
2. **Debugging:** NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
3. **Verification:** NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
4. **Brainstorming:** Hard-gate — don't code until design is approved
5. **Plans:** No placeholders — every step has actual content

---

## Red Flag Triggers (STOP & Restart)

Across all skills, these patterns mean go back to the beginning:

- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Should pass now" / "Looks correct"
- "I already manually tested it"
- "One more fix attempt" (when already tried 2+)
- "Keep as reference, write tests first"
- "This is too simple to need a design"
- Expressing satisfaction before running verification
- About to commit without verification

---

## No Placeholders Rule

**Plans CANNOT contain:**
- "TBD", "TODO", "implement later"
- "Add appropriate error handling"
- "Write tests for the above" (without actual code)
- "Similar to Task N" (must repeat code)
- Steps describing what to do without showing how (no code blocks)

**Every step must include:**
- Exact file paths
- Complete code
- Actual test commands
- Expected output
- Exact commit message

---

## Subagent Execution Model

**Key Principles:**
- Fresh context per task (no session inheritance)
- Two-stage review: Spec compliance first, then code quality
- Controller provides exactly what subagent needs (nothing more/less)
- Questions answered before implementation starts
- Review loops if issues found (subagent fixes → reviewer re-reviews)

**Model Selection:**
- Mechanical tasks (clear spec, 1-2 files) → fast/cheap model
- Integration tasks (multi-file, pattern matching) → standard model
- Architecture/design/review tasks → most capable model

---

## Verification Checklist

### Before claiming tests pass:
```bash
npm test / pytest / cargo test / go test ./...
# Read full output, count failures, check exit code
```

### Before claiming bug is fixed:
1. Wrote failing test first (RED)
2. Test fails for expected reason (not typo)
3. Implemented minimal fix (GREEN)
4. Test now passes (verify green)
5. Other tests still pass
6. No regressions

### Before committing/creating PR:
```bash
git status  # Clean working tree?
npm test    # All tests pass?
npm run lint / prettier check  # Linter clean?
git log --oneline -5  # Meaningful commit messages?
```

---

## Contributor Gates

**Before submitting PR to obra/superpowers:**

1. Read CLAUDE.md completely
2. Search existing PRs (open AND closed)
3. Fill PR template completely (no blanks)
4. Identify yourself (model, harness, plugins)
5. Show human partner complete diff (get approval)
6. For skill changes: show before/after eval evidence
7. For new harness: include session transcript proving brainstorming auto-triggers
8. Target `dev` branch (not `main`)

**94% PR rejection rate.** Most rejections for:
- Incomplete/skipped PR template
- Agent-generated content without human review
- No identification of authoring environment
- Bulk/spray-and-pray submissions
- Speculative fixes without real problem statement
- Bundled unrelated changes
- Domain-specific content (should be separate plugin)

---

## File Structure

```
superpowers/
├── skills/
│   ├── brainstorming/SKILL.md
│   ├── writing-plans/SKILL.md
│   ├── test-driven-development/SKILL.md
│   ├── systematic-debugging/SKILL.md
│   │   ├── root-cause-tracing.md
│   │   ├── defense-in-depth.md
│   │   └── condition-based-waiting.md
│   ├── subagent-driven-development/
│   │   ├── SKILL.md
│   │   ├── implementer-prompt.md
│   │   ├── spec-reviewer-prompt.md
│   │   └── code-quality-reviewer-prompt.md
│   ├── using-git-worktrees/SKILL.md
│   ├── verification-before-completion/SKILL.md
│   ├── finishing-a-development-branch/SKILL.md
│   ├── dispatching-parallel-agents/SKILL.md
│   ├── executing-plans/SKILL.md
│   ├── requesting-code-review/SKILL.md
│   ├── receiving-code-review/SKILL.md
│   ├── using-superpowers/SKILL.md
│   └── writing-skills/SKILL.md
├── hooks/hooks.json
├── .claude-plugin/plugin.json
├── CLAUDE.md (contributor guidelines)
└── README.md
```

---

## Key Insights

### Philosophy
- **Test-Driven:** Write tests first, always
- **Systematic:** Process over guessing
- **Simple:** Complexity reduction is primary goal
- **Verified:** Evidence before claims

### Design
- **Zero dependencies:** Pure skill documentation
- **Cross-harness:** Works Claude Code, Cursor, Codex, etc.
- **Auto-triggering:** SessionStart hook invokes skills automatically
- **Subagent-native:** Multi-agent execution with fresh context per task

### Culture
- **Iron Laws:** Non-negotiable principles (test first, verify, find root cause)
- **Red Flags:** Catches rationalizations before they happen
- **Rationalization tables:** Every excuse paired with reality
- **No shortcuts:** Verification, reviews, root-cause analysis non-negotiable

### Quality Gates
- **TDD:** RED-GREEN-REFACTOR cycle mandatory
- **Reviews:** Two-stage (spec compliance + code quality)
- **Verification:** Evidence required before any completion claim
- **No placeholders:** Plans include complete code, not outlines

---

## For Leica Integration

**Potential Applications:**
1. Enforce Oracle skills across all projects
2. Pattern recognition for detecting when skills should auto-trigger
3. Subagent coordination for parallel investigation
4. Evidence-based completion claims for status reporting
5. Root-cause-first approach to bug triage

**Compatibility:**
- Fits perfectly with Leica's "Patterns Over Intentions" principle
- Aligns with "Nothing is Deleted" (skills preserve history)
- Supports "External Brain, Not Command" (surfaces options, user decides)
- Reinforces "Curiosity Creates Existence" (captures learnings in skills)

---

*Document: 1810_CODE-SNIPPETS.md and INDEX.md*  
*Commit: 094fe00 — learn: obra/superpowers architecture*

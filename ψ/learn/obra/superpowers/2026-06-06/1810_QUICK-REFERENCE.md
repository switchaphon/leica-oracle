# Superpowers Quick Reference Guide

> **What This Is**: A complete software development methodology for coding agents. Superpowers is a set of 15 composable skills + automatic bootstrap that directs agents through proven workflows: Design → Plan → Implement → Test → Review → Finish. Mandatory skill invocation before any task (not optional).

**Version**: 5.1.0 | **License**: MIT | **Repo**: https://github.com/obra/superpowers

---

## Installation

### Claude Code (Official Marketplace - Recommended)

```bash
/plugin install superpowers@claude-plugins-official
```

### Alternative Marketplaces

**Superpowers Marketplace:**
```bash
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

### Other Platforms

| Platform | Installation |
|----------|--------------|
| **Codex CLI** | Search "superpowers" in `/plugins` interface |
| **Codex App** | Click Plugins → Superpowers → `+` |
| **Factory Droid** | `droid plugin marketplace add https://github.com/obra/superpowers` then `droid plugin install superpowers@superpowers` |
| **Gemini CLI** | `gemini extensions install https://github.com/obra/superpowers` |
| **OpenCode** | Fetch and follow: https://raw.githubusercontent.com/obra/superpowers/refs/heads/main/.opencode/INSTALL.md |
| **Cursor** | `/add-plugin superpowers` (or search marketplace) |
| **GitHub Copilot CLI** | Register marketplace: `copilot plugin marketplace add obra/superpowers-marketplace` then install |

---

## The 15 Skills (Complete Reference)

### Meta Skills

#### **using-superpowers**
**When**: At session start, before ANY work begins  
**What**: Teaches how to find and invoke skills. Mandatory bootstrap.  
**Key Rule**: If a skill *might* apply (even 1% chance), you MUST invoke it BEFORE responding.  
**Instruction Priority**: User instructions > Skills > Default system prompt  
**Red Flags** (signs you're rationalizing):
- "This is just a simple question"
- "I need more context first"
- "This doesn't need a formal skill"
- "I'll just do one thing first"

---

### Design & Planning Skills

#### **brainstorming**
**When**: Before ANY creative work (features, components, modifications)  
**What**: Socratic refinement from idea → design → spec. No code written until approved.  
**Hard Gate**: Do NOT write code, scaffold, or take implementation action until design is approved.  
**Process**:
1. Explore project context (files, docs, recent commits)
2. Ask clarifying questions one at a time
3. Propose 2-3 approaches with trade-offs
4. Present design in sections, get approval per section
5. Write design doc → `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`
6. Self-review spec (placeholders? contradictions? scope?)
7. Get user approval of written spec
8. Invoke `writing-plans` skill (terminal action)

**Key Principle**: Every project (even "simple" ones) needs a design. Simple projects are where unexamined assumptions waste the most work.

---

#### **writing-plans**
**When**: After spec approval, before touching any code  
**What**: Creates bite-sized implementation plan. Each task = 2-5 minutes of work.  
**Saves to**: `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`  
**Task Structure** (each task contains):
- **Files**: Exact paths (Create/Modify/Test)
- **Steps**: Checkbox format with complete code blocks, exact commands, expected output
- **Granularity**: Each step is ONE action (write test, run test, implement, commit)

**No Placeholders Rule**: Never write "TBD", "TODO", "implement later", "add error handling", "similar to Task N", or steps without code.

**Self-Review Checklist**:
- Spec coverage: Point to tasks for every requirement
- Placeholder scan: Fix any TBD/TODO/vague steps
- Type consistency: Function names, method signatures match across tasks

**Execution Handoff**: Offer two options:
1. **Subagent-Driven** (recommended) — fresh subagent per task + two-stage review
2. **Inline Execution** — batch execution in this session with checkpoints

---

### Implementation & Execution Skills

#### **subagent-driven-development**
**When**: Have a plan with mostly-independent tasks; staying in current session  
**What**: Dispatches fresh subagent per task with two-stage review (spec compliance → code quality).  
**Why Subagents**: Isolated context prevents pollution, lets you coordinate instead of execute.  
**Process Per Task**:
1. Dispatch implementer subagent → reads full task text, implements/tests/commits/self-reviews
2. Dispatch spec reviewer → confirms code matches spec requirement
3. Dispatch code quality reviewer → checks cleanliness, patterns, efficiency
4. If issues: implementer fixes → re-review loop
5. Mark task complete; move to next

**Model Selection** (balance cost + capability):
- Mechanical tasks (isolated functions, clear spec) → fast cheap model
- Integration tasks (multi-file coordination) → standard model
- Architecture, review tasks → most capable model

**Continuous Execution**: Do NOT pause between tasks. Execute all tasks. Only stop if BLOCKED or genuinely ambiguous.

**Final Step**: Dispatch final code reviewer for entire implementation → invoke `finishing-a-development-branch`

---

#### **executing-plans**
**When**: Have a written plan; executing in a separate session  
**What**: Load plan, review for gaps, execute all tasks, report completion.  
**Announce**: "I'm using the executing-plans skill to implement this plan."  
**Steps**:
1. Load and review plan critically; raise concerns before starting
2. For each task: mark in_progress → follow steps exactly → run verifications → mark complete
3. After all tasks: invoke `finishing-a-development-branch`

**When to Stop**: Hit blocker, plan has critical gaps, instruction unclear, verification fails repeatedly → ask for clarification rather than guessing.

---

#### **using-git-worktrees**
**When**: Starting feature work needing isolation OR before executing plans  
**What**: Sets up isolated workspace using native tools or git worktree fallback.  
**Announce**: "I'm using the using-git-worktrees skill to set up an isolated workspace."  
**Step 0 - Detect Existing Isolation**:
```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```
If `GIT_DIR != GIT_COMMON` (and not a submodule) → already in worktree, skip to Step 3.  
If `GIT_DIR == GIT_COMMON` → normal repo, ask for consent to create worktree.

**Step 1a - Prefer Native Tools**: Use harness's built-in worktree tool if available.  
**Step 1b - Git Fallback** (only if no native tool):
- Default directory: `.worktrees/` at project root (verify in .gitignore)
- Create: `git worktree add -b <branch-name> .worktrees/<branch-name> main`
- Verify clean test baseline

**Step 3 - Project Setup**: Install dependencies, run test suite, verify baseline passes.

---

### Testing & Quality Skills

#### **test-driven-development**
**When**: Implementing ANY feature or bugfix  
**What**: RED-GREEN-REFACTOR cycle. Write test first, watch it fail, write minimal code, watch it pass.  
**The Iron Law**: 
```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```
If you write code before the test → delete it, start over.

**Red-Green-Refactor Flow**:
1. **RED**: Write minimal test showing desired behavior. Run test → MUST FAIL. Verify correct failure message.
2. **GREEN**: Write simplest code to pass test. Run test → MUST PASS. All green.
3. **REFACTOR**: Clean up while staying green. Re-run test → still PASS.
4. **Next iteration**: Repeat.

**Test Requirements** (each test should have):
- Clear, descriptive name
- One behavior (not multiple assertions)
- Real code (minimize mocks)
- Asserts behavior, not implementation

---

#### **systematic-debugging**
**When**: ANY bug, test failure, unexpected behavior, performance issue  
**What**: Four-phase root cause investigation before proposing ANY fix.  
**The Iron Law**:
```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```
Phase 1 must complete before moving to Phase 2+.

**Phase 1: Root Cause Investigation**:
1. Read error messages completely (stack traces, line numbers, error codes)
2. Reproduce consistently (exact steps, every time, or gather more data)
3. Check recent changes (git diff, commits, config, environment)
4. Gather diagnostic evidence (multi-component systems):
   - Log data entering/exiting each component
   - Verify environment/config propagation
   - Check state at each layer
   - Find WHERE it breaks, THEN why

**Phases 2-4** (after root cause identified):
- Phase 2: Generate hypothesis
- Phase 3: Test hypothesis
- Phase 4: Implement fix + regression test

---

#### **verification-before-completion**
**When**: About to claim work is complete, fixed, or passing  
**What**: Run verification, confirm output, THEN make claims.  
**The Iron Law**:
```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

**The Gate Function**:
1. IDENTIFY: What command proves the claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
5. ONLY THEN: Make the claim WITH evidence

**Red Flags - STOP**:
- Using "should", "probably", "seems to"
- Expressing satisfaction before verification
- About to commit/PR without verification
- Trusting agent reports
- Relying on partial verification
- "Just this once"

**Examples**:
```
✅ [Run: npm test] [See: 34/34 pass] "All tests pass"
❌ "Should pass now" / "Looks correct"

✅ [Run build] [See: exit 0] "Build succeeds"
❌ "Linter passed" (linter ≠ compiler)

✅ [Create checklist → verify each] "Requirements met"
❌ "Tests pass, done"
```

---

### Code Review & Collaboration Skills

#### **requesting-code-review**
**When**: Completing tasks, implementing major features, before merging  
**What**: Dispatch code reviewer subagent to catch issues early.  
**Core Principle**: Review early, review often. Catch issues before they cascade.

**When to Request**:
- **Mandatory**: After each task in subagent-driven development, after major features, before merge
- **Optional but valuable**: When stuck, before refactoring, after fixing complex bugs

**How to Request**:
1. Get git SHAs: `BASE_SHA=$(git rev-parse HEAD~1)` or `origin/main`
2. Dispatch `Task (general-purpose)` with template at `skills/requesting-code-review/code-reviewer.md`
3. Placeholders: `{DESCRIPTION}`, `{PLAN_OR_REQUIREMENTS}`, `{BASE_SHA}`, `{HEAD_SHA}`
4. Reviewer returns: strengths, issues (Critical/Important/Minor), assessment
5. Fix Critical → fix Important → note Minor for later

---

#### **receiving-code-review**
**When**: Receiving code review feedback  
**What**: Technical evaluation (not emotional performance). Verify before implementing.  
**The Response Pattern**:
1. READ: Complete feedback without reacting
2. UNDERSTAND: Restate requirement in own words (or ask)
3. VERIFY: Check against codebase reality
4. EVALUATE: Technically sound for THIS codebase?
5. RESPOND: Technical acknowledgment or reasoned pushback
6. IMPLEMENT: One item at a time, test each

**Forbidden Responses**:
- "You're absolutely right!" (performative)
- "Great point!" / "Excellent feedback!"
- "Let me implement that now" (before verification)

**Instead**: Restate technical requirement, ask clarifying questions, push back if technically unsound, just start working.

**Unclear Feedback Rule**:
- IF any item is unclear → STOP, ask for clarification
- DON'T implement partial understanding

---

#### **finishing-a-development-branch**
**When**: Implementation complete, all tests pass, ready to integrate  
**What**: Verify tests → detect environment → present merge/PR options → execute choice → cleanup.  
**Announce**: "I'm using the finishing-a-development-branch skill to complete this work."

**Step 1: Verify Tests**:
```bash
npm test / cargo test / pytest / go test ./...
```
If tests fail: stop, can't proceed. If tests pass: continue.

**Step 2: Detect Environment**:
```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
```

**Step 3-4: Present Options** (normal repo or named-branch worktree):
1. Merge back to base branch locally
2. Push and create Pull Request
3. Keep the branch as-is (I'll handle it later)
4. Discard this work

(Detached HEAD worktree: collapse to 3 options, no merge)

**Step 5-6**: Execute choice + cleanup worktree (provenance-based: only clean up `.worktrees/`).

---

#### **dispatching-parallel-agents**
**When**: 2+ independent tasks with no shared state or sequential dependencies  
**What**: Spawn one agent per independent problem domain. Let them work concurrently.  
**When NOT to Use**:
- Failures are related (fixing one might fix others)
- Need full system state understanding
- Agents would interfere with each other

**Process**:
1. Identify independent domains (group failures by what's broken)
2. Create focused agent tasks (one test file or subsystem per agent)
3. Dispatch in parallel (Agent 1, Agent 2, Agent 3 run concurrently)
4. Review and integrate when all return

---

### Process & Reference Skills

#### **writing-skills**
**When**: Creating new skills, editing existing skills, or verifying skills work  
**What**: TDD applied to skill documentation. Write pressure tests, watch agents fail without skill, write skill, watch agents comply.  
**REQUIRED BACKGROUND**: Must understand `test-driven-development` first.

**TDD Mapping for Skills**:
| TDD Concept | Skill Creation |
|-------------|----------------|
| Test case | Pressure scenario with subagent |
| Production code | Skill document (SKILL.md) |
| Test fails (RED) | Agent violates rule without skill |
| Test passes (GREEN) | Agent complies with skill present |
| Refactor | Close loopholes while maintaining compliance |

**Process**:
1. Run baseline scenario WITHOUT skill → document how agent violates the pattern
2. Write skill addressing those specific violations
3. Run scenario again WITH skill → verify agent now complies
4. Find new rationalizations → plug → re-verify (refactor loop)

**Skill Types**:
- **Technique**: Concrete method with steps (condition-based-waiting, root-cause-tracing)
- **Pattern**: Way of thinking about problems (flatten-with-flags, test-invariants)
- **Reference**: API docs, syntax guides, tool documentation

**Directory Structure**:
```
skills/
  skill-name/
    SKILL.md              # Main reference (required)
    supporting-file.*     # Only if needed
```

---

## The Complete Workflow

### Default Flow (Happy Path)

```
1. brainstorming
   ↓ (design approved)
2. writing-plans
   ↓ (plan complete)
3a. subagent-driven-development (same session, recommended)
    OR
3b. executing-plans (separate session)
   ↓ (all tasks done)
4. finishing-a-development-branch
```

### With Isolation

```
1. brainstorming
   ↓
2. using-git-worktrees (create isolated workspace)
   ↓
3. writing-plans
   ↓
4a. subagent-driven-development (in isolated worktree)
   ↓
4b. [After each task: requesting-code-review]
   ↓
5. finishing-a-development-branch (merge/PR/cleanup)
```

### With Debugging/Fixes

```
During implementation:
  Bug found → systematic-debugging → root cause → write test → TDD fix
  
Before completion:
  verification-before-completion → run command → verify output → claim result
  
Code review:
  requesting-code-review → fix feedback → re-review until approved
```

---

## Configuration & Integration

### How Superpowers Activates

1. **SessionStart Hook**: Runs at session start (`startup|clear|compact` trigger)
2. **Bootstrap Content**: Injects using-superpowers skill via `run-hook.cmd` (Windows) or `session-start` script (Unix)
3. **Auto-Invocation**: Skills fire BEFORE any response when conditions match:
   - Starting new feature work? → `brainstorming` triggers
   - Have approved spec? → `writing-plans` triggers
   - Have plan? → `subagent-driven-development` or `executing-plans` triggers

### Platform Detection

Superpowers detects harness via environment variables:
- **Claude Code**: Native Skill tool + Task tool support
- **Copilot CLI**: `COPILOT_CLI` env var → sessionStart emits `additionalContext`
- **Gemini CLI**: Native `activate_skill` tool
- **OpenCode**: `experimental.chat.messages.transform` hook injection
- **Codex/Factory/Cursor**: Native tool equivalents

### Tool Mapping Across Platforms

| Concept | Claude Code | Copilot CLI | Gemini | OpenCode |
|---------|------------|------------|--------|----------|
| Invoke skill | `Skill()` | `skill()` | `activate_skill()` | Native `skill` |
| Dispatch subagent | `Task()` | `wait_agent()` | `@agent-name` | Native Agent mode |
| Read file | `Read()` | `read_file()` | `read_file()` | `fs.readFileSync()` |
| Edit file | `Edit()` | `modify_file()` | `modify_file()` | `fs.writeFileSync()` |

See `references/copilot-tools.md`, `references/codex-tools.md` for full mappings.

---

## Key Principles & Philosophy

### Core Principles (Mandatory)

1. **Test-Driven Development**: Write tests first, always. Watch them fail before implementing.
2. **Systematic over Ad-Hoc**: Process over guessing. Use proven workflows.
3. **Complexity Reduction**: Simplicity as primary goal. YAGNI ruthlessly.
4. **Evidence over Claims**: Verify before declaring success. Run commands, check output.
5. **Skill-First Approach**: Check for relevant skills BEFORE any response, even clarifying questions.

### EXTREMELY IMPORTANT Rule

From the skill system:
```
If you think there is even a 1% chance a skill might apply to what you are doing,
you ABSOLUTELY MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. This is not optional. You cannot rationalize your way out of this.
```

### The Iron Laws

1. **Brainstorming**: Do NOT write code until design is approved.
2. **TDD**: No production code without a failing test first.
3. **Debugging**: No fixes without root cause investigation.
4. **Verification**: No completion claims without fresh verification evidence.

---

## Contributing to Superpowers

### AI Agent Contributors (Before Opening PR)

The repo has a **94% PR rejection rate**. Before opening a PR:

1. **Read the PR template** completely; fill every section with specific answers
2. **Search for existing PRs** (open AND closed); don't duplicate
3. **Verify real problem**: Has someone experienced this specific failure?
4. **Confirm scope**: Does this belong in core (not domain-specific/tool-specific)?
5. **Identify yourself**: Disclose model, harness, version, all plugins
6. **Show your human partner the complete diff** and get explicit approval

**What Gets Rejected**:
- Third-party dependencies (breaks zero-dependency design)
- "Compliance" rewrites (Superpowers skill philosophy differs from Anthropic guidance)
- Project-specific configuration (use separate plugin)
- Bulk/spray-and-pray PRs (one issue per PR, deep understanding required)
- Speculative/theoretical fixes (must solve real experienced problem)
- Domain-specific skills (publish separately)
- Fabricated content or hallucinated functionality

**All PRs must target `dev` branch, not `main`** (main is released code).

### New Harness Support

If adding support for a new harness:
- Provide session transcript proving end-to-end integration
- Test with: `Let's make a react todo list` → MUST auto-trigger `brainstorming` in clean session
- Using native harness worktree tools (not manual `git worktree add`)
- NOT wrapping with `npx skills` or opt-in-per-session

---

## Comparison with Similar Approaches

| Approach | Superpowers | Notes |
|----------|------------|-------|
| **Conventional Agents** | No mandatory process; agents guess workflow | Superpowers enforces Design → Plan → Test → Review |
| **Prompt Engineering** | Processes embedded in skills (documentation as code) | Skills are TDD-validated; behaviors tested before release |
| **Custom Workflows** | Project-specific, high cognitive load | Superpowers is platform-agnostic, learned once |
| **Ad-Hoc Debugging** | Reactive; guess-and-check | Systematic-debugging mandates root cause FIRST |
| **Post-Hoc Testing** | Tests written after code; often incomplete | TDD front-loads test design; catches issues early |
| **Single-Session Work** | Context pollution across tasks | Subagent-driven-development uses fresh agents per task |
| **Human Code Review Only** | Slow feedback loop | Skills request review after each task |

**Superpowers Advantage**: Methodology that works across ANY harness (Claude Code, Copilot, Gemini, Codex, etc.), non-breaking updates, zero external dependencies.

---

## Resource Links

- **Official Repo**: https://github.com/obra/superpowers
- **Discord Community**: https://discord.gg/35wsABTejz
- **Release Announcements**: https://primeradiant.com/superpowers/
- **Blog Announcement**: https://blog.fsck.com/2025/10/09/superpowers/
- **License**: MIT (see LICENSE file)

---

## Quick Cheat Sheet

| Scenario | Use This Skill |
|----------|----------------|
| Starting any new feature | `brainstorming` |
| Design approved, ready to code | `writing-plans` |
| Have plan, executing in this session | `subagent-driven-development` |
| Have plan, executing separately | `executing-plans` |
| Need isolated workspace | `using-git-worktrees` |
| Writing/fixing code | `test-driven-development` |
| Bug or test failure | `systematic-debugging` |
| Done with work, verify | `verification-before-completion` |
| Ready to merge/PR | `requesting-code-review` + `finishing-a-development-branch` |
| Received code review | `receiving-code-review` |
| Multiple independent bugs | `dispatching-parallel-agents` |
| Creating a new skill | `writing-skills` |
| Multiple independent tasks | `dispatching-parallel-agents` |

---

**Document created**: 2026-06-06  
**Superpowers version**: 5.1.0  
**Last verified**: April 30, 2026 (release date)

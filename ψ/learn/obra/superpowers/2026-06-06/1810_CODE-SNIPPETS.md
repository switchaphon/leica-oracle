# Superpowers: Code Snippets & Architecture

**Source:** `/Users/switchaphon/ghq/github.com/obra/superpowers/`  
**Version:** 5.1.0  
**Author:** Jesse Vincent  
**Date:** 2026-06-06  

---

## I. Plugin Manifests & Configuration

### Claude Plugin Definition

**File:** `.claude-plugin/plugin.json`

```json
{
  "name": "superpowers",
  "description": "Core skills library for Claude Code: TDD, debugging, collaboration patterns, and proven techniques",
  "version": "5.1.0",
  "author": {
    "name": "Jesse Vincent",
    "email": "jesse@fsck.com"
  },
  "homepage": "https://github.com/obra/superpowers",
  "repository": "https://github.com/obra/superpowers",
  "license": "MIT",
  "keywords": [
    "skills",
    "tdd",
    "debugging",
    "collaboration",
    "best-practices",
    "workflows"
  ]
}
```

### Marketplace Configuration

**File:** `.claude-plugin/marketplace.json`

```json
{
  "name": "superpowers-dev",
  "description": "Development marketplace for Superpowers core skills library",
  "owner": {
    "name": "Jesse Vincent",
    "email": "jesse@fsck.com"
  },
  "plugins": [
    {
      "name": "superpowers",
      "description": "Core skills library for Claude Code: TDD, debugging, collaboration patterns, and proven techniques",
      "version": "5.1.0",
      "source": "./",
      "author": {
        "name": "Jesse Vincent",
        "email": "jesse@fsck.com"
      }
    }
  ]
}
```

### Hook Configuration

**File:** `hooks/hooks.json`

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd\" session-start",
            "async": false
          }
        ]
      }
    ]
  }
}
```

---

## II. Core Skill Frontmatter Patterns

All skills follow YAML frontmatter + Markdown structure:

```markdown
---
name: skill-name-with-hyphens
description: Use when [specific triggering conditions and symptoms]
---

# Skill Name

## Overview
[What is this? Core principle in 1-2 sentences]

## When to Use
[Bullet list with SYMPTOMS and use cases]

## The Process / Core Pattern
[Main workflow or technique]

## Red Flags - STOP
[When to halt and restart process]

## Common Rationalizations
[Table: Excuse → Reality]

## Quick Reference
[Scanning reference]
```

---

## III. Skill Inventory & Definitions

### 1. Brainstorming

**Name:** `brainstorming`  
**Description:** You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation.

**Key Pattern:**
- Explore project context → Ask clarifying questions (one at a time) → Propose 2-3 approaches → Present design sections → Get approval → Write design doc → Spec self-review → User review → Invoke writing-plans

**Hard Gate:**
```
Do NOT invoke any implementation skill, write any code, scaffold any project, 
or take any implementation action until you have presented a design and the 
user has approved it. This applies to EVERY project regardless of perceived 
simplicity.
```

**Design Document Location:**
```
docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md
```

---

### 2. Writing Plans

**Name:** `writing-plans`  
**Description:** Use when you have a spec or requirements for a multi-step task, before touching code

**Core Principle:** Assume engineer has zero context. DRY. YAGNI. TDD. Frequent commits.

**Plan Document Header (REQUIRED):**
```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development 
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. 
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

**Task Structure Template:**
```markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
```

**Save Location:**
```
docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md
```

**Plan Failures (Never Write):**
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code)
- Steps without showing how (code blocks required for code steps)

---

### 3. Test-Driven Development (TDD)

**Name:** `test-driven-development`  
**Description:** Use when implementing any feature or bugfix, before writing implementation code

**Iron Law:**
```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

**Red-Green-Refactor Cycle:**

```
RED → Verify RED → GREEN → Verify GREEN → REFACTOR → Repeat
```

**RED Phase - Write Failing Test:**
```typescript
test('retries failed operations 3 times', async () => {
  let attempts = 0;
  const operation = () => {
    attempts++;
    if (attempts < 3) throw new Error('fail');
    return 'success';
  };

  const result = await retryOperation(operation);

  expect(result).toBe('success');
  expect(attempts).toBe(3);
});
```

**Test Requirements:**
- One behavior
- Clear name
- Real code (no mocks unless unavoidable)

**Verify RED (MANDATORY):**
```bash
npm test path/to/test.test.ts
# Confirm: Test fails, failure message is expected, fails because feature missing
```

**GREEN Phase - Minimal Code:**
```typescript
async function retryOperation<T>(fn: () => Promise<T>): Promise<T> {
  for (let i = 0; i < 3; i++) {
    try {
      return await fn();
    } catch (e) {
      if (i === 2) throw e;
    }
  }
  throw new Error('unreachable');
}
```

**Verify GREEN (MANDATORY):**
```bash
npm test path/to/test.test.ts
# Confirm: Test passes, other tests still pass, output pristine
```

**REFACTOR Phase:**
- Remove duplication
- Improve names
- Extract helpers
- Keep tests green, don't add behavior

**Verification Checklist:**
- [ ] Every new function/method has a test
- [ ] Watched each test fail before implementing
- [ ] Each test failed for expected reason (feature missing, not typo)
- [ ] Wrote minimal code to pass each test
- [ ] All tests pass
- [ ] Output pristine (no errors, warnings)
- [ ] Tests use real code (mocks only if unavoidable)
- [ ] Edge cases and errors covered

---

### 4. Systematic Debugging

**Name:** `systematic-debugging`  
**Description:** Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes

**Iron Law:**
```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

**The Four Phases:**

#### Phase 1: Root Cause Investigation

1. **Read Error Messages Carefully**
   - Don't skip past errors or warnings
   - Note line numbers, file paths, error codes

2. **Reproduce Consistently**
   - Can you trigger it reliably?
   - What are the exact steps?
   - Does it happen every time?

3. **Check Recent Changes**
   - What changed that could cause this?
   - Git diff, recent commits
   - New dependencies, config changes

4. **Gather Evidence (Multi-Component Systems)**
   ```bash
   # Layer 1: Workflow
   echo "=== Secrets available in workflow: ==="
   echo "IDENTITY: ${IDENTITY:+SET}${IDENTITY:-UNSET}"

   # Layer 2: Build script
   echo "=== Env vars in build script: ==="
   env | grep IDENTITY || echo "IDENTITY not in environment"

   # Layer 3: Signing script
   echo "=== Keychain state: ==="
   security list-keychains
   security find-identity -v

   # Layer 4: Actual signing
   codesign --sign "$IDENTITY" --verbose=4 "$APP"
   ```

5. **Trace Data Flow** (see `root-cause-tracing.md`)

#### Phase 2: Pattern Analysis

1. **Find Working Examples**
2. **Compare Against References**
3. **Identify Differences**
4. **Understand Dependencies**

#### Phase 3: Hypothesis and Testing

1. **Form Single Hypothesis** - "I think X is the root cause because Y"
2. **Test Minimally** - Smallest possible change
3. **Verify Before Continuing** - One variable at a time
4. **When You Don't Know** - Say it, don't pretend

#### Phase 4: Implementation

1. **Create Failing Test Case**
2. **Implement Single Fix**
3. **Verify Fix**
4. **If Fix Doesn't Work:**
   - Count how many fixes: < 3 → Return to Phase 1
   - ≥ 3 → Question the architecture

5. **If 3+ Fixes Failed: Question Architecture**
   - Pattern indicates architectural problem
   - STOP and question fundamentals

**Red Flags - STOP and Follow Process:**
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "One more fix attempt" (when already tried 2+)
- Each fix reveals new problem in different place

---

### 5. Subagent-Driven Development

**Name:** `subagent-driven-development`  
**Description:** Use when executing implementation plans with independent tasks in the current session

**Core Principle:** Fresh subagent per task + two-stage review (spec compliance, then code quality) = high quality, fast iteration

**Process Flow:**
```
Read plan → Extract all tasks → Create TodoWrite
    ↓
Per Task:
  Dispatch implementer → Questions? → Answer & redispatch
    ↓
  Implementer implements, tests, commits, self-reviews
    ↓
  Dispatch spec reviewer → Issues? → Implementer fixes → Spec reviewer re-reviews
    ↓
  Dispatch code quality reviewer → Issues? → Implementer fixes → Code reviewer re-reviews
    ↓
  Mark task complete
    ↓
More tasks? → Loop or proceed to final review
    ↓
Dispatch final code reviewer
    ↓
Use finishing-a-development-branch skill
```

**Implementer Status Handling:**

| Status | Action |
|--------|--------|
| DONE | Proceed to spec compliance review |
| DONE_WITH_CONCERNS | Read concerns, address if needed, proceed to review |
| NEEDS_CONTEXT | Provide missing info and re-dispatch |
| BLOCKED | Assess blocker: context → provide & redispatch; reasoning → more capable model; task too large → break up; plan wrong → escalate |

**Model Selection Strategy:**

- **Mechanical implementation** (isolated functions, clear specs, 1-2 files) → fast, cheap model
- **Integration and judgment** (multi-file coordination, pattern matching, debugging) → standard model
- **Architecture, design, review** → most capable model

**Key Requirements:**
- Fresh context per task (no session inheritance)
- Two-stage review: spec compliance first, then code quality
- Review loops: if issues found, implementer fixes and reviewer re-reviews
- Don't skip reviews or move to next task with open issues

---

### 6. Using Git Worktrees

**Name:** `using-git-worktrees`  
**Description:** Use when starting feature work that needs isolation from current workspace or before executing implementation plans

**Core Principle:** Detect existing isolation first → Use native tools → Fall back to git

**Step 0: Detect Existing Isolation**

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)

# Submodule guard
git rev-parse --show-superproject-working-tree 2>/dev/null
```

**If `GIT_DIR != GIT_COMMON` (not a submodule):** Already in linked worktree → Skip creation

**If `GIT_DIR == GIT_COMMON`:** In normal repo → Ask for consent or use declared preference

**Step 1a: Native Worktree Tools (Preferred)**

Use if available (e.g., `EnterWorktree`, `WorktreeCreate`, `/worktree` command, `--worktree` flag)

**Step 1b: Git Worktree Fallback**

Only if no native tool available.

**Directory Priority:**
1. Check instruction file for declared preference
2. Check for existing `.worktrees/` or `worktrees/`
3. Check for global legacy: `~/.config/superpowers/worktrees/$project`
4. Default to `.worktrees/` at project root

**Safety Verification (project-local only):**
```bash
git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
# If NOT ignored: Add to .gitignore, commit, then proceed
```

**Create Worktree:**
```bash
project=$(basename "$(git rev-parse --show-toplevel)")
git worktree add "$path" -b "$BRANCH_NAME"
cd "$path"
```

**Step 3: Project Setup**

```bash
# Node.js
if [ -f package.json ]; then npm install; fi

# Rust
if [ -f Cargo.toml ]; then cargo build; fi

# Python
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f pyproject.toml ]; then poetry install; fi

# Go
if [ -f go.mod ]; then go mod download; fi
```

**Step 4: Verify Clean Baseline**

```bash
# Use project-appropriate command
npm test / cargo test / pytest / go test ./...
```

**Report:**
```
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

---

### 7. Verification Before Completion

**Name:** `verification-before-completion`  
**Description:** Use when about to claim work is complete, fixed, or passing, before committing or creating PRs

**Core Principle:** Evidence before claims, always

**Iron Law:**
```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

**The Gate Function:**
```
BEFORE claiming any status:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim
```

**Common Failures:**

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |

**Red Flags - STOP:**
- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!")
- About to commit/push/PR without verification
- Trusting agent success reports
- Relying on partial verification
- ANY wording implying success without running verification

---

### 8. Finishing a Development Branch

**Name:** `finishing-a-development-branch`  
**Description:** Use when implementation is complete, all tests pass, and you need to decide how to integrate the work

**Core Principle:** Verify tests → Detect environment → Present options → Execute choice → Clean up

**Step 1: Verify Tests**

```bash
npm test / cargo test / pytest / go test ./...
```

If tests fail: Report failures and stop. Cannot proceed until tests pass.

**Step 2: Detect Environment**

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
```

| State | Menu | Cleanup |
|-------|------|---------|
| `GIT_DIR == GIT_COMMON` (normal repo) | Standard 4 options | No worktree to clean up |
| `GIT_DIR != GIT_COMMON`, named branch | Standard 4 options | Provenance-based |
| `GIT_DIR != GIT_COMMON`, detached HEAD | Reduced 3 options | No cleanup (externally managed) |

**Step 3: Determine Base Branch**

```bash
git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null
```

**Step 4: Present Options**

**Normal repo or named-branch worktree:**
```
Implementation complete. What would you like to do?

1. Merge back to <base-branch> locally
2. Push and create a Pull Request
3. Keep the branch as-is (I'll handle it later)
4. Discard this work

Which option?
```

**Detached HEAD:**
```
Implementation complete. You're on a detached HEAD (externally managed workspace).

1. Push as new branch and create a Pull Request
2. Keep as-is (I'll handle it later)
3. Discard this work

Which option?
```

---

### 9. Dispatching Parallel Agents

**Name:** `dispatching-parallel-agents`  
**Description:** Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies

**Core Principle:** Dispatch one agent per independent problem domain

**Agent Prompt Structure:**
```markdown
Fix the 3 failing tests in src/agents/agent-tool-abort.test.ts:

1. "should abort tool with partial output capture" - expects 'interrupted at' in message
2. "should handle mixed completed and aborted tools" - fast tool aborted instead of completed
3. "should properly track pendingToolCount" - expects 3 results but gets 0

These are timing/race condition issues. Your task:

1. Read the test file and understand what each test verifies
2. Identify root cause - timing issues or actual bugs?
3. Fix by:
   - Replacing arbitrary timeouts with event-based waiting
   - Fixing bugs in abort implementation if found
   - Adjusting test expectations if testing changed behavior

Do NOT just increase timeouts - find the real issue.

Return: Summary of what you found and what you fixed.
```

**Use When:**
- 3+ test files failing with different root causes
- Multiple subsystems broken independently
- Each problem can be understood without context from others
- No shared state between investigations

**Don't Use When:**
- Failures are related (fix one might fix others)
- Need to understand full system state
- Agents would interfere with each other

---

### 10. Executing Plans

**Name:** `executing-plans`  
**Description:** Use when you have a written implementation plan to execute in a separate session with review checkpoints

**Process:**
1. Load and review plan critically
2. Create TodoWrite
3. Execute each task exactly as specified
4. Mark completed
5. When all tasks done: Use finishing-a-development-branch skill

**When to Stop and Ask for Help:**
- Hit a blocker (missing dependency, test fails, unclear instruction)
- Plan has critical gaps
- Don't understand an instruction
- Verification fails repeatedly

---

## IV. Writing Skills Framework

**File:** `skills/writing-skills/SKILL.md`

**Core Principle:** Writing skills IS Test-Driven Development applied to process documentation

**TDD Mapping for Skills:**

| TDD Concept | Skill Creation |
|-------------|----------------|
| Test case | Pressure scenario with subagent |
| Production code | Skill document (SKILL.md) |
| Test fails (RED) | Agent violates rule without skill (baseline) |
| Test passes (GREEN) | Agent complies with skill present |
| Refactor | Close loopholes while maintaining compliance |

**SKILL.md Structure:**

```markdown
---
name: Skill-Name-With-Hyphens
description: Use when [specific triggering conditions and symptoms]
---

# Skill Name

## Overview
What is this? Core principle in 1-2 sentences.

## When to Use
[Small inline flowchart IF decision non-obvious]

Bullet list with SYMPTOMS and use cases
When NOT to use

## Core Pattern (for techniques/patterns)
Before/after code comparison

## Quick Reference
Table or bullets for scanning common operations

## Implementation
Inline code for simple patterns
Link to file for heavy reference or reusable tools

## Common Mistakes
What goes wrong + fixes

## Real-World Impact (optional)
Concrete results
```

**Frontmatter Requirements:**
- `name`: Use letters, numbers, and hyphens only
- `description`: "Use when..." focus on triggering conditions
  - Start with "Use when..."
  - Include specific symptoms, situations, contexts
  - NEVER summarize the skill's process or workflow
  - Keep under 500 characters if possible

**Claude Search Optimization (CSO):**
- Rich description field answers: "Should I read this skill right now?"
- Future Claude reads description to decide which skills to load
- Description = When to Use, NOT What the Skill Does

---

## V. Contributor Guidelines & PR Requirements

**File:** `CLAUDE.md`

**For AI Agents - 94% PR Rejection Rate:**

BEFORE opening a PR:

1. **Read entire PR template** - Fill every section with real, specific answers
2. **Search for existing PRs** - Open AND closed. Don't duplicate.
3. **Verify real problem** - Don't contribute vaguely; describe specific experience
4. **Confirm belongs in core** - Domain-specific → standalone plugin
5. **Identify yourself** - Disclose model, harness version, every plugin
6. **Show human partner complete diff** - Get explicit approval before submitting

**PR Requirements:**
- Fully complete PR template (no blanks, no placeholders)
- Search existing PRs (open AND closed) for duplicates
- Show evidence of human involvement (human reviews complete diff before submission)
- Disclose authoring environment (model, harness, plugins)
- Target `dev` branch, not `main`

**What Will NOT Be Accepted:**
- Third-party dependencies (zero-dependency by design)
- "Compliance" changes to skills without eval evidence
- Project-specific configuration
- Bulk or spray-and-pray PRs
- Speculative or theoretical fixes
- Domain-specific skills (publish separately)
- Fork-specific changes
- Fabricated content
- Bundled unrelated changes

**New Harness Support:**
- MUST include session transcript proving end-to-end integration
- Real integration loads `using-superpowers` bootstrap at session start
- Acceptance test: `Let's make a react todo list` → brainstorming auto-triggers
- Paste complete transcript in PR

**Skill Changes Require Evaluation:**
- Use `superpowers:writing-skills` to develop
- Run adversarial pressure testing across sessions
- Show before/after eval results in PR
- Don't modify carefully-tuned content without evidence

---

## VI. Project Philosophy & Principles

**From README.md:**

### The Basic Workflow

1. **brainstorming** - Activates before writing code. Refines rough ideas through questions, explores alternatives, presents design in sections for validation. Saves design document.

2. **using-git-worktrees** - Activates after design approval. Creates isolated workspace on new branch, runs project setup, verifies clean test baseline.

3. **writing-plans** - Activates with approved design. Breaks work into bite-sized tasks (2-5 minutes each). Every task has exact file paths, complete code, verification steps.

4. **subagent-driven-development** or **executing-plans** - Activates with plan. Dispatches fresh subagent per task with two-stage review (spec compliance, then code quality), or executes in batches with human checkpoints.

5. **test-driven-development** - Activates during implementation. Enforces RED-GREEN-REFACTOR: write failing test, watch it fail, write minimal code, watch it pass, commit. Deletes code written before tests.

6. **requesting-code-review** - Activates between tasks. Reviews against plan, reports issues by severity. Critical issues block progress.

7. **finishing-a-development-branch** - Activates when tasks complete. Verifies tests, presents options (merge/PR/keep/discard), cleans up worktree.

**The agent checks for relevant skills before any task.** Mandatory workflows, not suggestions.

### Philosophy

- **Test-Driven Development** - Write tests first, always
- **Systematic over ad-hoc** - Process over guessing
- **Complexity reduction** - Simplicity as primary goal
- **Evidence over claims** - Verify before declaring success

---

## VII. Key Patterns Across Skills

### 1. Iron Laws

Every major skill has an Iron Law (non-negotiable principle):

```
TDD:           NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
Debugging:     NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
Verification:  NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
Brainstorming: HARD-GATE (Don't invoke implementation until design approved)
```

### 2. Red Flags - STOP Pattern

All skills define Red Flags (anti-patterns indicating you should stop and restart):

```
If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "One more fix attempt" (when already tried 2+)

ALL of these mean: STOP. Return to [Phase 1/beginning].
```

### 3. Rationalization Prevention

Skills include tables of Excuses → Reality:

```
| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "Already manually tested" | Ad-hoc ≠ systematic. No record, can't re-run. |
| "Deleting X hours is wasteful" | Sunk cost fallacy. Keeping unverified code is technical debt. |
```

### 4. Checklist Pattern

Implementation skills include verification checklists:

```
- [ ] Every new function/method has a test
- [ ] Watched each test fail before implementing
- [ ] Each test failed for expected reason
- [ ] Wrote minimal code to pass each test
- [ ] All tests pass
- [ ] Output pristine (no errors, warnings)
- [ ] Tests use real code (mocks only if unavoidable)
- [ ] Edge cases and errors covered

Can't check all boxes? You skipped TDD. Start over.
```

### 5. Status → Action Mapping

Skills with branching workflows include decision tables:

```
| Status | Action |
|--------|--------|
| DONE | Proceed to spec compliance review |
| DONE_WITH_CONCERNS | Read concerns, address if needed, proceed to review |
| NEEDS_CONTEXT | Provide missing info and re-dispatch |
| BLOCKED | Assess blocker: context → provide; reasoning → more capable model; task too large → break up; plan wrong → escalate |
```

### 6. No Placeholders Rule

Planning skill explicitly forbids vague content:

**These are PLAN FAILURES:**
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code)
- Steps that describe what to do without showing how

**Every step must contain actual content an engineer needs.**

### 7. Fresh Context Principle

Subagent-driven and parallel agent skills emphasize:
- Fresh subagent per task (no session inheritance)
- Isolated context (you construct exactly what they need)
- Preserves controller's context for coordination work
- No context pollution between tasks

---

## VIII. Integration Workflows

### Recommended Execution Path

1. **New feature request**
   ↓
2. Use `/brainstorming` skill
   ↓
3. Design document approved
   ↓
4. Use `/writing-plans` skill (creates plan)
   ↓
5. Plan complete
   ↓
6. Choose execution:
   - **Parallel session** → `/executing-plans` (for async work)
   - **Same session with fresh subagents** → `/subagent-driven-development` (recommended)
   ↓
7. All tasks complete
   ↓
8. Use `/finishing-a-development-branch` skill

### Code Review Integration

**Part of brainstorming → planning → execution → finishing workflow**

- `/requesting-code-review` - Between tasks during subagent execution
- `/receiving-code-review` - When human provides feedback

### Debugging Integration

**When a test fails or bug appears:**
1. Use `/systematic-debugging` skill (Phase 1 & 2)
2. Form hypothesis (Phase 3)
3. Write failing test (use `/test-driven-development`)
4. Implement fix (TDD cycle)
5. Use `/verification-before-completion` before claiming fixed

---

## IX. Skills NOT in This Document

These skills exist but are not fully documented in snippets (reference the repo for details):

- `requesting-code-review` - Pre-review checklist
- `receiving-code-review` - Responding to feedback
- `using-superpowers` - Introduction to the skills system
- Supporting techniques in systematic-debugging:
  - `root-cause-tracing.md` - Trace bugs backward through call stack
  - `defense-in-depth.md` - Add validation at multiple layers
  - `condition-based-waiting.md` - Replace arbitrary timeouts with condition polling
- `testing-anti-patterns.md` - Pitfalls in mocking and test design

---

## X. Key Files & Locations

```
superpowers/
├── .claude-plugin/
│   ├── plugin.json          # Claude plugin manifest
│   └── marketplace.json     # Marketplace config
├── .cursor-plugin/
│   └── plugin.json          # Cursor IDE integration
├── .codex-plugin/
│   └── plugin.json          # Codex (OpenAI) integration
├── .opencode/
│   ├── INSTALL.md
│   └── plugins/superpowers.js
├── hooks/
│   └── hooks.json           # SessionStart hook for auto-triggering
├── skills/
│   ├── brainstorming/
│   ├── writing-plans/
│   ├── test-driven-development/
│   ├── systematic-debugging/
│   ├── subagent-driven-development/
│   ├── using-git-worktrees/
│   ├── verification-before-completion/
│   ├── finishing-a-development-branch/
│   ├── dispatching-parallel-agents/
│   ├── executing-plans/
│   ├── requesting-code-review/
│   ├── receiving-code-review/
│   ├── using-superpowers/
│   └── writing-skills/
├── CLAUDE.md                # Contributor guidelines (94% PR rejection rate)
├── README.md                # Main project documentation
├── GEMINI.md                # Google Gemini integration
└── package.json             # NPM package metadata
```

---

## XI. Summary: What Makes Superpowers Unique

1. **Enforces discipline through Iron Laws**
   - Non-negotiable: Test first, verify before claiming success, find root cause before fixing

2. **Red Flags instead of warnings**
   - Recognizes rationalizations and stops them before they become problems

3. **Zero dependencies by design**
   - Pure skill documentation, works across all coding agents (Claude, Cursor, Codex, etc.)

4. **Workflow automation**
   - SessionStart hook auto-triggers skills at right moments without user opt-in per session

5. **TDD applied to documentation**
   - Skills are pressure-tested with baseline failures before being deployed

6. **Subagent-native**
   - Designed for multi-agent execution with two-stage reviews and fresh context per task

7. **Evidence-first culture**
   - Every completion claim must be backed by verification evidence (test runs, build output, etc.)

8. **No placeholders**
   - Plans include complete code, exact commands, real test cases — no "fill in later"

9. **Rationalizations catalogued**
   - Every excuse to skip process is explicitly listed with its reality

10. **Contributor rigor**
    - 94% PR rejection rate because maintainers enforce all principles strictly

---

*End of document*

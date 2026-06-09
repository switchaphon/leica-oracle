---
name: upstream-lens
description: "Analyze a repo's recent commits through 5 optical lenses — see what a flat log hides. Leica's precision optics applied to upstream intelligence."
---

# /upstream-lens — 5-Lens Upstream Analysis

> "A flat log shows WHAT happened. Five lenses show WHAT IT MEANS."

## Usage

```
/upstream-lens <owner/repo>                    # Last 14 days
/upstream-lens <owner/repo> --since 2026-05-25 # Custom range
/upstream-lens <owner/repo> --lenses 3         # Quick mode (3 lenses)
```

## Step 1: Fetch Raw Data

```bash
REPO="${1:-Soul-Brews-Studio/maw-js}"
SINCE="${2:-$(date -v-14d +%Y-%m-%d)}"

gh api "repos/$REPO/commits?since=${SINCE}T00:00:00Z&per_page=100" --paginate \
  --jq '.[] | [.commit.author.date[0:10], .sha[0:7], (.commit.message|split("\n")[0]), .author.login // .commit.author.name] | @tsv'
```

Save raw output. Count total commits.

## Step 2: Apply 5 Lenses

Run each lens sequentially on the same data. Each lens asks a DIFFERENT question.

### 🔭 Lens 1: Telescope (Big Picture)
- Group commits by day → show daily count as bar chart
- Calculate velocity: commits/day average, peak day, quiet days
- Trend: accelerating, steady, or cooling?
- Answer: "Is this repo healthy or stressed?"

### 🔬 Lens 2: Microscope (Hotspots)
- Extract file paths from commit messages (feat(X), fix(X), or infer from prefix)
- Find the TOP 5 areas being touched most
- Who's committing? Human vs bot vs CI
- Answer: "Where is the energy concentrated?"

### 📐 Lens 3: Blueprint (Structure)
- Classify by prefix: feat / fix / refactor / docs / chore / bump / test / ci
- Ratio: new features vs fixes vs maintenance
- Any new directories or files mentioned?
- Any deletions or deprecations?
- Answer: "Is this building new things or maintaining old ones?"

### ⚠️ Lens 4: Red Flag (Risk)
- Count reverts, force pushes, "hotfix", "urgent", "broken"
- Large diffs (if detectable from message: "rewrite", "migration", "breaking")
- Same file fixed multiple times (yo-yo pattern)
- Answer: "What could bite us if we pull this upstream?"

### 🔮 Lens 5: Forecast (Prediction)
- Based on patterns: what's likely next?
- Areas with heavy feat → expect bugs soon
- Areas with heavy fix → stabilizing, safe to integrate
- Quiet areas → stale or stable?
- Answer: "What should we watch in the next 2 weeks?"

## Step 3: Cross-Lens Summary

Write 3-5 sentences synthesizing what multiple lenses agree on.
Format as a verdict:

```
VERDICT: [one line — the state of this repo in plain language]
SIGNAL:  [what to watch]
NOISE:   [what to ignore]
```

## Output Format

All output in code blocks (Discord-safe). Use monospace alignment.
Each lens gets its own section with emoji + name + guiding question.
Tables over prose. Numbers over feelings.

## Rules

1. RUN REAL COMMANDS — no mock data
2. Each lens must cite specific commits (sha + message)
3. Lenses may disagree — show the tension, don't harmonize
4. Keep each lens under 15 lines — precision, not padding
5. Cross-lens summary is mandatory — the synthesis is the value
6. Rerunnable — same command, different day, fresh analysis

---
name: git-file-tracker
description: "Track file lifecycle in any git repo — when files were born, deleted, renamed, and what's still alive. See the samsara of your codebase."
---

# /git-file-tracker — File Lifecycle Analysis

> "ไฟล์ก็เกิดขึ้น ตั้งอยู่ ดับไป เหมือนทุกสิ่ง"

## Usage

```
/git-file-tracker                    # Current repo, all time
/git-file-tracker --since 2026-05-25 # Custom range
/git-file-tracker <path/to/repo>     # Specific repo
```

## Step 1: Files Created (Born)

```bash
git log --diff-filter=A --name-only --format="COMMIT:%H %ai %s" |
  awk '/^COMMIT:/{date=$2; msg=substr($0,index($0,$4))} /^[^C]/{print date"\t"$0"\t"msg}'
```

Group by date → show "birth timeline"

## Step 2: Files Deleted (Died)

```bash
git log --diff-filter=D --name-only --format="COMMIT:%H %ai %s" |
  awk '/^COMMIT:/{date=$2; msg=substr($0,index($0,$4))} /^[^C]/{print date"\t"$0"\t"msg}'
```

Count total deleted. Show which commits killed them.

## Step 3: Files Renamed (Reincarnated)

```bash
git log --diff-filter=R --name-status --format="COMMIT:%H %ai" |
  grep "^R"
```

## Step 4: Files Still Alive

```bash
git ls-files | wc -l
```

Compare: total ever created vs still alive = survival rate

## Step 5: Summary

```
BORN:     X files created
DIED:     Y files deleted
RENAMED:  Z files reincarnated
ALIVE:    N files remain
SURVIVAL: (N / X) * 100 %

Busiest birth day:  YYYY-MM-DD (N files)
Biggest massacre:   YYYY-MM-DD (N files deleted)
Oldest survivor:    <filename> (since YYYY-MM-DD)
```

## Output

Code blocks, monospace, Discord-safe. Tables for timelines.

## Rules

1. Run real git commands — no mock
2. Cite specific commits + dates
3. "Nothing is Deleted" — git history preserves all

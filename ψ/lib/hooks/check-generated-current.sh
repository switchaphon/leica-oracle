#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# check-generated-current.sh - block a commit that edits a source without
# regenerating what is published from it.
#
# WHY THIS EXISTS
#
# On 2026-09-04 a claim was retracted in CASE-STUDY.md and in the reference page
# and NOT in README.md, which went on asserting it for seven more hours to the
# one reader who had disproved it. The day before, a published artifact asserted
# "six traps" for a day after the markdown had grown to seventeen.
#
# Both times the rule already existed, written down, in this repo's own
# learnings:
#
#     "Retraction is not complete when the source is corrected. It is complete
#      when every surface carrying the claim is corrected, withdrawn, or
#      explicitly superseded."
#         - ψ/memory/learnings/2026-09-04_a-published-claim-outlives-my-belief-in-it.md
#
#     "Documentation is not a control; only a changed default is."
#         - ψ/memory/learnings/2026-08-28_a-written-lesson-is-not-a-held-lesson.md
#
# A memory audit on 2026-09-05 counted eleven occurrences of this class in
# thirty-nine days, every remedy a rule to remember, every rule broken by its
# own author - and exactly one attempt at an executable gate
# (build-case-study.py --check), which was built and then wired to nothing.
#
# This is that flag, wired.
#
# WHAT IT DOES NOT DO
#
# It cannot tell whether a claim is true, or find every copy of a number. It
# checks one thing only: if you staged a source, is the artifact built from it
# still in step? That is the mechanical half of the problem. The judgement half
# stays yours.
#
# Install (once per clone):
#     ln -sf ../../ψ/lib/hooks/check-generated-current.sh \
#            .git/hooks/pre-commit.local
# The fleet hook at ~/.config/git/hooks/pre-commit chains to it automatically.
#
# Escape hatch, for a deliberate two-step commit:
#     SKIP_GENCHECK=1 git commit ...
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail

RED=$'\033[0;31m'; YLW=$'\033[0;33m'; GRN=$'\033[0;32m'; DIM=$'\033[2m'; RST=$'\033[0m'

if [[ "${SKIP_GENCHECK:-0}" == "1" ]]; then
  printf '%s⚠  generated-artifact check SKIPPED (SKIP_GENCHECK=1)%s\n' "$YLW" "$RST" >&2
  exit 0
fi

REPO_ROOT=$(git rev-parse --show-toplevel) || exit 0
cd "$REPO_ROOT" || exit 0

STAGED=$(git diff --cached --name-only --diff-filter=ACMR)
[[ -z "$STAGED" ]] && exit 0

FAILED=0

# ── the manifest ────────────────────────────────────────────────────────────
# One line per generated artifact:
#     <source path> <checker command>
# The checker must exit non-zero when the artifact is out of date and print its
# own explanation. Add a row here when you add a renderer; a renderer with no
# row is a renderer whose output can drift silently.
check_pair() {
  local src="$1"; shift
  local label="$1"; shift
  grep -qxF "$src" <<<"$STAGED" || return 0
  printf '%s→ %s staged, checking %s%s\n' "$DIM" "$src" "$label" "$RST" >&2
  if ! "$@" >/dev/null 2>&1; then
    printf '%s✖ %s is stale relative to %s%s\n' "$RED" "$label" "$src" "$RST" >&2
    "$@" 2>&1 | sed 's/^/    /' >&2
    FAILED=1
  fi
}

check_pair "ψ/lab/hii-water-level/CASE-STUDY.md" \
           "CASE-STUDY.html" \
           python3 ψ/lab/hii-water-level/build-case-study.py --check

# ── trap-count coherence ────────────────────────────────────────────────────
# The case study names its own trap count in prose ("Twenty-eight traps"). That
# sentence has been wrong before, for a day, on a published page. Compare the
# words against the headings.
if grep -qxF "ψ/lab/hii-water-level/CASE-STUDY.md" <<<"$STAGED"; then
  CS=ψ/lab/hii-water-level/CASE-STUDY.md
  n=$(grep -c '^### 3\.[0-9]* ' "$CS")
  claimed=$(sed -n 's/^## 3\. \([A-Za-z-]*\) traps.*/\1/p' "$CS" | head -1)
  words=(zero one two three four five six seven eight nine ten eleven twelve
         thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty
         twenty-one twenty-two twenty-three twenty-four twenty-five twenty-six
         twenty-seven twenty-eight twenty-nine thirty)
  expect="${words[$n]:-$n}"
  if [[ "$(tr '[:upper:]' '[:lower:]' <<<"$claimed")" != "$expect" ]]; then
    printf '%s✖ CASE-STUDY.md says "%s traps" but has %d trap headings (expected "%s")%s\n' \
      "$RED" "$claimed" "$n" "$expect" "$RST" >&2
    FAILED=1
  fi
fi

# ── dangling internal references ────────────────────────────────────────────
# "see 3.29" pointing at a trap that does not exist is how a correction ends up
# citing a fix nobody wrote.
if grep -qxF "ψ/lab/hii-water-level/CASE-STUDY.md" <<<"$STAGED"; then
  CS=ψ/lab/hii-water-level/CASE-STUDY.md
  while read -r ref; do
    [[ -z "$ref" ]] && continue
    grep -q "^### ${ref} " "$CS" || {
      printf '%s✖ CASE-STUDY.md references %s, which has no heading%s\n' "$RED" "$ref" "$RST" >&2
      FAILED=1
    }
  done < <(grep -o 'see 3\.[0-9]\+' "$CS" | sed 's/see //' | sort -u)
fi

if [[ $FAILED -ne 0 ]]; then
  cat >&2 <<EOF

${YLW}A source changed and something published from it did not.${RST}

  Rebuild, stage the result, and commit again:
      python3 ψ/lab/hii-water-level/build-case-study.py
      git add ψ/lab/hii-water-level/CASE-STUDY.html

${DIM}Deliberate two-step commit:  SKIP_GENCHECK=1 git commit ...${RST}
EOF
  exit 1
fi

printf '%s✓ generated artifacts current%s\n' "$GRN" "$RST" >&2
exit 0

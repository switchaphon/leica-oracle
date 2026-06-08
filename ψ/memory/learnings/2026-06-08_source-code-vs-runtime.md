# Source code analysis ≠ runtime reality

**Date**: 2026-06-08
**Source**: rrr: leica-oracle (maw token doc session)

## Pattern

Reading source code or binary strings gives you what code _does_, but not what users _see_. Interactive commands (browser OAuth, GPG keygen, pinentry dialogs) have UX that cannot be verified from code alone.

## Examples from this session

1. **`claude setup-token`**: Binary string says `"Use this token by setting: export CLAUDE_CODE_OAUTH_TOKEN=<token>"`. Assumed token was on that line. Reality: token is displayed on its OWN line above, `<token>` is a placeholder.

2. **GPG pinentry**: Documented "dialog box pops up". Reality: fresh `brew install gnupg` installs `pinentry-curses` (terminal-based), not `pinentry-mac` (GUI dialog).

3. **`maw init` prompts**: Guessed "ghq root?" as a prompt. Reality: removed in PR #680 — only 3 prompts now.

## Rule

When documenting interactive CLI flows: always ask a human to run the command once and report the exact output. Claim confidence only AFTER human verification of interactive steps.

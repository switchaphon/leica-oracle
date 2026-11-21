# maw-codex-team-kit: quick reference

Source: `/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/maw-codex-team-kit`, HEAD `397db8b`. 8 commits, all authored "Nat" on 2026-07-06 (19:00 to 19:48 +0700). 18 tracked files.
Read-only review. Nothing was installed, built, or run. Line refs are `file:line` at that HEAD. Quoted text keeps its wording, with arrows written as `->`. CHEATSHEET.md is in Thai and is paraphrased.

## Key findings

- Failures are reported as success. `down` prints "team down ... branches cleared" even when kill, move, or `branch -d` failed (team.ts:137, 150, 152). `up` keeps spawning coders after a failed `use` and still prints "coders up" (team.ts:118-125).
- Charter values keep trailing `# comments`. The kit's own examples put one on the `session:` line (help.ts:32, CHEATSHEET.md:23, templates/team.yaml:10). Copied as written, `down` targets a window name that does not exist (team.ts:64, 137).
- The kit never logs in and never reads `auth.json`. It has no quota or rate-limit logic. Several coders can share one account with no warning (team.ts:77, 116).

## 1. What it does

It is a `maw` plugin with the command `codex` (plugin/plugin.json:10-13). It spawns a team of codex/omx coders from a YAML charter. Per coder it creates a git worktree at `agents/<slug>`, pins `CODEX_HOME` to `~/.codex-team/<N>`, and appends a trust entry for that worktree path so codex skips the trust prompt (team.ts:110-127, use.ts:37-38, lib.ts:98-110). `use` pins `CODEX_HOME` in a directory's `.envrc`, and `list` and `current` read it back. The team is torn down by killing each window, moving each worktree to `/tmp`, pruning, and running `git branch -d`: kill each window, move each worktree to `/tmp`, prune, `git branch -d` (team.ts:129-154).

It does NOT:
- log in, create accounts, or read or write `auth.json`. "login" appears nowhere in the repo. `auth.json` appears only in docs and help text (README:48, help.ts:57, CHEATSHEET.md:112).
- detect, measure, retry, or fail over on quota or rate limits. "quota" appears only in one code comment (team.ts:108-109).
- send the charter's `prompt:` to a coder. `up` leaves coders idle (README:82, FIELD-REPORTS.md:51).
- commit, merge, or check worktree state. The base branch is hard-coded `main` (team.ts:118).
- check that tmux windows are alive. `status` filters `maw worktree ls` text (team.ts:156-161).
- set `OMX_AUTO_UPDATE`. The docs tell you to export it (CHEATSHEET.md:111). `buildEnvrc` writes only `CODEX_HOME` (lib.ts:117-134).
- have tests. None are tracked. `typecheck` is the only check (plugin/package.json:8).

## 2. Prerequisites and install

Stated (README:47-49): `maw` ("fleet CLI", linked to the maw-rs repo), `bun`, `direnv`, and codex accounts in `~/.codex-team/<N>/`, each with `auth.json` and `config.toml`. No prerequisite versions are stated anywhere in the repo.

Used by code but not listed: `omx` (the engine binary, hard-coded at team.ts:33), `git` (team.ts:39, 148, 150), `tmux` (implied through maw windows; template:10 says "tmux session"), and `ls` (lib.ts:61).

Pinned: `plugin/bun.lock` resolves `typescript` 5.9.3 and `@types/bun` 1.3.14. package.json:11-12 asks for `"latest"` and `^5.6.0`. No Bun version is pinned.

Install, exactly as README:36-45 gives it:

```bash
cd plugin && bun install && bun run build   # build; package.json:7 runs: bun build src/index.ts --target=bun --outfile=dist/index.js
ln -sfn "$PWD" ~/.maw/plugins/codex         # link; run it from plugin/ so $PWD is plugin/
maw codex                                    # expect the usage line
```

- `dist/` is gitignored (.gitignore:3) and absent from this checkout, so every machine must build. The entry is `./dist/index.js` (plugin.json:9).
- The Makefile has no install step. Its `up`, `down`, `status` and `help` targets (Makefile:16-26) call `maw codex <verb>` with no arguments, so `make up` cannot pass `--account`.
- CHEATSHEET.md:10-14 gives a `ghq get` variant of the same steps.
- README:44 quotes the usage line without `help`. The code prints the usage with `help` added, plus a hint to run `maw codex help` (index.ts:70-71).

## 3. Commands

| Command | Args and flags | Behaviour (source) | Example |
|---|---|---|---|
| `use <N> [dir]` | `N` must be an existing numeric dir in `~/.codex-team` (use.ts:26-28). `dir` defaults to the caller's `$PWD` (lib.ts:25-27). | Replaces any `CODEX_HOME` line in `dir/.envrc` with `export CODEX_HOME="$HOME/.codex-team/<N>"` (lib.ts:117-134). Runs `direnv allow <dir>` (use.ts:34-35). Appends trust to `config.toml` if that file exists (lib.ts:98-110). Output names the account, the path, trust, and any direnv failure (use.ts:43-48). | `maw codex use 3 ~/code/proj/agents/proj-codex-parser` |
| `list [dir]` (alias `ls`, index.ts:44) | `dir` optional | Lists numeric dirs and marks the one in `dir/.envrc`. Prints "no accounts in ~/.codex-team" if none exist (list.ts:10-25). help.ts:13 omits `[dir]`. | `maw codex list` |
| `current [dir]` | `dir` optional | Prints the account number only, or `none` (current.ts:10-14). Meant for statuslines. | `maw codex current` prints `3` |
| `up [charter] [--account N]` | `charter` is an explicit path, else the first `.yaml` or `.yml` in `<git root>/ψ/teams` (team.ts:44-55). `--account N` or `--account=N` (index.ts:27-33). | Once: adds `agents/` to `.git/info/exclude` (team.ts:90-105, 114). Per coder, in order: `maw worktree add <slug> --base main` (team.ts:118); `use` on the worktree (team.ts:120); `maw work . --wt <slug> -e "direnv exec . omx --yolo --direct"` (team.ts:122). `--account` overrides every coder (team.ts:116). | `maw codex up --account 5` |
| `down [charter]` | Same charter rule. `--account` is parsed and ignored (index.ts:56-61). | Per coder: `maw kill <session>:<repo>-<slug>` (team.ts:137), then renames the worktree dir to `/tmp/wt-<slug>-<pid>` (team.ts:139-145). Then once: `git worktree prune` (team.ts:148). Then per coder: `git branch -d agents/<slug>` (team.ts:149-151). | `maw codex down` |
| `status` | No arguments (index.ts:62-64). | Runs `maw worktree ls` in `$PWD` and keeps lines that mention codex or `agents/`. Prints "no worktrees" if maw fails, "(no codex worktrees)" if none match (team.ts:156-161). | `maw codex status` |
| `help` (also `--help`, `-h`) | None | Prints the bundled reference (help.ts:6-59). An unknown or missing verb prints a one-line usage (index.ts:70-71). | `maw codex help` |

Notes:
- Only `up` and `down` take a charter path. A bare number is read as a charter path, not an account (index.ts:34). So `maw codex up 5` fails with "no charter found" (index.ts:24, 52-53).
- Exit status: no code path sets one (no `process.exit` call and no `process.exitCode` assignment in `src/`). Handled failures exit 0. `index.ts` has no try/catch.

## 4. Charter format

The parser is regex-based (team.ts:63-80). package.json has no YAML dependency.

| Key | Read by | Required | Default | Notes |
|---|---|---|---|---|
| `name` | `^name:` (team.ts:63) | no | `team` | Stored on the Charter object but never printed. |
| `session` | `^session:` (team.ts:64) | in practice yes | `""` | Feeds the kill target (team.ts:137) and the banner (team.ts:125). Empty is not rejected. |
| `default_account` | `^default_account:\s*(\d+)` (team.ts:67) | no | `1` | Digits only. Applies to members with no `omx-N` or `codex-N` engine. |
| `default_engine` | `^default_engine:` (team.ts:68) | no | none | UNDOCUMENTED: absent from README, template and help. Used only when `default_account` is missing. |
| `- role:` items | Split on `^\s*- role:` (team.ts:71) | yes | none | The `members:` key is never read. Any `- role:` item counts. |
| `role` | First line of each item (team.ts:72) | no | `""` | Only the exact value `lead` matters (team.ts:76). |
| `name` (member) | First `name:` in the item (team.ts:73) | yes | `""` | Becomes the slug: worktree name, window name, `agents/<slug>` branch, temp dir name. Not validated. |
| `engine` | First `engine:` in the item (team.ts:74) | no | `""` | Only digits after `omx-` or `codex-` are used (team.ts:77). `claude` is ignored. The launch binary is always `omx` (team.ts:33). |
| `worktree` | First `worktree:` in the item (team.ts:75) | yes for coders | none | Joined onto the repo root (team.ts:119, 138). |

- Skipped members (team.ts:76): role is `lead`, or there is no `worktree`, or `worktree` is `false` or `~`.
- Account precedence (team.ts:77, 116): `--account` > member `omx-N`/`codex-N` > `default_account` > `default_engine` > `1`. This matches README:142-149.
- Read by nothing in `src/`: `project` (template:9), `branch` (template:29, 40; the branch is hard-coded as `agents/<slug>` at team.ts:150), and `prompt` (template:30-34, 41-43).

Minimal (parses correctly):

```yaml
session: 90-myproject
members:
  - role: parser
    name: myproject-codex-parser
    engine: omx-1
    worktree: agents/myproject-codex-parser
```

Full (every key the code reads). Result: parser on account 1, writer on account 2 via `default_account`, lead skipped:

```yaml
name: myproject-team
session: 90-myproject
default_account: 2
members:
  - role: lead
    name: myproject
    engine: claude
  - role: parser
    name: myproject-codex-parser
    engine: omx-1
    worktree: agents/myproject-codex-parser
  - role: writer
    name: myproject-codex-writer
    engine: claude
    worktree: agents/myproject-codex-writer
```

Parser trap (in no doc): values run to end of line, so a trailing `# comment` becomes part of the value (no stripping anywhere in team.ts:63-75). Three in-repo examples put a comment on the `session:` line: help.ts:32, CHEATSHEET.md:23, templates/team.yaml:10. Copied as written, `session` becomes `90-myproject` followed by the comment text. The kill target then names a window that does not exist, `down` misses it silently (team.ts:137), and it still prints success (team.ts:152). The README example (README:61-62) has no such comment. A comment after `role:` breaks the `lead` check (team.ts:76). A comment after `engine:` is harmless only because the regex takes the first `omx-N`. Top-level keys must start at column 0.

## 5. Account model

- Home: `~/.codex-team` (lib.ts:17, `homedir()`). An account is a numeric subdirectory (lib.ts:66, `^\d+$`). The docs say each holds `auth.json` and `config.toml` (README:48-49, help.ts:57). CHEATSHEET.md:112 gives a range of 1 to 10. The code does not enforce it.
- What the kit writes there: only `config.toml`, appending `[projects."<abs path>"]` with `trust_level = "trusted"` (lib.ts:107-108). If `config.toml` is missing, it returns false and writes nothing (lib.ts:101-106). The append on lib.ts:108 sits outside any try/catch.
- Existence check: the directory name only (lib.ts:71-73, use.ts:26-28). `auth.json` and `config.toml` are not checked.
- Login: the kit authenticates nothing. No code runs `codex login` or reads `auth.json`. It points `CODEX_HOME` at a directory that must already hold credentials. The docs do not say how to create or log in an account (not found in source or docs).
- Shared account: nothing stops several coders from landing on one `N`. They can come from `--account N` (team.ts:116), `default_account` (team.ts:77), or equal `omx-N` engines. There is no duplicate check and no warning. Coders on one `N` share `auth.json` and `config.toml`. Trust entries accumulate per worktree path, and `down` never removes them (team.ts:146-153 has no cleanup). Not found in source or docs: anything about concurrent sessions sharing one `CODEX_HOME`.
- Rate-limit statements, verbatim:
  - README:24: "Shared account. If every coder uses the default codex home they share one auth -> one rate-limit."
  - templates/team.yaml:3-4: "One coder per task, each pinned to its own codex account (~/.codex-team/<N>) so they don't share a rate-limit."
  - team.ts:108-109 (code comment): `--account` is "handy to consolidate a run onto whichever account still has quota."
  - Other quota wording: templates/team.yaml:38 ("a DIFFERENT account = isolated quota") and CHEATSHEET.md:34 (paraphrased: a separate account isolates quota). Neither describes any limit.

## 6. Gotchas and traps

### 6a. Documented gotchas (README, CHEATSHEET, help, FIELD-REPORTS)

| # | Source | Symptom | Documented fix | Guarded in src? |
|---|---|---|---|---|
| 1 | README:104-107; CHEATSHEET.md:98; help.ts:50-51 | Coder on the default home: shared auth, trust prompt | Pin `CODEX_HOME` in `.envrc`; launch via `direnv exec .` | Partly. `up` writes `.envrc` (team.ts:120), but a failed `use` still launches (team.ts:120-123). |
| 2 | README:109-111; CHEATSHEET.md:97 | Trust prompt on a new worktree | Seed trust into `config.toml` | Partly. Silent no-op if `config.toml` is missing (lib.ts:101-106). `up` never checks `trustSeeded` (team.ts:120-121). |
| 3 | README:113-117; CHEATSHEET.md:99-100; help.ts:42, 52 | Kill by session misses the window; coder strands at a shell | Derive the repo basename | Yes for the name (team.ts:131, 137). Kill result ignored (team.ts:137). |
| 4 | README:119-121; CHEATSHEET.md:103; help.ts:53 | `branch -d` refuses while the worktree is still registered | Kill, move, prune, then `branch -d` | Order yes (team.ts:147-151). `branch -d` result ignored (team.ts:150), yet the banner says branches cleared (team.ts:152). |
| 5 | CHEATSHEET.md:105; help.ts:53 | A safety hook blocks `--force` and `rm -rf` | `mv` to `/tmp`, then `branch -d` | Yes. No force and no rm (team.ts:141). |
| 6 | README:123-124; CHEATSHEET.md:101 | `maw team up` on a mixed charter deletes worktrees (bug #258) | Use `maw codex up` | By construction. The kit never calls `maw team`. |
| 7 | README:126-129; CHEATSHEET.md:104 | Worktrees and `.envrc` leak into the project's git | Auto-exclude `agents/` | Yes, on `up` only (team.ts:90-105, 114). The rule is hard-coded to `agents/` (team.ts:98-100). |
| 8 | README:131-135; CHEATSHEET.md:106; help.ts:55; FIELD-REPORTS.md:8-17 | Uncommitted code is invisible in worktrees | Commit first | No. Base is hard-coded `main` (team.ts:118). No dirty check (team.ts:110-127). |
| 9 | FIELD-REPORTS.md:51 | `up` boots coders idle; nothing is dispatched | `maw hey <session>:<window> "<task>"` | Not applicable by design. The charter `prompt:` is never read (template:30-34). |
| 10 | FIELD-REPORTS.md:53-54 | Coders do not auto-commit; branch is empty at merge | Tell each coder to commit | No. `down` moves dirty worktrees (team.ts:134 comment says so) and prints no destination. |
| 11 | FIELD-REPORTS.md:55-57 | Shared files cause merge conflicts | Lead owns hot files; coders add new files only | Process rule. Not enforced. |
| 12 | CHEATSHEET.md:102 | `.envrc` written into the plugin dir (cwd = plugin dir) | Read `process.env.PWD` | Partly. `callerDir()` uses PWD (lib.ts:25-27). Relative `dir` (use.ts:30, 35) and charter paths (team.ts:58) are not resolved against it. Not run. |
| 13 | CHEATSHEET.md:111; help.ts:57 | omx self-updates at boot | `export OMX_AUTO_UPDATE=0` in `~/.zshrc` or `.envrc` | No. The kit never sets it. |
| 14 | CHEATSHEET.md:112; README:24 | Shared-account rate limits | One account per coder | No. See section 5. |

### 6b. Traps in the code that no doc mentions

| # | Trap | Source | Effect |
|---|---|---|---|
| A | Failed `use` does not stop the spawn | team.ts:118-123 | The `worktree add` result is ignored. If `use` fails, `maw work` still runs, with no `.envrc` pin. The coder then uses the environment's `CODEX_HOME`, or the default home if unset (README:105). The banner still says "coders up" (team.ts:125). Inferred, not run. |
| B | Missing worktree dir throws | use.ts:32 | If `maw worktree add` failed, `writeFileSync` into the missing dir throws. Nothing catches it. Inferred from fs semantics. |
| C | Re-running `up` without `down` | team.ts:118 | No existence check before `worktree add`. Result ignored. Not run. |
| D | `down` leaves debris | team.ts:136-151 | The `agents/` exclude line stays. Trust blocks stay in each `config.toml`. `/tmp/wt-*` dirs remain. The output never says where a worktree went. |
| E | `/tmp` move can fail across filesystems | team.ts:141-143 | `renameSync` fails with EXDEV if `/tmp` is on another filesystem (common on Linux). The catch prints "move failed" and the worktree stays registered. Inferred, not run. |
| F | A missing binary may throw | lib.ts:41-46 | `Bun.spawnSync` may throw for a missing `direnv`, `git` or `maw` instead of returning `ok: false`. Not verified. |
| G | `gitRoot()` falls back silently | team.ts:37-41 | If `git rev-parse` fails, the caller dir is used as the root. Later steps then fail quietly. |
| H | `--yolo` is hard-coded | team.ts:33 | Every coder runs `omx --yolo`. README:22-23 says only that `--yolo` does not skip the trust prompt. The docs never say what it permits. |
| I | No slug or session validation | team.ts:63-80 | Empty or odd values flow into `maw worktree add`, `kill` and branch names. |
| J | `.envrc` on the main checkout is not excluded | use.ts:30-32; team.ts:98-100 | Only `agents/` is excluded. A `use` run on the main repo writes a `.envrc` that nothing excludes. |
| K | Trust key is `resolve()`, not realpath | lib.ts:98-99 | A symlinked path may not match the path codex checks. Not tested. |

### 6c. Docs versus code

| Doc says | Code does | Source |
|---|---|---|
| README:8: `up` spawns "the whole team from ψ/teams/*.yaml" | Reads only the first `.yaml` or `.yml` from an unsorted readdir. | team.ts:49-51 |
| README:9 and CHEATSHEET.md:42: `status` lists "live" coders (CHEATSHEET adds worktree, branch, session) | Filters `maw worktree ls` text. No tmux, branch or session fields are added. | team.ts:156-161 |
| README:57-58: "each on a different account" | Advice only. Nothing enforces it. | team.ts:77, 116 |
| README:3-5: every coder boots silently | Depends on `config.toml` existing and `use` succeeding. | lib.ts:101-106; team.ts:120-121 |
| README:119-121: per-coder order is kill, move, prune, branch | Kills and moves all coders first, then one prune, then all branch deletes. | team.ts:134-151 |
| README:47-49: requirements | Omits `omx` (team.ts:33) and `git` (team.ts:37-41). | code |
| template:9, 29, 30-34: `project`, `branch`, `prompt` fields | Never read. | code (grep) |
| CHEATSHEET.md:112: accounts `N=1..10` | Any digits are accepted. | lib.ts:66 |
| CHEATSHEET.md:100 (paraphrased): `down` does not work, and the plugin is said to be fixed | The window name is fixed. Kill failures are still silent. | team.ts:137 |
| CHEATSHEET.md:102: `.envrc` location "fixed" | Partly fixed (row 12 above). | lib.ts:25-27 |
| plugin.json:4 description: account switching only | The plugin also runs the team lifecycle. | index.ts:2-12 |
| README:44: usage text without `help` | Code adds `help` and `[args]`. | index.ts:71 |

## 7. Field reports

| Report | Who and where | Scale | Proven, per the report | Not proven or not stated |
|---|---|---|---|---|
| #1 turso-oracle (FIELD-REPORTS.md:8-17) | Fresh repo | 5 coders | Says "Validated the kit end-to-end (3/3 verbs)" (:16-17). Uncommitted-work trap reproduced (:10-13). | Which three verbs. Accounts, timings, versions, quota events, OS. |
| #2 kru32-oracle (FIELD-REPORTS.md:21-57) | ESP32 web flasher (Astro 7, React, Tailwind v4) | 5 coders on accounts 1, 3, 4, 5, 6 (:29) | Silent boot, zero trust prompts (:31). Teardown killed every window "first try" with session 81-kru32 vs repo kru32-oracle (:32). Four branches of new files merged with 0 conflicts (:42, :56-57). Coders took about 4-6 min each; lead kept 40-81% context (:33). | Rate-limit or quota events. Why account 2 was skipped. Whether any worktree was dirty at `down`. The `--account` and `default_account` paths. `status` output. Versions. Logs or commit hashes. The live site was not fetched. |
| Origin (README:13) | maw-fleetpad | 5 coders | Built and hardened there (README:13). CHEATSHEET.md:3 says validated on "fleetpad + turso + kru32". | No fleetpad report exists in docs/FIELD-REPORTS.md. |

- Who ran them: FIELD-REPORTS.md:3 says the runs were done "by other people with the kit", "not the authors". Only oracle names are given, with no dates and no logs. The reports are self-reported.
- Scale ceiling: nothing documented above 5 coders. Account numbers used: 1, 3, 4, 5, 6.
- Net: silent boot and window-name teardown are reported once each, both in the kru32 run at 5 coders. Rate limits, the `--account` and `default_account` paths, dirty-worktree teardown, and non-macOS hosts are not shown.

## 8. Runtime and versions

- Docs assume maw-rs. README:47 links `github.com/Soul-Brews-Studio/maw-rs`. There is no maw-js mention anywhere in the repo. No maw version is stated, and the code never checks one.
- Commands the kit calls (team.ts): `maw worktree add <slug> --base main` (:118), `maw work . --wt <slug> -e <cmd>` (:122), `maw kill <target>` (:137), `maw worktree ls` (:157).
- Docs-only maw calls: `maw peek` and `maw hey` (CHEATSHEET.md:60-66), `maw team send` (:69), `maw team up` (README:123), `maw serve` with an env var (CHEATSHEET.md:91), and `maw token use` (lib.ts:5, cited as the model it mirrors).
- Manifest: plugin.json:7 `"sdk": "^1.0.0"`, :8 `"schemaVersion": 1`, :3 version `0.1.0`. The code imports no SDK. The entry runs top-level code (index.ts:23-72) with no `import.meta.main` guard and no default export. That suits a script run, not an import.
- Timing: This machine's `maw` moved to maw-rs on 2026-07-27 (local migration record). All 8 commits are dated 2026-07-06, so the runs predate that switch. The repo does not say which maw build they used.
- Bun: no version pinned (section 2).

## 9. Verification status

Nothing was installed, built, or run. Every claim comes from reading source, docs and git metadata. Items marked "inferred" or "not run" need a test before anyone relies on them: 6b rows A, B, C, E, F and K, and 6a row 12.

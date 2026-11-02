# maw-codex-team-kit: architecture

Source: `/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/maw-codex-team-kit`, HEAD `397db8b` (8 commits, all dated 2026-07-06).
Short names such as `team.ts` mean `plugin/src/team.ts`. Line numbers match the files at HEAD.
Method: read-only (find, Read, grep, git log). Nothing was built, installed or run.
"not found in source" means the repo gives no evidence for the claim.

## Key points

- The plugin is a Bun/TypeScript script that shells out to `maw`, `git`, `direnv` and `ls`. It imports no host SDK, although `plugin.json:7` declares `"sdk": "^1.0.0"`. The only maw-rs reference in the repo is `README.md:47`.
- The coder command is `direnv exec . omx --yolo --direct` (`team.ts:33`). The plugin sets no sandbox or approval flag, but it pre-approves each worktree `.envrc` (`use.ts:35`) and seeds codex trust (`lib.ts:98-110`).
- Outcomes are not checked. `up` prints "up" when `maw work` exits 0 and still launches a coder after an account error (`team.ts:120-123`). `down` ignores kill and branch results and always prints success (`team.ts:137`, `:150`, `:152`). Charter values keep inline comments (`team.ts:64` against `templates/team.yaml:10`).

## 1. Directory structure

```
plugin/src/index.ts     argv dispatcher and the only entry point (index.ts:23-72)
plugin/src/lib.ts       shared helpers: callerDir, run (Bun.spawnSync), account list, trust seeding, .envrc rewrite
plugin/src/use.ts       cmdUse: pin CODEX_HOME in <dir>/.envrc, direnv allow, seed trust; formatUse
plugin/src/list.ts      cmdList (alias ls): list ~/.codex-team accounts, mark the active one
plugin/src/current.ts   cmdCurrent: print the active account slug, or "none"
plugin/src/team.ts      findCharter (charter parser) plus cmdUp, cmdDown, cmdTeamStatus; holds ENGINE_CMD
plugin/src/help.ts      HELP text printed by `maw codex help`; no logic
plugin/plugin.json      host manifest: name, entry, cli.command, cli.help, sdk, schemaVersion
plugin/package.json     scripts: build (bun build -> dist/index.js), typecheck; devDependencies only
plugin/bun.lock         lockfile for the dev dependencies
plugin/tsconfig.json    strict, noEmit, types ["bun"]
Makefile                make up/down/status, each a call to `maw codex` (Makefile:16-23)
templates/team.yaml     charter template; users copy it to ψ/teams/<team>.yaml (README.md:57)
README.md               install, charter format, gotchas, config table (documentation only)
docs/CHEATSHEET.md      Thai cheat sheet: lifecycle, dispatch, trap table (documentation only)
docs/FIELD-REPORTS.md   two field reports from other repos (documentation only)
.gitignore              ignores plugin/dist/ (line 3), so a clone has no entry file until built
LICENSE                 MIT (LICENSE:1)
```

No test files are tracked. `lib.ts:114-115` calls `buildEnvrc` "exposed for testing", but no test exists in the repo.

## 2. Entry points and host contract

### 2.1 How a `maw codex <verb>` call reaches the code

- Manifest: `plugin.json:9` `"entry": "./dist/index.js"`; `plugin.json:11` `"command": "codex"` maps `maw codex ...` to this plugin; `plugin.json:7` `"sdk": "^1.0.0"`; `plugin.json:8` `"schemaVersion": 1`.
- Build: `package.json:7` `bun build src/index.ts --target=bun --outfile=dist/index.js`. `dist/` is gitignored (`.gitignore:3`), so a fresh clone has no entry file until `README.md:38` is run.
- Install: `README.md:41` `ln -sfn "$PWD" ~/.maw/plugins/codex`. The loader that reads plugin.json and runs the entry is not in this repo (not found in source).
- Dispatch: `index.ts:23` `const [verb, ...rest] = process.argv.slice(2);`, then `switch (verb)` at `index.ts:39`. Verbs: use (`:40`), list/ls (`:43-44`), current (`:47`), up (`:50`), down (`:56`), status (`:62`), help/--help/-h (`:65-67`). Anything else prints usage (`:70-71`).
- No `import.meta.main` guard: the switch runs at module top level, so it runs when the file is executed and also when it is imported. The execute-as-subprocess style (`bun <entry> <args>`) fits this code. Local notes on how maw-rs loads TS plugins describe that style, but the repo does not show which mode maw uses.
- Exit status: no `process.exit` in plugin/src. Handled failures print text and exit 0 (for example NO_CHARTER, `index.ts:24` and `:53`). Uncaught exceptions end the process (Bun default; not verified here).

### 2.2 What the plugin assumes about host maw

- Runtime is Bun, not Node: `lib.ts:42` `Bun.spawnSync`, `lib.ts:47` TextDecoder, `package.json:7` `--target=bun`, `tsconfig.json:7` `"types": ["bun"]`. The other imports are Node built-ins: fs, path, os (`team.ts:15-16`, `lib.ts:13-15`, `use.ts:9-10`, `list.ts:6-7`, `current.ts:6-7`).
- Host SDK: none imported. Every import is a built-in or a sibling module (grep `^import`). `plugin.json:7` declares `sdk`, but no code reads it.
- maw variant (maw-js or maw-rs): not determined by the code. The only mention of maw-rs in the whole repo is `README.md:47`:
  > Requirements: [`maw`](https://github.com/Soul-Brews-Studio/maw-rs) (fleet CLI), [`bun`](https://bun.sh), ...

  `git log -S maw-rs` lists only commit `45fc500` (the first commit), so the string was added there and not added or removed later.
- Host calls: subprocesses with argv arrays and no shell, looked up on PATH.
  - `maw worktree add <slug> --base main` (`team.ts:118`)
  - `maw work . --wt <slug> -e "direnv exec . omx --yolo --direct"` (`team.ts:122`)
  - `maw kill <session>:<repo>-<slug>` (`team.ts:137`)
  - `maw worktree ls` (`team.ts:157`)
  There is no version check and no existence check. What these subcommands do is not in this repo (not found in source).
- Assumptions stated only in comments: maw dispatches dev-tier plugins with cwd set to the plugin dir, and the caller's PWD is inherited (`lib.ts:19-24`; `team.ts:35-36`). Env read: PWD (`lib.ts:26`) and HOME through `os.homedir` (`lib.ts:17`).
- tmux is never called directly (no "tmux" in plugin/src). Windows are created and killed through maw (`team.ts:122`, `:137`).

## 3. Core abstractions

```
index.ts    -> use.ts, list.ts, current.ts, team.ts, help.ts      (index.ts:17-21)
team.ts     -> lib.ts (callerDir, run), use.ts (cmdUse)          (team.ts:17-18)
use.ts      -> lib.ts (accountExists, buildEnvrc, callerDir, ensureCodexTrust, listAccounts, run)   (use.ts:11)
list.ts     -> lib.ts (callerDir, detectAccount, listAccounts)   (list.ts:8)
current.ts  -> lib.ts (callerDir, detectAccount)                 (current.ts:8)
lib.ts      -> node fs, os, path and the Bun global only         (lib.ts:13-15)
help.ts     -> nothing (exports one string)
```

- `lib.ts` is the kernel. `TEAM_ROOT` = ~/.codex-team (`:17`). `callerDir()` returns PWD, not `process.cwd()` (`:25-27`). `run()` wraps `Bun.spawnSync` and returns `{ok, exitCode, stdout, stderr}` with no try/catch (`:41-54`). `listAccounts()` shells out to `ls` and keeps all-digit names (`:60-68`). `accountExists` (`:71-73`). `detectAccount()` reads the CODEX_HOME line and skips comments (`:80-87`). `ensureCodexTrust()` appends a TOML block (`:98-110`). `buildEnvrc()` replaces the CODEX_HOME line and keeps the rest (`:117-134`).
- `use.ts`: `cmdUse` (`:22-41`) is the only writer of `.envrc` (`:32`). `formatUse` (`:43-48`) is used only by `index.ts:41`. `cmdUp` does not use it.
- `team.ts`: `ENGINE_CMD` (`:33`), `gitRoot` (`:37-41`), `findCharter` (`:44-81`), `ensureWorktreeIgnored` (`:90-105`), `cmdUp` (`:110-127`), `cmdDown` (`:129-154`), `cmdTeamStatus` (`:156-161`). Types `Coder` (`:20-24`) and `Charter` (`:26-31`).
- `list.ts` and `current.ts` are read-only views (`list.ts:10-25`, `current.ts:10-14`).
- `help.ts` is one constant (`:6-59`). Its text is kept by hand next to README and CHEATSHEET; no generator exists in the repo.
- `index.ts`: `parseFlags` (`:27-37`) reads `--account N` or `--account=N`; the first non-flag argument is the charter path.

## 4. Data flow of `up`

### 4.1 Charter parsing (`findCharter`, `team.ts:44-81`)

A regex parser. No YAML library is used.

- Discovery with no path: the first `.yaml` or `.yml` that `readdirSync` returns for `<git root>/ψ/teams` (`team.ts:47-51`). The list is not sorted. Other files are ignored without a message.
- Top-level keys: `name` (`:63`; parsed, then never read); `session` (`:64`; missing gives an empty string, not an error); `default_account` (`:67`) or `default_engine` (`:68`).
- Coders: the file is split on `/^\s*- role:/m` (`:71`). Per block: `role` (`:72`), `slug` from the first `name:` anywhere in the block (`:73`), `engine` (`:74`), `worktree` (`:75`). A block is skipped when role is `lead`, worktree is absent, or worktree is `false` or `~` (`:76`).
- Account per coder (`:77`): digits from `(omx|codex)-N` in engine, else the charter default, else `"1"`.
- Never read: `members`, `project`, `branch`, `prompt` (`templates/team.yaml:9, 17, 29, 30-34`; grep finds no reader).
- Trailing comments are kept. Each value is `(.+)` to end of line with no comment stripping (`:63-75`). `templates/team.yaml:10` is `session: 90-myproject          # tmux session (...)`, so the parsed session would contain the comment text. That string then goes into the kill target (`:137`) and the summary (`:125`). Not executed.

### 4.2 Per-coder sequence (`cmdUp`, `team.ts:110-127`)

0. Repo root: `git rev-parse --show-toplevel`, run in PWD (`:37-41`). If that fails, the root silently becomes PWD (`:40`).
1. Once per run: append `# maw codex worktrees` and `agents/` to `<root>/.git/info/exclude` (`:91`, `:98`, `:100`). Errors are swallowed (`:102-103`).
2. Account = `--account` override, else the coder's account (`:116`).
3. `maw worktree add <slug> --base main`, cwd = root (`:118`). Result ignored. `--base main` is hard-coded.
4. `cmdUse(account, <root>/<worktree>)` (`:119-120`):
   a. The account must be a numeric directory under ~/.codex-team (`use.ts:26`; `lib.ts:60-73`). If not, return `ok:false` before any write (`use.ts:27`).
   b. Rewrite `<dir>/.envrc` (`use.ts:30-32`): drop old CODEX_HOME lines, keep the others, append `export CODEX_HOME="$HOME/.codex-team/<N>"` (`lib.ts:117-134`).
   c. `direnv allow <dir>` (`use.ts:35`). Nothing passes `skipDirenv=true` (`team.ts:120`, `index.ts:41`).
   d. `ensureCodexTrust` (`use.ts:38`; `lib.ts:98-110`): if `~/.codex-team/<N>/config.toml` exists and lacks `"<abs>"`, append `[projects."<abs>"]` and `trust_level = "trusted"`.
5. Only `!ok` is reported (`:121`). The direnv and trust outcomes are dropped.
6. `maw work . --wt <slug> -e "direnv exec . omx --yolo --direct"`, cwd = root (`:122`). "up" is printed when `maw work` exits 0 (`:123`). Nothing checks that codex booted.
7. Summary "N coders up in <session>" (`:125`), printed whatever happened above.

### 4.3 Files and directories written

- `<root>/.git/info/exclude`: one block appended (`team.ts:100`). This is inside the user's git dir.
- `<root>/<worktree>/.envrc`, one per coder (`use.ts:32`). It stays out of git only because the worktree path is under `agents/`, which is hard-coded (`team.ts:100`). A worktree path outside `agents/` is not excluded.
- `~/.codex-team/<N>/config.toml`: append only (`lib.ts:108`).
- Made by maw, not by plugin code: the git worktree and its branch (`team.ts:118`; path and branch name not in source), and the tmux window (`team.ts:122`).
- Made by direnv: its own allow record for the `.envrc` (`use.ts:35`; not in source).
- Not touched: `~/.codex-team/<N>/auth.json` (never read or checked; grep).

### 4.4 Exact command that starts the coder

```
plugin call (team.ts:122, cwd = repo root):  maw work . --wt <slug> -e "direnv exec . omx --yolo --direct"
engine run in the window (team.ts:33):       direnv exec . omx --yolo --direct
```

- Flags present: `--yolo` and `--direct`. Absent: any sandbox flag, any approval-policy flag, any config override. CODEX_HOME is not in argv; it comes from the worktree `.envrc` through direnv (`lib.ts:118`).
- `-e` is one argv element containing spaces (`team.ts:122`). How maw splits it: not found in source.
- `--yolo` is the only bypass-style flag in the repo. Its meaning is defined by omx (not found in source). `README.md:23` says it does not skip the trust prompt; the kit handles trust with the config.toml entry instead (`lib.ts:98-110`). `--direct`: not found in source.
- OMX_AUTO_UPDATE is not set by any code path (only `help.ts:57` and `CHEATSHEET.md:111` mention it).

Who does what:

- Plugin: charter parse, account choice, `.envrc`, the direnv allow call, the trust TOML, the exclude file, the engine string.
- maw: git worktree, tmux window, engine launch, window kill. How `--wt` sets the directory is not in source.
- direnv: approves `.envrc` (`use.ts:35`) and loads it for `direnv exec .` (`team.ts:33`).
- omx and codex: run codex, apply `--yolo` and `--direct`, read the trust entries (external).
- git: `rev-parse` (`team.ts:39`), `prune` (`:148`), `branch -d` (`:150`).
- tmux: not called by the plugin.

Approvals in `up`: three things pass without a prompt. The worktree `.envrc` is allowed (`use.ts:35`). Codex trust is seeded for the worktree path (`lib.ts:98-110`). The engine runs with `--yolo` (`team.ts:33`). `buildEnvrc` keeps every other line of an existing `.envrc` (`lib.ts:122-133`). If the repo tracks an `.envrc`, that content is what direnv allow approves.

### 4.5 Failure paths (from reading; not executed)

- Account missing or not numeric: `cmdUse` returns `ok:false` before writing (`use.ts:26-28`). `cmdUp` prints a warning (`team.ts:121`) and still runs `maw work` (`:122`). No new CODEX_HOME line is written, so a fresh worktree has none and the coder inherits the environment's CODEX_HOME, which is the default home unless set. A worktree that already has an old CODEX_HOME line keeps it. The summary still says the coders are up (`:125`). This is the shared-account trap the kit exists to prevent (`README.md:24`).
- Worktree directory missing (for example, `maw worktree add` failed and its result was ignored at `:118`): `writeFileSync` at `use.ts:32` throws ENOENT. Nothing catches it (`team.ts:110-127`; `index.ts:50-55`). The loop stops and earlier coders keep running.
- direnv allow fails: recorded as `direnvOk=false` (`use.ts:35`) and not checked by `cmdUp` (`team.ts:120-121`). The engine then runs against an unapproved `.envrc` (direnv behaviour; not in source).
- Trust file missing: `ensureCodexTrust` returns false with no message (`lib.ts:103-105`). The coder meets the trust prompt that `README.md:22-23` describes.
- Not in a git repo: the root falls back to PWD (`team.ts:40`), and the steps run against that directory.

### 4.6 Explicit path arguments ignore the caller directory

Defaults use `callerDir()` (`lib.ts:25-27`). Explicit arguments do not: the charter path (`index.ts:52` -> `team.ts:45`, `:58`); the dir for `use` (`use.ts:22`, `:30`, `:35`, and `resolve(dir)` at `lib.ts:99`); and the dir for `list` and `current` (`list.ts:10-14`, `current.ts:10-11`). Those resolve against `process.cwd()`, which `lib.ts:19-24` says is the plugin dir under maw. This is a reading, not a test. Commit `b526f35` changed only `team.ts` (`git log --name-status`); `use.ts`, `list.ts`, `current.ts` and `lib.ts` are unchanged since `45fc500`.

## 5. Data flow of `down` and `status`

`down` (`cmdDown`, `team.ts:129-154`):

- Charter as in 4.1. `repo = basename(gitRoot())` (`:130-131`).
- Phase 1, per coder (`:135-146`): `maw kill <session>:<repo>-<slug>` (`:137`), result ignored. If `<root>/<worktree>` exists (`:139`), `renameSync` it to `/tmp/wt-<slug>-<pid>` (`:141`). Errors are reported (`:142-143`). The `/tmp` path is hard-coded.
- Phase 2 (`:148-151`): `git worktree prune`, then `git branch -d agents/<slug>` per coder (`:150`). Results ignored. `-d` refuses unmerged branches (git behaviour).
- Summary (`:152`) says worktrees, branches and windows are cleared. It prints whatever happened above.
- Effects: directories are moved to /tmp and left there (no `rm` in plugin/src). Branches go only through `-d`. Prune clears git's worktree metadata. `.git/info/exclude` keeps its `agents/` line (no removal path). ~/.codex-team is untouched. The lead window is never killed (the lead has no worktree, `:76`).

`status` (`cmdTeamStatus`, `team.ts:156-161`):

- `maw worktree ls` with cwd = `callerDir()` (`:157`). A non-zero exit gives "no worktrees" (`:158`).
- Keeps lines matching `/codex|agents\//` (`:159`). None gives "(no codex worktrees)" (`:160`).
- Read-only: no charter, git, tmux or writes. It does not check for live processes, although `README.md:9` says "list live coders".

## 6. External dependencies

Runtime tools (looked up on PATH):

- `bun`: runtime and build (`lib.ts:42`; `package.json:7`).
- `maw`: `team.ts:118`, `:122`, `:137`, `:157`.
- `git`: `rev-parse` (`team.ts:39`), `worktree prune` (`:148`), `branch -d` (`:150`).
- `direnv`: `allow` (`use.ts:35`); `exec` in the engine line (`team.ts:33`).
- `ls`: `listAccounts` (`lib.ts:61`), a subprocess rather than `fs.readdir`.
- `omx`: named only in `team.ts:33`; run by maw inside the window.
- `codex`: never invoked directly; named in a regex and comments (`lib.ts:85`, `team.ts:77`).

Runtime APIs and built-ins: fs, path, `os.homedir` (`lib.ts:13-17`); `Bun.spawnSync` (`lib.ts:42`); `process.env.PWD` (`lib.ts:26`); `process.argv` (`index.ts:23`); `process.pid` (`team.ts:141`).

npm: no runtime dependencies (`package.json:10-13` lists devDependencies only).

- `@types/bun` "latest" (`package.json:11`), locked at 1.3.14 (`bun.lock:13`).
- `typescript` "^5.6.0" (`package.json:12`), locked at 5.9.3 (`bun.lock:19`).
- Transitive: `bun-types` 1.3.14 (`bun.lock:17`), `@types/node` 26.1.0 (`bun.lock:15`), `undici-types` 8.3.0 (`bun.lock:21`).

Files: `~/.codex-team` (`ls`, `lib.ts:61`); `~/.codex-team/<N>/config.toml` (read `lib.ts:100-104`, appended `lib.ts:108`); `<root>/.git/info/exclude` (`team.ts:91`); `<root>/<worktree>/.envrc` (`use.ts:30-32`); `/tmp` (`team.ts:141`). The `~/.maw/plugins/codex` symlink is made by the user (`README.md:41`), not by code.

## 7. README vs code

Format: claim (where) -> code (where). Only claims that do not match, or that the source cannot confirm, are listed.

1. "spawn the whole team from ψ/teams/*.yaml" (`README.md:8`, `:80`) -> one charter only, the first `.yaml` or `.yml` from unsorted readdir (`team.ts:49-51`). The rest are ignored.
2. maw-rs is the requirement (`README.md:47`) -> plain `maw` on PATH, no version check, no sdk import (`team.ts:118-157`; `plugin.json:7` is never read).
3. Usage `<use|list|current|up|down|status>` (`README.md:44`; `CHEATSHEET.md:14`) -> `index.ts:71` also lists `help` and `[args]`. Minor.
4. "use seeds trust, so new worktrees boot silently" (`README.md:109-111`; `CHEATSHEET.md:97`) -> the write is at `lib.ts:108`, but a missing config.toml is skipped silently (`lib.ts:103-105`) and `up` does not report it (`team.ts:120-121`). The trust prompt itself, "boot silently", and "omx --yolo does not skip it" (`README.md:22-23`) are codex or omx behaviour (not found in source).
5. Accounts each have `auth.json` and `config.toml` (`README.md:48-49`) -> only the directory name is checked (`lib.ts:60-73`); `auth.json` is never read; `config.toml` matters only for trust.
6. Precedence table (`README.md:140-149`) -> matches `team.ts:77`, `:116`, `:66-68`. Undocumented: `default_engine: omx-N` (`team.ts:68`) and `codex-N` in engine (`team.ts:77`).
7. "Accounts N=1..10" (`CHEATSHEET.md:112`) -> any all-digit directory name (`lib.ts:66`).
8. Status shows "worktree + branch + session" (`CHEATSHEET.md:42`) and "list live coders" (`README.md:9`) -> filters `maw worktree ls` text (`team.ts:157-160`). No branch or session query; no liveness check.
9. `down` "drops" the worktree (`CHEATSHEET.md:43`; `index.ts:11`) -> the directory is moved to /tmp (`team.ts:139-141`) and never removed. `README.md:121` ("move worktree to /tmp") is accurate.
10. `down` prints success (`team.ts:152`) -> kill and branch -d results are ignored (`team.ts:137`, `:150`).
11. Header says `down` runs `maw kill <repo>-<slug>` (`team.ts:7`) -> the code passes `<session>:<repo>-<slug>` (`team.ts:137`).
12. `maw team send myproject-team` (`CHEATSHEET.md:69`) -> the kit never creates or calls a maw team (no "maw team" in plugin/src). `name` is parsed (`team.ts:63`) and unused.
13. Charter `prompt:` blocks (`templates/team.yaml:30-34`, `:41-43`) and "dispatch tasks with maw hey" (`README.md:82`) -> the prompt is never read, so `up` sends no task. Dispatch is manual (`FIELD-REPORTS.md:51` agrees).
14. Charter `branch:` (`templates/team.yaml:29`) -> not read; the branch is hard-coded as `agents/<slug>` (`team.ts:150`).
15. Window = `<repo>-<slug>` (`CHEATSHEET.md:56`) with the template name `myproject-codex-parser` (`templates/team.yaml:26`; `README.md:68`) -> per the code, slug is the full name (`team.ts:73`) and the window is `myproject-myproject-codex-parser` (`team.ts:137`). `CHEATSHEET.md:60` and `:66` show `myproject-codex-parser`. Both cannot hold. maw's real naming is not in source.
16. Worktree is branched from main (`README.md:131-132`) -> `--base main` is hard-coded (`team.ts:118`). Not configurable; no other default branch is handled.
17. "OMX_AUTO_UPDATE=0" is required (`CHEATSHEET.md:111`; `help.ts:57`) -> never set by code. It is a prerequisite only.
18. `maw work -e omx` resolves to `omx --yolo --direct` with no CODEX_HOME (`README.md:104-107`) -> maw behaviour; not in source. The kit passes the full string itself (`team.ts:33`).
19. "Plugin reads PWD, fixed" (`CHEATSHEET.md:102`) -> true for defaults (`lib.ts:26`); explicit arguments bypass it (section 4.6).
20. Window naming `<repo>-<slug>` (`README.md:113-117`; `help.ts:42-44`; `CHEATSHEET.md:56`) -> the code depends on it (`team.ts:137`); maw's naming is not in source.
21. Field reports: 3/3 verbs (`FIELD-REPORTS.md:16-17`), "first try" (`:32`), 4-6 min per coder (`:33`), live URL (`:34`), 0 merge conflicts (`:42`, `:56-57`), 5-coder run (`README.md:13`) -> external run reports; not found in source.
22. `maw team up` can delete worktrees, "bug #258" (`README.md:123-124`; `CHEATSHEET.md:101`) -> not found in source; the kit does not call `maw team up`.
23. Other unconfirmed claims: `MAW_WS_CAPTURE_INTERVAL_MS` (`CHEATSHEET.md:91`); "mirrors maw token use" (`README.md:90`; `help.ts:9`); "already global on m5" (`CHEATSHEET.md:17`) -> not found in source.
24. Layout (`README.md:155-163`) omits `index.ts`, `help.ts`, `docs/` and `LICENSE`. Minor.

# CODE-SNIPPETS: maw-codex-team-kit

Source: `/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/maw-codex-team-kit`, HEAD `397db8b` (2026-07-06; 8 commits; 18 tracked files). Every file cited is byte-identical to HEAD. Read-only: nothing was built, installed or run.

Each captioned code block was checked line-by-line against its caption's line range, so it is verbatim. Single-line quotes are verbatim with leading indentation removed. Bullet refs are relative to the repo root. "Not found in source" means the repo does not show it.

## 1. Entry point and verb dispatch

**`/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/maw-codex-team-kit/plugin/src/index.ts:39-72`**

```ts
switch (verb) {
  case "use":
    console.log(formatUse(cmdUse(rest[0]!, rest[1])));
    break;
  case "list":
  case "ls":
    console.log(cmdList(rest[0]));
    break;
  case "current":
    console.log(cmdCurrent(rest[0]));
    break;
  case "up": {
    const { charter, account } = parseFlags(rest);
    const c = findCharter(charter);
    console.log(c ? cmdUp(c, account) : NO_CHARTER);
    break;
  }
  case "down": {
    const { charter } = parseFlags(rest);
    const c = findCharter(charter);
    console.log(c ? cmdDown(c) : NO_CHARTER);
    break;
  }
  case "status":
    console.log(cmdTeamStatus());
    break;
  case "help":
  case "--help":
  case "-h":
    console.log(HELP);
    break;
  default:
    console.log("usage: maw codex <use|list|current|up|down|status|help> [args]\n\nrun `maw codex help` for the full reference.");
}
```

Each verb is one `case` in this top-level switch, which runs when the file executes; unknown verbs reach the usage line at `plugin/src/index.ts:71`.

- Manifest (`plugin/plugin.json:9`, `:11`): `"entry": "./dist/index.js",` and `"command": "codex",`.
- The file exports nothing and has no `import.meta.main` guard, so the switch also runs on import. Argument split: `const [verb, ...rest] = process.argv.slice(2);`
- `up` and `down` share `parseFlags` (`plugin/src/index.ts:27-37`); its `--account` branch is `if (a === "--account") account = args[++i];`
- Charter with no path: `file = join(teamsDir, yamls[0]);` takes the first file from an unsorted `readdirSync` (`plugin/src/team.ts:49-51`).
- Relative `use`, `list`, `current` and charter paths reach Node fs as typed. `plugin/src/lib.ts:19-24` says maw runs plugins with cwd set to the plugin directory, so they would resolve there (reading only; not run).

## 2. Coder launch command

**`/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/maw-codex-team-kit/plugin/src/team.ts:33-33`**

```ts
const ENGINE_CMD = "direnv exec . omx --yolo --direct";
```

The launch string is a constant; no charter field or CLI flag changes it.

- Handed to maw at `plugin/src/team.ts:122`: `const w = run(["maw", "work", ".", "--wt", c.slug, "-e", ENGINE_CMD], { cwd: root });`
- `direnv exec .` loads the `.envrc` of the directory it runs in, so `CODEX_HOME` is set before omx starts. The README gives this reason at `README.md:104-107` (a claim, not code). That the window runs in the worktree is not found in source. `--yolo` and `--direct` are omx flags; their behaviour is not found in source. The binary is `omx`; `codex` is never launched.
- `--wt <slug>` and `-e` are `maw work` arguments; how maw runs the `-e` string or quotes `--wt` is not found in source.
- The charter `engine:` is read only for its account digits (`const account = engine.match(/(?:omx|codex)-(\d+)/)?.[1] ?? defaultAccount ?? "1";`). The Makefile repeats the command at `Makefile:10`.

## 3. up: worktree, .envrc, direnv allow, trust seed

Per coder, `cmdUp` runs `maw worktree add` (result discarded: `run(["maw", "worktree", "add", c.slug, "--base", "main"], { cwd: root });`), then `cmdUse`, then `maw work`. `cmdUse` writes the `.envrc`, runs `direnv allow` and seeds trust, in that order:

- `writeFileSync(envrcPath, buildEnvrc(existing, account));`
- `if (!skipDirenv) direnvOk = run(["direnv", "allow", dir]).ok;`
- `const trustSeeded = ensureCodexTrust(account, dir);`

**`/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/maw-codex-team-kit/plugin/src/lib.ts:98-110`**

```ts
export function ensureCodexTrust(account: string, dir: string): boolean {
  const abs = resolve(dir);
  const cfg = join(TEAM_ROOT, account, "config.toml");
  let toml: string;
  try {
    toml = readFileSync(cfg, "utf-8");
  } catch {
    return false;
  }
  if (toml.includes(`"${abs}"`)) return false;
  appendFileSync(cfg, `\n[projects."${abs}"]\ntrust_level = "trusted"\n`);
  return true;
}
```

`ensureCodexTrust` appends one trust table per worktree path to `~/.codex-team/<N>/config.toml` (`TEAM_ROOT` is `export const TEAM_ROOT = join(homedir(), ".codex-team");`) and skips paths already present.

The exact text appended at `plugin/src/lib.ts:108`, with a placeholder path. It begins with a blank line:

```toml

[projects."/path/to/repo/agents/myproject-codex-parser"]
trust_level = "trusted"
```

**`/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/maw-codex-team-kit/plugin/src/lib.ts:118-118`**

```ts
  const line = `export CODEX_HOME="$HOME/.codex-team/${account}"`;
```

This is the one `.envrc` line that `buildEnvrc` writes for the account.

- Older `CODEX_HOME=` lines are dropped first, whatever they pointed at (`return !s.startsWith("export CODEX_HOME=") && !s.startsWith("CODEX_HOME=");`). Other lines are kept, and `direnv allow` then approves the whole file.
- The direnv result (`plugin/src/use.ts:35`, above) is recorded, and only the `use` verb prints it (`plugin/src/use.ts:45`). `up` checks only `u.ok` (`plugin/src/team.ts:121`), which is false only for a missing or unknown account (`plugin/src/use.ts:23-28`), so `up` never reports a direnv failure.
- A missing `config.toml` skips trust with no message (`plugin/src/lib.ts:102-106`); the append at line 108 has no try block.

## 4. Account / CODEX_HOME resolution and what use writes

**`/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/maw-codex-team-kit/plugin/src/team.ts:65-68`**

```ts
  // charter-level default: `default_account: 5` (or default_account from an omx-N engine)
  const defaultAccount =
    content.match(/^default_account:\s*(\d+)/m)?.[1] ??
    content.match(/^default_engine:\s*\S*?(?:omx|codex)-(\d+)/m)?.[1];
```

The charter default is read from `default_account:`, or from the digits of `default_engine:`.

Resolution, highest first: (1) CLI override, `const account = overrideAccount ?? c.account;`; (2) per-coder `omx-N` or `codex-N` digits, the first `??` in `const account = engine.match(/(?:omx|codex)-(\d+)/)?.[1] ?? defaultAccount ?? "1";`; (3) the charter default above; (4) fallback `"1"`, the last `??` in that same line. This matches `plugin/src/help.ts:24-28` and `README.md:140-149`. The comment at `plugin/src/team.ts:65` mentions "default_account from an omx-N engine", but the code reads `default_engine:`.

- `--account` accepts any string (`plugin/src/index.ts:32-33`). `cmdUse` checks it with `if (!accountExists(account)) {` (`plugin/src/use.ts:26`), which tests membership in a list kept by `.filter((s) => /^\d+$/.test(s))` (`plugin/src/lib.ts:66`). Plain files with digit names therefore pass too.
- `use`, `list` and `current` default `dir` to `callerDir()`, which reads `PWD`: `return process.env.PWD || process.cwd();`

## 5. How up keeps worktrees out of git

**`/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/maw-codex-team-kit/plugin/src/team.ts:90-105`**

```ts
function ensureWorktreeIgnored(root: string): boolean {
  const exclude = join(root, ".git", "info", "exclude");
  let content = "";
  try {
    content = readFileSync(exclude, "utf-8");
  } catch {
    /* may not exist yet — append creates it */
  }
  if (/^agents\/\s*$/m.test(content)) return false;
  try {
    appendFileSync(exclude, `${content && !content.endsWith("\n") ? "\n" : ""}# maw codex worktrees\nagents/\n`);
    return true;
  } catch {
    return false;
  }
}
```

`ensureWorktreeIgnored` appends `# maw codex worktrees` and `agents/` to `.git/info/exclude` unless an `agents/` line is already there.

- Written on separate lines, with a newline first if the file has content but no trailing newline (`plugin/src/team.ts:100`). Called once, from `cmdUp` (`if (ensureWorktreeIgnored(root)) out.push("✓ agents/ → .git/info/exclude (worktrees kept out of git)");`). `cmdDown` never removes these lines.
- Hard-coded to `agents/` (line 98), so a charter whose `worktree:` is elsewhere is not excluded.
- Silent: read errors are ignored (`plugin/src/team.ts:93-97`) and a failed append returns false (`plugin/src/team.ts:102-103`), so nothing is printed. Reading only: if `.git` is a file (a linked worktree), both calls fail silently.
- Added in commit `58f2642`.

## 6. down: teardown order and what it touches

**`/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/maw-codex-team-kit/plugin/src/team.ts:129-154`**

```ts
export function cmdDown(charter: Charter): string {
  const root = gitRoot();
  const repo = basename(root);
  const out: string[] = [];

  // phase 1: kill window + move worktree out (untracked/dirty files can't block a move)
  for (const c of charter.coders) {
    out.push(`⬇ ${c.slug}`);
    run(["maw", "kill", `${charter.session}:${repo}-${c.slug}`], { cwd: root });
    const wt = join(root, c.worktree);
    if (existsSync(wt)) {
      try {
        renameSync(wt, join("/tmp", `wt-${c.slug}-${process.pid}`));
      } catch (e) {
        out.push(`  ⚠ move failed: ${String(e)}`);
      }
    }
  }
  // phase 2: prune BEFORE branch delete (git refuses to delete a still-registered worktree branch)
  run(["git", "worktree", "prune"], { cwd: root });
  for (const c of charter.coders) {
    run(["git", "branch", "-d", `agents/${c.slug}`], { cwd: root });
  }
  out.push(`\n✅ team down — worktrees + branches + windows cleared`);
  return out.join("\n");
}
```

`cmdDown` kills each window, renames each worktree into `/tmp`, prunes worktree records, and runs `git branch -d` on each `agents/<slug>` branch, ignoring most results.

- The move (`plugin/src/team.ts:141`) is a rename to `/tmp/wt-<slug>-<pid>`, not a delete; the source has no `rm`, `-D`, `--force`, `reset` or `clean` (grep over `plugin/src`). The new location is never printed.
- Prune (`plugin/src/team.ts:148`) runs repo-wide, so it also clears other stale worktree records. `-d` (`plugin/src/team.ts:150`) refuses unmerged work, but its result is discarded, so the branch stays with no message.
- The closing line (`plugin/src/team.ts:152`) reports "worktrees + branches + windows cleared" whatever happened.
- Charter path (`plugin/src/team.ts:75`, `:138`) has no containment check. `worktree: .` resolves to the repo root and `worktree: ..` to its parent, so `down` would rename them to `/tmp` (reading only; not run).
- `session` keeps trailing comments (`plugin/src/team.ts:64`), so a template copied with its line-10 comment gives a kill target that cannot match a real session, and the failure is hidden (topic 9). `config.toml` trust entries are never removed.

## 7. Error handling: swallowed, silently continued, retried

Retries: none. The blank-line trim `while (kept.length > 0 && kept[kept.length - 1].trim() === "") kept.pop();` is a loop, not a retry.

- lib.ts: `ok: proc.exitCode === 0,` is the only success test; `run()` never throws on a non-zero exit, and `Bun.spawnSync` (`plugin/src/lib.ts:42`) is not wrapped (whether a missing binary throws is not verified here). `if (!r.ok) return [];` turns a failed `ls` into an empty account list. `} catch {` then `return false;` (`plugin/src/lib.ts:104-105`) ignores a missing or unreadable `config.toml`.
- team.ts: `return r.ok ? r.stdout.trim() : cwd;` silently makes the caller directory the root. `return null;` at `plugin/src/team.ts:53` and `:60` turns an unreadable charter or `ψ/teams` folder into "no charter found" (`plugin/src/index.ts:24`), even for an explicit path that exists. `const session = content.match(/^session:\s*(.+)$/m)?.[1]?.trim() ?? "";` gives an empty session when `session:` is missing. `const slug = block.match(/name:\s*(.+)/)?.[1]?.trim() ?? "";` and `const account = engine.match(/(?:omx|codex)-(\d+)/)?.[1] ?? defaultAccount ?? "1";` silently default the slug and the account. `/* may not exist yet — append creates it */` ignores read errors on purpose.
- team.ts, up: `plugin/src/team.ts:118` discards the `maw worktree add` result, and `plugin/src/team.ts:121` reads only `u.ok`. `plugin/src/team.ts:122` runs the engine even when account setup failed, and the summary at line 125 counts every coder. team.ts, down: lines 137, 148 and 150 discard the kill, prune and branch results, and lines 142-143 log a failed move and carry on. team.ts, status: `if (!r.ok) return "no worktrees";` reads any `maw worktree ls` failure as "no worktrees".
- use.ts: `if (!skipDirenv) direnvOk = run(["direnv", "allow", dir]).ok;` records a failed approval, and only `use` reports it. `export function cmdUse(account: string, dir: string = callerDir(), skipDirenv = false): UseResult {` declares `skipDirenv`, which no caller passes, so it is dead. `writeFileSync(envrcPath, buildEnvrc(existing, account));` has no try: if `<dir>` does not exist it throws. In `up` that happens when `maw worktree add` created nothing (`plugin/src/team.ts:118`). The exception leaves `cmdUp` (`plugin/src/index.ts:53` has no catch), so the summary is never printed, and nothing rolls back the coders already started.
- index.ts: `if (a === "--account") account = args[++i];` silently ignores a `--account` with no value. `console.log(c ? cmdUp(c, account) : NO_CHARTER);` has no try, and neither does the `down` call at `plugin/src/index.ts:59`.

## 8. Shell-outs built from user or charter input

- No shell runs: every subprocess goes through `Bun.spawnSync(cmd, {` (`plugin/src/lib.ts:42`) with an argv array. A grep over `plugin/src` finds no `sh -c`, `execSync`, Bun shell tag or `child_process`; the one `.exec(` hit is a RegExp at `plugin/src/lib.ts:85`.
- No shell quoting or escaping is applied, because argv elements are passed unparsed. The values still reach tools whose handling is not in this repo (not found in source): the kill call ``run(["maw", "kill", `${charter.session}:${repo}-${c.slug}`], { cwd: root });`` (`plugin/src/team.ts:137`); `ENGINE_CMD` (`plugin/src/team.ts:33`), a constant with spaces, passed as `-e` (`plugin/src/team.ts:122`); and `c.slug` as `--wt` (`plugin/src/team.ts:122`).
- Files read later by a shell or parser: `.envrc` (`plugin/src/lib.ts:118`, topic 3) is safe only because `account` must match an existing digit-only name (`plugin/src/use.ts:26`, `plugin/src/lib.ts:66`), and direnv then evaluates it as shell, kept lines included. `config.toml` (`plugin/src/lib.ts:108`) takes the path inside `[projects."..."]` unescaped, so a double quote in the path yields invalid TOML.
- Charter-driven destination with no validation (`plugin/src/team.ts:141`):

**`/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/maw-codex-team-kit/plugin/src/team.ts:141-141`**

```ts
        renameSync(wt, join("/tmp", `wt-${c.slug}-${process.pid}`));
```

A slug with several `..` segments (for example `../../../x`) can point this destination outside `/tmp` (reading only; not run).

## 9. Charter template (templates/team.yaml), in full

**`/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/maw-codex-team-kit/templates/team.yaml:1-43`**

```yaml
# <team-name> — codex coder team charter
#
# Drives `maw codex up|down|status`. One coder per task, each pinned to its own
# codex account (~/.codex-team/<N>) so they don't share a rate-limit.
#
# Copy this to ψ/teams/<team>.yaml (or anywhere) and edit.

name: myproject-team           # team label
project: your-org/your-repo    # GitHub slug
session: 90-myproject          # tmux session (usually <NN>-<repo-basename>)

# Optional: put every coder on ONE account unless it sets its own `engine: omx-N`.
# Account resolution (highest wins): `maw codex up --account N` > per-coder omx-N
# > this default_account > 1. Uncomment to run the whole team on one account:
# default_account: 5

members:
  # The lead is you (this window). Do NOT give it a worktree — omitting the
  # field keeps it out of the coder loop.
  - role: lead
    name: myproject
    engine: claude

  # Each coder: name = worktree slug, engine = omx-<N> picks account N.
  - role: parser
    name: myproject-codex-parser
    engine: omx-1                          # → CODEX_HOME=~/.codex-team/1
    worktree: agents/myproject-codex-parser
    branch: agents/myproject-codex-parser
    prompt: |
      Coder myproject-codex-parser — TASK: <one task>.
      Build gate: <your test/lint command> green. Own branch+worktree off main.
      PR/merge → main (lead-gated). Report ACK→blocked→done to lead
      (maw hey 90-myproject:myproject via the lead window).

  - role: writer
    name: myproject-codex-writer
    engine: omx-2                          # a DIFFERENT account = isolated quota
    worktree: agents/myproject-codex-writer
    branch: agents/myproject-codex-writer
    prompt: |
      Coder myproject-codex-writer — TASK: <one task>. Build gate green.
      Never touch other worktrees. PR/merge → main. Report to lead.
```

The parser reads this file with regexes, not a YAML library (`plugin/src/team.ts:63-79`).

- Read: top-level `name:` (unused by the output), `session:`, `default_account:` (line 15 is commented out, so ignored), `default_engine:`; per coder `role:`, `name:`, `engine:`, `worktree:`.
- Ignored: `project:` (line 9), `branch:` (lines 29 and 40), and both `prompt:` blocks (lines 30-34 and 41-43). No code sends a prompt; dispatch is manual (`plugin/src/help.ts:42-47`).
- Trailing comments stay in values, since the regexes run to end of line (`plugin/src/team.ts:63-64`, `:74-75`). Line 10 therefore gives a `session` that includes its comment; a comment after `worktree:` or `name:` would join the path or slug. The line 27 comment is harmless, because only the `omx-N` digits are kept.
- The lead is skipped by `role === "lead"` or by having no worktree (`plugin/src/team.ts:76`).

## Notes outside the nine topics

- `plugin/src/help.ts:57` lists `env: OMX_AUTO_UPDATE=0`; nothing in the source sets or reads it.
- `README.md:123-124` warns that `maw team up` can misparse a mixed charter and delete worktrees; that code is not in this repo.

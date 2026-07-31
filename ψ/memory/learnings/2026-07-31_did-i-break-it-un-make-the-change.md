# "Did I break it?" — un-make the change and re-run

**Discovered**: 2026-07-31, renaming this machine's maw node from `leica` to `mba`

Two verification failures happened back to back after a config change. One nearly caused a
correct change to be reverted. The other was settled in ninety seconds. The difference was
entirely method.

---

## The trap: a test that reads nothing from what you changed

After editing `~/.config/maw/maw.config.json`, every `maw route` query returned `not_found`.
That reads as *the rename broke routing — revert.*

It was noise. `maw route` is a **pure planner**: it takes every input as a CLI flag
(`--node`, `--agent`, `--session`, `--window <index:name:true|false>`) and reads **nothing**
from disk. Run bare, it returns `not_found` whether the real config is perfect or absent.
Supplied with flags matching the real config, everything resolved:

```
route vets-hub-oracle   -> local 11-vets-hub:1
route mba:11-vets-hub   -> self-node
route local:vets-hub    -> self-node
route leica:11-vets-hub -> unknown_node        (correct: the old name is gone)
```

**A failing test is not evidence until you know the test reads what you changed.**

The tell was available before reading any source: the *old* name failed too. A broken rename
leaves the old name working. When both the old and new value fail identically, the instrument
is the suspect, not the change.

Real verification came from commands that do read config: `maw federation status`
(`● mba (local) online`) and `maw locate <agent>` (`node: mba (this node)`).

---

## The technique: revert, re-run, restore

Minutes later `maw hey --inbox` failed. Instead of reasoning about whether the rename could
plausibly cause it:

```bash
cp config config.new            # keep the change
cp config.backup config         # un-make it
maw hey <agent> "..." --inbox   # identical failure  -> pre-existing
cp config.new config            # put it back
```

Ninety seconds, and blame was apportioned with evidence rather than argument. The failure was
pre-existing and unrelated.

**When a change is followed by a failure, un-make the change and re-run.** This is cheaper
than reading code, cheaper than reasoning, and it produces an answer rather than an opinion.
It requires only that you took a backup — which is a reason to always take one.

A positive control turned out to matter here too: `maw hey --inbox` failed for **every**
agent, including the node's own oracle, while `maw locate <agent> --path` resolved the same
agents to real repo paths. Two resolvers that should agree, disagreeing — an upstream bug,
not a local misconfiguration.

---

## Search for the artefact, not the mechanism

The first instinct was to grep the source for a format string that would emit `[node:agent]`.
That found nothing, because the prefix is not built by a format literal — it is a stored
field copied into message frontmatter.

Grepping for the **literal string that appears in the output** found real messages
immediately and answered the entire question:

```
---
from: leica:pops-vet
to: pawrent
---
[leica:pops-vet] From pops-vet-oracle: ...
```

`<node>:<agent>`. Not the sender — the machine. Every oracle on one laptop shares it.

**Look for where a thing *is*, before looking for where it is *made*.**

---

## Two structural lessons from the config itself

**Layered config: every layer must agree, and the higher layer may hold more.** There were
two files — a base and a `.50` layer. Both carried the node name, and the `.50` layer had
*more* agent entries than the base (32 vs 23). Editing only the first file found would have
been a silent half-change.

**A routing table's values should not be a name that can be renamed.** The table mapped each
agent to the node it lives on, and every value was the literal node name — so renaming the
node orphans every entry. The routing spec exposes `selfAliases: ["configured-node",
"local"]`, meaning the literal string `local` is treated identically to the configured name.
Setting the values to `local` makes the table rename-proof.

Also worth knowing: that table is consulted **last** in the precedence chain, after local
tmux window lookup. On a single-machine setup it barely runs. It earns its keep the day a
second machine joins and a message has to decide whether to cross the network.

---

## "Does anything need restarting?" is one question per stateful layer

Not a yes/no. Answer each layer with evidence:

| layer | holds config? | how it was checked |
|---|---|---|
| CLI | no — re-reads per invocation | already reported the new name with nothing restarted |
| agent sessions | no — never read it; they shell out to the CLI | so they pick up changes for free |
| daemon | loaded at startup, but irrelevant here | served HTML contained neither the old nor the new name; every data endpoint 404 |

Answer: nothing needed restarting. Reached by checking three things, not by assuming one.

Related: [[2026-07-30_five-ways-a-secret-scan-lies]] — the same underlying discipline, applied
to measurement instead of to change.

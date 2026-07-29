# Five ways a secret scan lies — and the control that catches each

**Discovered**: 2026-07-30 (session 2026-07-29 17:00 → 2026-07-30 06:04)
**Context**: A checklist said *20 credentials pending rotation*. Verified figure: **32
needing action, 24 already closed, ~30 that were never credentials.** The count moved four
times, in both directions.

> This repo is public. No credential map here — no hashes mapped to systems, no file
> locations. Method only. The map lives in `~/security/` (700/600, outside git).

---

## The root error

The original scan matched exactly six shapes: `glpat-`, `sk-ant-oat`, `sk-ant-api`,
`gh[pous]_`, `root:<32hex>`, and `postgres://` URIs. It reported 20 matches. Everyone,
including me, read that as *20 credentials*.

**A scan's coverage is a property of its pattern list, never of its result.** The clearest
proof: in the same `kubectl create secret` command where the scan caught a postgres
password, a `JWT_SECRET` sat one line away and was never counted. Re-scanning for other
shapes found 14 live Discord bot tokens — an entire bot fleet — plus LINE tokens, auth
signing secrets, and API keys.

---

## Lie 1 — "It's already dead" (unproven negative)

Six leaked GitLab PATs each returned `401`. That reads as *already revoked, nothing to do*.
But a 401 cannot distinguish *revoked token* from *request that never authenticates at all*.

**Control:** run a **known-live credential of the same type** through the identical path. If
it doesn't succeed, the negative result is not evidence — it's a broken instrument.

The first attempt at a control failed: the only live credential to hand was a password, not
a PAT, and the API accepts only PATs. Correct response was to report *inconclusive* and
default to rotating all six. Hours later a live PAT turned up in `pass`, referenced from a
`.envrc` already read but not noticed. It returned 200; a fabricated token returned 401; the
method was proven and the six really were revoked.

**Two lessons, not one.** The discipline was right — but the pessimistic branch was not the
true one. Verification converts a guess into a fact; it does not make the scary answer
correct. And **the control is usually already on the machine** — in `pass`, in a `.envrc`,
in a config skimmed an hour ago. Look for it before paying for the expensive branch.

**Asymmetry worth remembering:** a *positive* result is self-proving. Only a valid key gets
a 200. Controls are needed for absence, not presence.

---

## Lie 2 — "It's reused everywhere" (substring illusion)

An 8-character leaked password appeared to be reused across **1,171 files**. The value was
the word `postgres`. Substring-matching a short dictionary word matches everything that
mentions the topic.

**Control:** before believing any reuse sweep, hash the value against a candidate list of
common words and dev defaults. Length ≤ 12 with low entropy means dictionary-check first.

The same finding closed a governance question in the other direction: the one hit in the
public repo turned out to have user, password and host all set to their defaults — user
`postgres`, password the same word, host `localhost`. The canonical dev default, not a
secret, so no history rewrite was needed.

*(Writing that URI out in full is what got the first attempt at this very file blocked by
the repo's own gitleaks pre-commit hook — correctly. The fix was to rephrase, not to
allowlist the fingerprint. Punching a hole in the guard to publish a document about not
punching holes in the guard would have cost more than the sentence was worth.)*

---

## Lie 3 — "This is a credential" (fixtures, constants, references)

Five distinct classes of thing that match secret patterns and are not secrets:

| class | example encountered |
|---|---|
| deliberate test fixtures | a fabricated `root:<32hex>` written to prove a pre-commit hook blocks — the transcript says so in its own words |
| vendor documentation placeholders | `AKIAIOSFODNN7EXAMPLE`, AWS's own doc example, picked up from a **third-party repo's** unit test |
| library constants | `cryptography`'s X.509 OIDs — `SUBJECT_KEY_IDENTIFIER`, `PRIVATE_KEY_USAGE_PERIOD`, `OID_KEY_USAGE` — and `inspect`'s `POSITIONAL_OR_KEYWORD`, ~17 in total, all from a virtualenv inside the scanned tree |
| identifiers, not secrets | localStorage key *names*, property-name constants, a `pass` store path prefix |
| references to secrets | `process.env.SUPABASE_SERVICE_ROLE_KEY`, and `${this.pass}` from a TypeScript template literal — `postgres://${this.user}:${this.pass}@...` looks exactly like a credentialed URI |

**Controls:** exclude `site-packages` and virtualenvs from the scan; filter values that
begin with a reference sigil (`process.env`, `$`, `${`, `{{`, `%VAR%`) **case-insensitively**
— a filter matching only `${UPPERCASE` let `${this.pass}` through as a phantom 12th postgres
password; and keep a deny-list of hashes proven non-secret, so the next run doesn't
re-litigate them.

**A scan that redacts library source is worse than one that misses.** The extended scrub
script was one `--apply` from rewriting installed `cryptography` files, removing zero
exposure while corrupting a working venv.

---

## Lie 4 — "The scan itself is inert"

A seventh `glpat-` appeared that wasn't in the original six. It was the **fabricated
negative control invented earlier in the same session** — written into the session
transcript by the act of testing, then found by the next scan as a genuine hit.

**Scanning for secrets creates secret-shaped strings.** Anything invented for a control goes
onto the deny-list the moment it's invented.

Worse, and self-inflicted: printing the context around one postgres password masked *that*
password and let the neighbouring `JWT_SECRET` and `AUTH_SECRET` out in full — into the same
transcript class under audit. **Redact the window, not the target:** mask every known value
in a printed neighbourhood before printing it.

---

## Lie 5 — "It's not in HEAD, so it's handled"

Three secrets were absent from their repo's current `HEAD` but present in history. A
classifier labelled them `LIKELY SUPERSEDED`.

**Deleting a line from a file does nothing to a password on a server.** A commit named
*"redact revoked …"* records an intention, not a verified revocation — and a prior handoff
stated in plain text that one of the three had never been rotated. It happened to be the
widest-blast-radius credential in the set: 71 occurrences, shared across four services.

**Control:** treat file-level absence as a *deployment* signal only. Liveness is a property
of the server, and only the server can answer it.

---

## Signals that actually decide it

None of these needs cluster access:

| signal | what it establishes |
|---|---|
| asked its own issuer, got 200 | **live** — self-proving |
| asked its own issuer, got 401/400, *with a working positive control* | **dead** |
| present in a repo's current `HEAD` | **still shipped** — treat as live |
| in git history only | file no longer carries it — says nothing about the server |
| newest mtime of any file holding it | recency, and whether the inflow is ongoing |
| identifier decodes to a public ID | proves a token is real **without any network call** — a Discord bot token's first dot-segment is base64 of its own bot ID, so `pass show … \| cut -d. -f1 \| base64 -d` confirms the right token reached the right bot without ever displaying the secret |

---

## Beyond scanning: the inflow

Scrubbing is a one-time cleanup of a pipe that is still open. New secrets were arriving in
the scanned directory *during* the audit. The habits are the actual fix:

1. Never paste a secret into an agent prompt — that is how 14 bot tokens leaked, into files
   that are not version controlled and were not being scanned until now.
2. `.envrc` holds references, never values: `$(pass show ...)`.
3. Per-repo `.envrc` — **direnv loads only the nearest one and does not merge with
   parents**, so a home-level file is shadowed by every repo that has its own.
4. `.env.example` gets placeholders. Two real credentials were sitting in one.
5. Verify a stored secret by decoding its public identifier, never by printing it.
6. Re-scan periodically, and each time ask what the pattern list still cannot see.

## Meta

**Enumerate before you aggregate, when the number is the deliverable.** A summary figure
survived several turns carrying seventeen library constants and one self-fabricated token.
It was invisible in the aggregate and obvious the instant the list was printed.

Related: [[2026-07-29_release-vs-source-staleness-and-direnv-non-inheritance]]

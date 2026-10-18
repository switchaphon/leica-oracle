# Discord threads per tmux window - design

Date: 2026-10-17, updated 2026-10-18. Status: draft for Un's approval. First oracle: pops-vet.

This repo is public. The document names no Discord IDs and quotes no project content. Those live
in the oracle's own `.discord-state/`, which git ignores.

## Why

Each oracle runs as one tmux session with several windows, each window a Claude Code session on its
own task. The pops-vet bot relays all seven of its windows through one DM: a Claude session in the
bot window watches the others, summarises whatever they say into the DM, and types Un's answers back
when he prefixes them with a window number. Seven conversations in one chat are mixed together and
hard to follow, and on Discord mobile the relayed text breaks: lines wrap twice, and tables and
aligned layouts fall apart.

Un wants one Discord thread per window, under the oracle's own channel, where he talks to that window
directly and the text reads well on a phone.

## What Un decided

- Under the `#pops-vet` channel there is one thread per window of tmux session `04-pops-vet`, named
  `<window index>:<window name>`, for example `1:pops-vet`. The bot's own window gets no thread.
- The bot keeps the threads matching the real windows by itself: a new window gets a thread, and
  renaming or renumbering a window renames its thread. Threads follow the window's tmux id, not its
  number.
- A closed window's thread is archived, not deleted.
- No middleman. What Un writes in a thread goes into that window as written, and what the window
  writes goes into its thread. No AI summarises or rewrites anything on the way.
- If a window is busy when Un writes, the message waits and is delivered when the window is free.
  If the window is showing a choice (a permission or selection prompt), Un answers with the number.
- Only Un's messages are acted on, in `#pops-vet`, in its threads and in DM. Bots never talk to each
  other; there is no use case for it yet.
- The DM stays as a direct line to the bot.
- Messages in `#pops-vet` outside any thread go to the bot, with no @mention needed.
- In the shared channels that other oracle bots are in (`#meeting-room`, `#training-room`), the bot
  answers only when Un @mentions it. Otherwise it stays silent. When mentioned it may read the recent
  history of that channel for context.
- Nat loses DM access to this bot, because pops-vet's own allowlist names only Un.
- Only the bot window holds the bot token (decided 2026-10-18). Work windows stop logging in as the
  bot, so nothing marks Un's messages as seen while no bot is reading them.
- Formatting for mobile, chosen after test posts in thread `1:pops-vet`:
  - a table is sent twice, as an image to read and as cards to copy text from
  - an aligned layout (a mockup) is sent as an image
  - ordinary text is no longer wrapped in a code block
- The work starts with window 1 of pops-vet.

## Goals

1. Threads mirror the windows of one tmux session, kept in sync without Un's help.
2. Each window's messages reach its thread verbatim and readable on a phone.
3. Un's thread messages reach the right window verbatim, safely, even when it is busy.
4. The bot answers in its own channel and, on mention only, in shared channels.
5. Everything per oracle is configuration, so other oracles can follow without code changes.

## Non-goals

- Other oracles this round. The design must not stop them; their rollout is a later task.
- Fixing the global `DISCORD_STATE_DIR` for the other bots (see Current state). Only pops-vet moves.
- Forking or patching the Discord plugin.
- Changing how the windows write. They keep writing for the terminal; the bridge adapts the text.
- Remote controls beyond typing and choosing, such as interrupting a busy window. Possible later.

## Anti-goals

- An AI in the thread path. If a summary, a rewrite or a guessed routing ever appears, it is wrong.
- Lost history. Nothing in Discord gets deleted.
- Typing into a window that is busy, or whose input box already holds text Un typed at the Mac.
- The bot window acting on thread messages as well, so that one message is handled twice.
- Secrets leaving the machine in a post or inside a rendered image.
- Discord IDs or project content in this public repo.

## Current state (verified 2026-10-17)

- The Discord plugin is `claude-plugins-official/discord` 0.0.4. Its gate, in `server.ts`:
  - drops every message written by a bot
  - looks up a thread by its parent channel, so a thread inherits its parent's entry in
    `access.json`
  - checks a group's `allowFrom` before it checks mentions
  - counts as a mention: a direct @mention, a reply to one of the bot's messages, @everyone, and a
    role the bot holds (discord.js 14.25.1 `mentions.has`)
  - lets the outbound tools (reply, react, fetch) reach any channel listed in `groups`, whatever its
    `allowFrom`
- `~/.claude/settings.json` sets `env.DISCORD_STATE_DIR` to Leica's state directory. That value beats
  each repo's `.envrc`, so every bot on the machine reads Leica's `access.json`. Leica's list has no
  `#pops-vet`, which is why the pops-vet bot ignored Un's @mentions there this morning. Its transcript
  shows inbound messages only from the DM and `#training-room`.
- pops-vet's own `.discord-state/access.json` already lists `#pops-vet`, `#meeting-room` and
  `#training-room`. `#pops-vet` is the channel formerly named `#pops`; its ID is unchanged.
- Every Claude window in the pops-vet repo starts the plugin with the bot token that direnv loads
  from `.envrc`, so each one logs in as the pops-vet bot. Only the bot window, launched with
  `--channels`, shows inbound messages to its Claude session. The other windows still mark each
  message they receive before dropping it: typing, plus `ackReaction` when the `access.json` in use
  sets one. At 08:12 on 2026-10-17, Un's DMs got ✅ from windows 1 to 7 while no bot window was
  running (pops-vet memory `reference_discord-ack-is-not-a-read`). Any window started after a token
  rotation has the new token and does the same.
- `~/.claude/sessions/<pid>.json` maps each Claude process to its `sessionId`, its tmux position
  (`<session>:@<window id>.%<pane id>`) and, in newer versions, a busy/idle `status`. The transcript
  is `~/.claude/projects/<cwd with / replaced by ->/<sessionId>.jsonl` and holds the exact markdown
  the window wrote.
- The current relay, `relay.py` with `fmt.py`, lives in the bot window's session scratchpad, which is
  temporary. It has a working pane-state reader (busy, idle, prompt, usage limit, input box
  contents) and a safe send: paste through a tmux buffer with bracketed paste, press Enter, and only
  if the window is still idle at the same content with an empty input box.
- Already proven from the bot account: listing the guild's active threads, posting in a thread, and
  attaching a PNG.
- `.discord-state/` is git-ignored in both pops-vet-oracle and leica-oracle. Both
  `.claude/settings.json` and `.claude/settings.local.json` are tracked in pops-vet-oracle, which is
  private.
- Google Chrome is installed and renders a page to PNG headless. Pillow is not installed.
- The `pinentry-mac` program is missing on this machine. `pass` works only while gpg-agent still has
  the passphrase cached, so a bot restart can fail at the token step. This predates this work.

## Design

### 1. Pieces

```
tmux 04-pops-vet
  windows 1..7  Claude sessions doing the work
  window 8      the bot window
    pane A      claude --channels plugin:discord   (the bot: DM, main channel, shared channels)
    pane B      the thread bridge                  (threads, both directions)

Discord #pops-vet
  main channel  messages go to pane A (typed by the bridge); pane A answers with the plugin
  threads       1:pops-vet, 2:..., 7:...  one per window, handled only by the bridge
```

The thread bridge is a plain program with no AI in it. It talks to Discord over REST only, using the
bot's token from the environment, with no gateway connection. It reads tmux and the Claude session
files, types into windows through tmux, and posts to Discord.

### 2. Gate configuration (pops-vet's `access.json`)

- DM: `dmPolicy: allowlist`, `allowFrom: [Un]`.
- `#pops-vet`: `requireMention: false`, `allowFrom: [the bot's own user id]`. The plugin drops every
  bot-written message and nothing else matches that list, so the plugin delivers nothing from
  `#pops-vet` or any of its threads. The outbound tools still reach the channel, so the bot can reply
  there. This is how the bot window is kept from handling thread messages twice. Record the reason in
  the bridge config and in the bot-up skill, because `access.json` cannot carry a comment and the
  plugin drops unknown keys when it saves.
- `#meeting-room` and `#training-room`: `requireMention: true`, `allowFrom: [Un]`.

### 3. Thread sync

- Windows: every window of the configured tmux session except the bridge's own window, which it finds
  from `$TMUX_PANE`.
- Identity: the tmux window id (`@N`) together with the tmux server's start time. Window ids restart
  from `@0` when the tmux server restarts, so an id alone could point a thread at the wrong window
  after a reboot. The map from window to thread lives in the bridge state.
- After a tmux server restart, every saved mapping is closed and its thread archived, and the windows
  that come back get new threads. A thread is the life of one window, and a reboot ends them all.
- Name: `<index>:<name>`, cut to Discord's 100-character limit. tmux has `renumber-windows` on, so
  closing a window moves every later window down one number. Their threads get renamed; that is
  expected, not an error.
- A window with no thread: first look for a thread under the channel with exactly that name that the
  bridge has never mapped, active or archived, and adopt it. The two threads Un created by hand are
  adopted this way. Otherwise create a public thread with a 7-day auto-archive.
- Name changed: rename the thread. Discord allows few renames per channel in a short time, so
  debounce, honour `retry_after` on HTTP 429, and always apply the latest name, never a queue of old
  ones.
- Window gone: archive the thread (archive only, no lock) and mark the mapping closed. A closed
  mapping is never reused, even if a new window takes the same name.
- A new or adopted thread first gets the window's latest message, once, so it opens with context.

### 4. Window to thread

- Trigger: the pane-state reader (ported from `relay.py`) sees the window idle, at a prompt, or at a
  usage limit, with the same content on two polls in a row. The session file's `status` is a second
  signal where the Claude version writes it.
- Content when idle: read the window's transcript, found through its session file. Post everything
  the window said in the last turn: the assistant text blocks since the last human prompt, in order,
  without tool calls or tool output, and skipping sidechain (subagent) lines. If that runs past about
  6000 characters, post the final answer (the text after the last tool call) and attach the whole
  turn as a `.md` file.
- When the turn was started by Un typing at the Mac rather than from Discord, the post opens with a
  short quote of his prompt, so the thread reads as a conversation.
- Content at a prompt: the visible prompt lines from the pane (the question and the numbered
  options), under a subtext line saying it waits for a number.
- Content at a usage limit: the limit notice, once.
- Each post happens once. Idle posts are keyed by the transcript uuid of the last line included;
  prompt and limit posts by a hash of their lines.
- A window with no Claude session in it (a plain shell) keeps its thread, but nothing is posted from
  it or typed into it.

### 5. Thread to window

- Polling: list the guild's active threads, compare each mapped thread's `last_message_id` with the
  last one seen, and fetch only new messages. Messages from anyone but Un are ignored, and so are the
  bridge's own posts. On start the bridge records the current last ids and does not replay history.
- Text goes in as written. Bot mentions are stripped. When the message is a Discord reply, it opens
  with a one-line quote of the message replied to.
- Attachments are downloaded into the oracle's `.discord-state/inbox/` and their absolute paths are
  added on their own lines, so the window can open them. Windows ask Un for screenshots often.
- Delivery uses the safe send. The window must be idle, unchanged since it was read, and have an
  empty input box.
  - Busy, or text in the input box: react ⏳ and wait. When the window frees up, deliver, then swap
    ⏳ for ✅.
  - Several messages that arrive while waiting, or within a few seconds of each other, go in as one
    prompt, separated by blank lines.
  - At a prompt: a message that is only a number is pressed as that option. Anything else gets a
    short notice in the thread asking for the number.
- While a window works on a turn that came from Discord, the thread shows "typing".
- A message in an archived thread whose window is gone gets a short notice that the window is closed.
- Notices are posted by the bridge, short, in Thai, and free of the characters banned by Rule 7.

### 6. Main channel to the bot window

A message from Un in `#pops-vet` outside any thread is typed into pane A by the same safe send. It
uses the tag the plugin uses for live messages, so the bot treats it like any Discord message and
replies in the channel with the plugin's reply tool:

```
<channel source="discord" chat_id="..." message_id="..." user="..." user_id="..." ts="...">text</channel>
```

### 7. Formatting for Discord mobile

All of it is plain code. It works from the markdown in the transcript, not from the screen, so there
are no terminal line breaks to undo.

- Tables: render the table as an image (an HTML table in Discord's dark colours, Thai shaped by a
  proportional font, every column with a sensible minimum width), and send it with the text that comes
  before the table. Then send the same rows as cards:

  ```
  **<first column>**            (a short first cell becomes "<header> <cell>", for example "ขั้น 1")
  - <header 2>: <cell>
  - <header 3>: <cell>
  ```

- Aligned layouts: an unlabelled code fence holding a layout (two or more spaces inside its lines)
  becomes an image. Each run of text is pinned to its terminal column, so the columns line up while
  Thai vowels and tone marks still shape. The raw text goes along as a `.txt` attachment, so it can
  still be copied.
- Code fences with a language label stay code blocks, because they are there to be copied.
- Headings become bold lines. Horizontal rules become blank lines. Everything else Discord renders
  stays as it is: bold, lists, quotes, inline code, links.
- Messages split at paragraph boundaries under 2000 characters, never inside a code fence.
- Mentions are never pinged (`allowed_mentions: {parse: []}`).
- Every outbound text, including any text drawn into an image, passes the secret redaction from
  `relay.py`.
- If Chrome is missing or fails, fall back to text (cards, or the code block) and log it.

The test posts in thread `1:pops-vet` are the reference for how this should look.

The bot's own replies, in the DM, the main channel and the shared channels, go out through the
plugin's reply tool, so this formatter never sees them. They follow the same rules by instruction:
`bot-up` launches the bot with `--append-system-prompt` telling it that Discord shows no markdown
tables (send cards instead), to keep code blocks narrow, and to write no wide layouts. A formatter
command the bot could call to send tables as images is a possible follow-up, not part of this work.

### 8. Process, configuration and state

- The code lives in leica-oracle under `.claude/skills/bot-up/` (the bridge belongs to the bot's
  runtime), written in Python 3 with the standard library only, and holding no IDs.
- Per-oracle configuration: `<oracle repo>/.discord-state/bridge.json` holds the guild, the channel,
  Un's user id, the tmux session, the poll interval, and the reason `#pops-vet` lists the bot's own
  id. No config file means no bridge, so other oracles are unaffected.
- State: `.discord-state/bridge-state.json`, written atomically (temporary file, then rename). Log:
  `.discord-state/bridge.log`, size-capped, plus the pane itself. A pid file stops a second bridge
  from starting.
- `bot-up.sh` starts the bridge in a second pane of the bot window when `bridge.json` exists, and
  confirms it started. Both panes carry the bot-window marker from section 10, so direnv gives both of
  them the token. `--force` restarts both panes.
- Poll every 3 to 5 seconds. Honour Discord's rate limits; any 429 waits for `retry_after`.
- The bot needs these permissions in `#pops-vet`, which Un grants in Discord: View Channel, Read
  Message History, Send Messages, Send Messages in Threads, Create Public Threads, Manage Threads, Add
  Reactions, Attach Files. Sending in threads and attaching files are already proven.

### 9. Settings fix

Add `env.DISCORD_STATE_DIR` with pops-vet's own `.discord-state` path to pops-vet-oracle's
`.claude/settings.local.json`, so project settings override the global value for that repo only.
After the bot window restarts, confirm it took effect from the environment of the new plugin process.
If project settings do not override the global value, stop and bring it back to Un. The global fix
touches every bot.

### 10. The bot token only in the bot window

- `bot-up.sh` creates the bot window, and the bridge pane, with a marker variable in the pane's
  environment (`tmux new-window -e` / `split-window -e`), for example `ORACLE_BOT_WINDOW=1`. The
  oracle's `start.sh` sets the same marker before it runs `direnv export`.
- pops-vet's `.envrc` loads the token from `pass` only when the marker is set. Everywhere else it
  exports the token as an empty string. The plugin reads its fallback `.env` file only when the
  variable is undefined, so an empty value guarantees no window falls back to a file. The teammate
  wrapper `~/.claude/bin/claude-teammate` uses the same rule.
- The token still comes only from `.envrc` and `pass`, the rule the bot-up skill states. Work windows
  also stop calling `pass` for the bot token.
- Side effect: each work window shows one failed MCP server (discord). That is expected.
- `bot-up.sh` keeps working for oracles whose `.envrc` ignores the marker, so only pops-vet changes
  now.
- Windows that are already open keep their environment until they restart. The two work windows
  opened after the 2026-10-17 token rotation still log in as the bot until then.

## Rollout

1. Settings fix, pops-vet's `access.json` as in section 2, and the token change in section 10.
   Restart the bot window fresh with `bot-up --force`. That also retires this morning's `relay.py`
   monitor and the DM forwarding.
2. Bridge with window 1 only (`1:pops-vet`). Un checks a full round trip on his phone.
3. All windows of `04-pops-vet`.
4. Shared channels: an @mention from Un in each.
5. Later and separate: other oracles, and the global setting.

## Testing

- Unit tests with the standard library's unittest and synthetic fixtures. Real transcripts and real
  messages stay out of this public repo. Cover:
  - the formatter: tables to cards, layout detection, headings, fences, chunk sizes, redaction
  - the sync planner, as a pure function from windows, map and threads to actions: create, adopt,
    rename, renumber, archive
  - the inbound router's decisions: idle, busy, prompt, text in the input box, closed window,
    coalescing
  - turn extraction from a transcript, including tool calls and sidechain lines
- Live checks on pops-vet with Un:
  - threads appear and adopt the two existing ones
  - renaming and renumbering a window renames its thread
  - closing a scratch window archives its thread
  - Un's message reaches window 1 and the answer comes back in its thread
  - a message to a busy window waits with ⏳, then shows ✅
  - a prompt answered by number
  - a screenshot reaches the window
  - the main channel reaches the bot with no mention
  - a shared channel answers only on mention
  - the bot window never also handles a thread message
  - a newly opened work window has an empty bot token, and Un's next DM gets no mark from it, while
    the bot window and the bridge pane hold the token
- Only eyes verify layout. Un checks the first real posts on his phone.

## Risks

- A Claude Code update can change the screen the pane reader depends on. Its patterns fit versions
  2.1.288 to 2.1.302. The session file's `status` is a second signal.
- A plugin update could reorder the gate and break the `#pops-vet` setting. The live check "the bot
  window never also handles a thread message" catches that. Run it again after any plugin update.
- Thread renames are rate-limited. Debouncing covers normal use.
- Wide tables become small images on a phone. Tap to zoom, and the cards are the readable,
  copyable form.
- Anyone who controls Un's Discord account can drive windows that run with permission checks
  bypassed. The DM relay already has this risk. The bridge keeps the owner-only filter. Two-factor
  login on the account matters.
- `pinentry-mac` is missing, so a bot restart can fail at the token step once gpg-agent forgets the
  passphrase.

## Left to the builder

The module layout, exact poll intervals within 3 to 5 seconds, the image CSS within the look of the
test posts, the log format, the exact transcript filters (learn them from a real transcript locally,
then write synthetic fixtures), and how the pane patterns are ported from `relay.py`.

## Calls Leica made (for Un to check)

1. The bridge is its own program on Discord REST. The plugin is not forked or patched.
2. `#pops-vet` lists the bot's own id in `allowFrom`, so the plugin never takes its messages. The
   bridge passes main-channel messages to the bot window.
3. A thread gets everything the window said in the turn, not only the last paragraph. Very long
   turns get the final answer plus the full text as a file.
4. Prompts Un types at the Mac are quoted into the thread.
5. A new or adopted thread starts with the window's latest message.
6. Messages wait while the window is busy or while text sits in its input box, and quick bursts are
   joined into one prompt.
7. Attachments are downloaded and their paths typed into the window.
8. A Discord reply carries a one-line quote of the message it answers.
9. Plain shell windows get a thread but no typing.
10. A mockup image carries its raw text as a `.txt` attachment.
11. "Typing" shows only for turns that came from Discord.
12. The code goes in this public repo with no IDs. The config and state stay in the oracle's
    git-ignored `.discord-state/`.
13. After a tmux server restart, every thread is archived and the windows that come back get new
    ones. No thread is picked up again by name.
14. The bot's own replies follow the mobile rules by an instruction given at launch, not through the
    formatter.
15. The token rule works through a marker that bot-up sets on the bot window. Other windows get an
    empty token, not an unset one.

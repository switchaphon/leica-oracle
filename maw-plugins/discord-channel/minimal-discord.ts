#!/usr/bin/env bun
/**
 * Minimal Discord Channel for Claude Code.
 *
 * Stripped from fakechat (295 LOC) + discord.js minimum.
 * Same contract: stdio MCP ↔ Claude, discord.js ↔ Discord.
 * No access.json, no pairing, no gate() — just BOT_TOKEN + 1 channel.
 *
 * Usage:
 *   DISCORD_BOT_TOKEN=xxx DISCORD_CHANNEL_ID=123 bun run minimal-discord.ts
 *
 * Or via Claude Code:
 *   claude --channels "DISCORD_BOT_TOKEN=xxx DISCORD_CHANNEL_ID=123 bun minimal-discord.ts"
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from '@modelcontextprotocol/sdk/types.js'
import { Client, GatewayIntentBits, Partials, type Message } from 'discord.js'

// ── Config ───────────────────────────────────────────────────────────────

const TOKEN = process.env.DISCORD_BOT_TOKEN
const CHANNEL_ID = process.env.DISCORD_CHANNEL_ID

if (!TOKEN) {
  process.stderr.write('minimal-discord: DISCORD_BOT_TOKEN required\n')
  process.exit(1)
}
if (!CHANNEL_ID) {
  process.stderr.write('minimal-discord: DISCORD_CHANNEL_ID required\n')
  process.exit(1)
}

// ── Discord client (minimum intents) ─────────────────────────────────────

const discord = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.DirectMessages,
  ],
  partials: [Partials.Channel],
})

// ── MCP server (same contract as fakechat) ───────────────────────────────

const mcp = new Server(
  { name: 'minimal-discord', version: '0.1.0' },
  {
    capabilities: { tools: {}, experimental: { 'claude/channel': {} } },
    instructions: [
      'The sender reads Discord, not this session.',
      'Anything you want them to see must go through the reply tool.',
      'Messages arrive as <channel source="discord" chat_id="..." message_id="...">.',
      'Reply with the reply tool — pass chat_id back.',
    ].join(' '),
  },
)

// ── Tools: reply + edit_message (same as fakechat) ───────────────────────

mcp.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'reply',
      description: 'Send a message to Discord.',
      inputSchema: {
        type: 'object',
        properties: {
          chat_id: { type: 'string', description: 'Channel or DM ID' },
          text: { type: 'string' },
          reply_to: { type: 'string', description: 'Message ID to thread under' },
        },
        required: ['chat_id', 'text'],
      },
    },
    {
      name: 'edit_message',
      description: 'Edit a previously sent message.',
      inputSchema: {
        type: 'object',
        properties: {
          chat_id: { type: 'string' },
          message_id: { type: 'string' },
          text: { type: 'string' },
        },
        required: ['chat_id', 'message_id', 'text'],
      },
    },
  ],
}))

mcp.setRequestHandler(CallToolRequestSchema, async (req) => {
  const args = (req.params.arguments ?? {}) as Record<string, unknown>
  try {
    switch (req.params.name) {
      case 'reply': {
        const chatId = args.chat_id as string
        const text = args.text as string
        const replyTo = args.reply_to as string | undefined

        const channel = await discord.channels.fetch(chatId)
        if (!channel?.isTextBased() || !('send' in channel)) {
          throw new Error(`channel ${chatId} not found or not text-based`)
        }

        // chunk at 2000 chars (Discord hard limit)
        const chunks = text.length <= 2000 ? [text] : chunkText(text, 2000)
        const sentIds: string[] = []

        for (const chunk of chunks) {
          const sent = await channel.send({
            content: chunk,
            ...(replyTo && sentIds.length === 0
              ? { reply: { messageReference: replyTo } }
              : {}),
          })
          sentIds.push(sent.id)
        }

        return { content: [{ type: 'text', text: `sent (id: ${sentIds[0]})` }] }
      }

      case 'edit_message': {
        const chatId = args.chat_id as string
        const msgId = args.message_id as string
        const text = args.text as string

        const channel = await discord.channels.fetch(chatId)
        if (!channel?.isTextBased() || !('messages' in channel)) {
          throw new Error(`channel ${chatId} not found`)
        }
        const msg = await channel.messages.fetch(msgId)
        await msg.edit(text)
        return { content: [{ type: 'text', text: 'ok' }] }
      }

      default:
        return {
          content: [{ type: 'text', text: `unknown tool: ${req.params.name}` }],
          isError: true,
        }
    }
  } catch (err) {
    return {
      content: [{ type: 'text', text: `${req.params.name}: ${err instanceof Error ? err.message : err}` }],
      isError: true,
    }
  }
})

// ── Inbound: Discord → Claude (notification, same as fakechat deliver()) ─

discord.on('messageCreate', (msg: Message) => {
  if (msg.author.bot) return // prevent loop

  void mcp.notification({
    method: 'notifications/claude/channel',
    params: {
      content: msg.content || '(attachment)',
      meta: {
        chat_id: msg.channelId,
        message_id: msg.id,
        user: msg.author.username,
        user_id: msg.author.id,
        ts: msg.createdAt.toISOString(),
        ...(msg.attachments.size > 0
          ? {
              attachment_count: String(msg.attachments.size),
              attachments: msg.attachments
                .map((a) => `${a.name} (${a.contentType ?? '?'}, ${a.size}B)`)
                .join('; '),
            }
          : {}),
      },
    },
  })
})

// ── Lifecycle: stdio EOF → shutdown Gateway ──────────────────────────────

let shuttingDown = false
function shutdown(): void {
  if (shuttingDown) return
  shuttingDown = true
  process.stderr.write('minimal-discord: shutting down\n')
  setTimeout(() => process.exit(0), 2000)
  void Promise.resolve(discord.destroy()).finally(() => process.exit(0))
}
process.stdin.on('end', shutdown)
process.stdin.on('close', shutdown)
process.on('SIGTERM', shutdown)
process.on('SIGINT', shutdown)

// ── Helper ───────────────────────────────────────────────────────────────

function chunkText(text: string, limit: number): string[] {
  const out: string[] = []
  let rest = text
  while (rest.length > limit) {
    const cut = rest.lastIndexOf('\n', limit)
    const pos = cut > limit / 2 ? cut : limit
    out.push(rest.slice(0, pos))
    rest = rest.slice(pos).replace(/^\n+/, '')
  }
  if (rest) out.push(rest)
  return out
}

// ── Boot ─────────────────────────────────────────────────────────────────

await mcp.connect(new StdioServerTransport())
discord.once('ready', () => {
  process.stderr.write(`minimal-discord: connected as ${discord.user?.tag}\n`)
})
await discord.login(TOKEN)

#!/usr/bin/env bun
/**
 * Minimal MQTT Channel for Claude Code.
 *
 * Same contract as fakechat/discord — stdio MCP ↔ Claude,
 * but receives/sends messages via MQTT instead of Discord/WebSocket.
 *
 * Inbound:  MQTT subscribe → notifications/claude/channel → Claude
 * Outbound: Claude → reply tool → MQTT publish
 *
 * Usage:
 *   MQTT_BROKER=mqtt://localhost:1883 MQTT_TOPIC=oracle/chat bun run minimal-mqtt-channel.ts
 *
 * Protocol:
 *   Inbound topic:  <MQTT_TOPIC>/in    (JSON: { user, text, id?, ts? })
 *   Outbound topic: <MQTT_TOPIC>/out   (JSON: { text, reply_to?, ts })
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from '@modelcontextprotocol/sdk/types.js'
import mqtt from 'mqtt'

// ── Config ───────────────────────────────────────────────────────────────

const BROKER = process.env.MQTT_BROKER ?? 'mqtt://localhost:1883'
const TOPIC = process.env.MQTT_TOPIC ?? 'oracle/chat'
const TOPIC_IN = `${TOPIC}/in`
const TOPIC_OUT = `${TOPIC}/out`
const CLIENT_ID = process.env.MQTT_CLIENT_ID ?? `claude-${Date.now()}`

// ── MQTT client ──────────────────────────────────────────────────────────

const mqttClient = mqtt.connect(BROKER, {
  clientId: CLIENT_ID,
  clean: true,
  reconnectPeriod: 5000,
})

mqttClient.on('connect', () => {
  process.stderr.write(`mqtt-channel: connected to ${BROKER}\n`)
  mqttClient.subscribe(TOPIC_IN, (err) => {
    if (err) process.stderr.write(`mqtt-channel: subscribe failed: ${err}\n`)
    else process.stderr.write(`mqtt-channel: listening on ${TOPIC_IN}\n`)
  })
})

mqttClient.on('error', (err) => {
  process.stderr.write(`mqtt-channel: error: ${err}\n`)
})

// ── MCP server (same contract as fakechat) ───────────────────────────────

const mcp = new Server(
  { name: 'mqtt-channel', version: '0.1.0' },
  {
    capabilities: { tools: {}, experimental: { 'claude/channel': {} } },
    instructions: [
      'The sender reads MQTT, not this session.',
      'Anything you want them to see must go through the reply tool.',
      `Messages arrive from MQTT topic ${TOPIC_IN}.`,
      'Reply with the reply tool — it publishes to MQTT.',
    ].join(' '),
  },
)

// ── Tools: reply + edit_message ──────────────────────────────────────────

mcp.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'reply',
      description: `Send a message via MQTT (publishes to ${TOPIC_OUT}).`,
      inputSchema: {
        type: 'object',
        properties: {
          text: { type: 'string', description: 'Message text' },
          reply_to: { type: 'string', description: 'Original message ID' },
        },
        required: ['text'],
      },
    },
    {
      name: 'edit_message',
      description: 'Publish a correction to MQTT (topic/out with edit flag).',
      inputSchema: {
        type: 'object',
        properties: {
          message_id: { type: 'string' },
          text: { type: 'string' },
        },
        required: ['message_id', 'text'],
      },
    },
  ],
}))

let seq = 0
function nextId(): string {
  return `mqtt-${Date.now()}-${++seq}`
}

mcp.setRequestHandler(CallToolRequestSchema, async (req) => {
  const args = (req.params.arguments ?? {}) as Record<string, unknown>
  try {
    switch (req.params.name) {
      case 'reply': {
        const text = args.text as string
        const replyTo = args.reply_to as string | undefined
        const id = nextId()
        const payload = JSON.stringify({
          id,
          from: 'assistant',
          text,
          reply_to: replyTo,
          ts: new Date().toISOString(),
        })
        mqttClient.publish(TOPIC_OUT, payload, { qos: 1 })
        return { content: [{ type: 'text', text: `sent (id: ${id})` }] }
      }

      case 'edit_message': {
        const payload = JSON.stringify({
          type: 'edit',
          id: args.message_id as string,
          text: args.text as string,
          ts: new Date().toISOString(),
        })
        mqttClient.publish(TOPIC_OUT, payload, { qos: 1 })
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
      content: [
        { type: 'text', text: `${req.params.name}: ${err instanceof Error ? err.message : err}` },
      ],
      isError: true,
    }
  }
})

// ── Inbound: MQTT → Claude (notification) ────────────────────────────────

mqttClient.on('message', (topic, payload) => {
  if (topic !== TOPIC_IN) return

  try {
    const msg = JSON.parse(payload.toString()) as {
      user?: string
      user_id?: string
      text?: string
      id?: string
      ts?: string
    }

    const content = msg.text?.trim()
    if (!content) return

    void mcp.notification({
      method: 'notifications/claude/channel',
      params: {
        content,
        meta: {
          chat_id: TOPIC,
          message_id: msg.id ?? nextId(),
          user: msg.user ?? 'mqtt',
          user_id: msg.user_id ?? 'unknown',
          ts: msg.ts ?? new Date().toISOString(),
        },
      },
    })
  } catch {
    process.stderr.write(`mqtt-channel: invalid JSON on ${topic}\n`)
  }
})

// ── Lifecycle: stdio EOF → disconnect MQTT ───────────────────────────────

let shuttingDown = false
function shutdown(): void {
  if (shuttingDown) return
  shuttingDown = true
  process.stderr.write('mqtt-channel: shutting down\n')
  setTimeout(() => process.exit(0), 2000)
  mqttClient.end(false, () => process.exit(0))
}
process.stdin.on('end', shutdown)
process.stdin.on('close', shutdown)
process.on('SIGTERM', shutdown)
process.on('SIGINT', shutdown)

// ── Boot ─────────────────────────────────────────────────────────────────

await mcp.connect(new StdioServerTransport())

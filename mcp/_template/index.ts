/**
 * MCP Server Template — TypeScript (stdio transport)
 *
 * Replace all <placeholders> before use.
 * Run: npx ts-node index.ts
 */

import * as readline from 'readline'

const SERVER_NAME = '<server-name>'
const SERVER_VERSION = '1.0.0'

interface JsonRpcRequest {
  jsonrpc: '2.0'
  id?: number | string
  method: string
  params?: Record<string, unknown>
}

interface JsonRpcResponse {
  jsonrpc: '2.0'
  id?: number | string
  result?: unknown
  error?: { code: number; message: string }
}

function send(response: JsonRpcResponse): void {
  process.stdout.write(JSON.stringify(response) + '\n')
}

async function processRequest(request: JsonRpcRequest): Promise<void> {
  const { method, params = {}, id } = request

  if (method === 'notifications/initialized') return

  if (method === 'initialize') {
    send({
      jsonrpc: '2.0',
      id,
      result: {
        protocolVersion: '2024-11-05',
        capabilities: { tools: {} },
        serverInfo: { name: SERVER_NAME, version: SERVER_VERSION },
      },
    })
    return
  }

  if (method === 'tools/list') {
    send({
      jsonrpc: '2.0',
      id,
      result: {
        tools: [
          {
            name: '<tool-name>',
            description: '<what this tool does>',
            inputSchema: {
              type: 'object',
              properties: {
                '<param>': { type: 'string', description: '<param description>' },
              },
              required: ['<param>'],
            },
          },
        ],
      },
    })
    return
  }

  if (method === 'tools/call') {
    const { name, arguments: args = {} } = params as { name: string; arguments: Record<string, unknown> }
    if (name === '<tool-name>') {
      send({
        jsonrpc: '2.0',
        id,
        result: { content: [{ type: 'text', text: `Received: ${JSON.stringify(args)}` }] },
      })
      return
    }
    send({
      jsonrpc: '2.0',
      id,
      result: { content: [{ type: 'text', text: `Unknown tool: ${name}` }], isError: true },
    })
    return
  }

  send({ jsonrpc: '2.0', id, error: { code: -32601, message: 'Method not found' } })
}

const rl = readline.createInterface({ input: process.stdin })
rl.on('line', (line) => {
  try {
    const request: JsonRpcRequest = JSON.parse(line.trim())
    processRequest(request).catch(console.error)
  } catch {
    // ignore malformed input
  }
})

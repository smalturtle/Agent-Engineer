"""
MCP Server Template — Python (stdio transport)

Replace all <placeholders> before use.
"""
from __future__ import annotations

import asyncio
import json
import sys
from typing import Any


SERVER_NAME = "<server-name>"
SERVER_VERSION = "1.0.0"


async def handle_initialize(params: dict[str, Any]) -> dict[str, Any]:
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {}},
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
    }


async def handle_tools_list() -> dict[str, Any]:
    return {
        "tools": [
            {
                "name": "<tool-name>",
                "description": "<what this tool does>",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "<param>": {"type": "string", "description": "<param description>"}
                    },
                    "required": ["<param>"],
                },
            }
        ]
    }


async def handle_tools_call(params: dict[str, Any]) -> dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments", {})

    if name == "<tool-name>":
        result = f"Received: {arguments}"
        return {"content": [{"type": "text", "text": result}]}

    return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}


async def process_request(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")

    handlers = {
        "initialize": lambda: handle_initialize(params),
        "tools/list": handle_tools_list,
        "tools/call": lambda: handle_tools_call(params),
    }

    if method == "notifications/initialized":
        return None

    handler = handlers.get(method)
    if handler is None:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}

    result = await handler()
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


async def main() -> None:
    while True:
        line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        if not line:
            break
        try:
            request = json.loads(line.strip())
            response = await process_request(request)
            if response is not None:
                print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            pass


if __name__ == "__main__":
    asyncio.run(main())

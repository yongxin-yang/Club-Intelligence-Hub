"""
File: app/core/mcp_client.py
Function: 统一管理 MCP Client 的创建与配置, 提供给 Gateway 使用
Class/Function:
    get_mcp_server_url: 从环境变量读取 MCP Server URL
    create_mcp_client: 基于 URL 创建 SSE MCP Client 实例
Call:
    由 app.gateway.api 导入以获取 MCP Client
"""

import os
from contextlib import asynccontextmanager


def get_mcp_server_url() -> str:
    # Default to /sse endpoint for FastMCP
    return os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:3333/sse")


@asynccontextmanager
async def create_mcp_client():
    from mcp.client.sse import sse_client
    from mcp.client.session import ClientSession

    url = get_mcp_server_url()
    print(f"[DEBUG] Connecting to MCP Server at {url}...")
    # Increase timeout for testing environment
    async with sse_client(url, timeout=10) as streams:
        print("[DEBUG] SSE Connected. Initializing session...")
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            print("[DEBUG] Session initialized.")
            yield session


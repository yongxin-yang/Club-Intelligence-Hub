"""
File: app/gateway/api.py
Function: 实现 AI Gateway 层 Chat Mode HTTP 接口, 编排 LLM 与 MCP 调用
Class/Function:
    ChatRequest: 定义 /ai/chat 请求体数据模型
    create_mcp_client: 基于 MCP Server URL 创建客户端实例
    get_llm_client: 创建 OpenAI LLM 客户端
    chat: /ai/chat 路由处理函数, 返回文本或工具结果
Call:
    前端 -> /ai/chat -> 本文件 -> OpenAI LLM + MCP Server(app.mcp_server.server)
"""

import json
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from openai import OpenAI


MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:3333")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_id: Optional[str] = None
    mode: Optional[str] = None


def create_mcp_client():
    from mcp.client.sse import Client as SSEClient
    return SSEClient(MCP_SERVER_URL)


def get_llm_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 环境变量未设置")
    return OpenAI(api_key=api_key)


app = FastAPI(title="Club AI Gateway", version="0.1.0")


@app.post("/ai/chat")
async def chat(req: ChatRequest) -> Dict[str, Any]:
    mode = req.mode or "chat"
    if mode != "chat":
        raise HTTPException(status_code=400, detail="当前仅支持 chat 模式")

    mcp_client = create_mcp_client()
    tools = await mcp_client.list_tools()

    openai_tools: List[Dict[str, Any]] = []
    for t in tools:
        openai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
        )

    llm = get_llm_client()

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI assistant for the Club AI Hub. "
                "You must use tools to access club systems and data."
            ),
        },
        {
            "role": "user",
            "content": req.message,
        },
    ]

    response = llm.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        tools=openai_tools,
        tool_choice="auto",
    )

    msg = response.choices[0].message

    if msg.tool_calls:
        results: List[Dict[str, Any]] = []
        for call in msg.tool_calls:
            raw_args = call.function.arguments or "{}"
            try:
                parsed_args = json.loads(raw_args)
            except json.JSONDecodeError:
                parsed_args = {}

            result = await mcp_client.call_tool(call.function.name, parsed_args)
            results.append({"tool": call.function.name, "result": result})

        return {"type": "tool_result", "data": results}

    return {"type": "text", "content": msg.content}


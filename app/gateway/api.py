"""
File: app/gateway/api.py
Function: 实现 AI Gateway 层 Chat Mode HTTP 接口, 编排 LLM 与 MCP 调用
Class/Function:
    ChatRequest: 定义 /ai/chat 请求体数据模型
    create_mcp_client: 基于 MCP Server URL 创建客户端实例
    chat: /ai/chat 路由处理函数, 通过核心层获取统一的 LLM 客户端
Call:
    前端 -> /ai/chat -> 本文件 -> app.core.llm -> 外部 LLM + MCP Server(app.mcp_server.server)
"""

import json
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.core.llm import get_llm_client_and_model
from app.core.mcp_client import create_mcp_client


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_id: Optional[str] = None
    mode: Optional[str] = None


app = FastAPI(title="Club AI Gateway", version="0.1.0")


@app.post("/ai/chat")
async def chat(req: ChatRequest) -> Dict[str, Any]:
    mode = req.mode or "chat"
    if mode != "chat":
        raise HTTPException(status_code=400, detail="当前仅支持 chat 模式")

    async with create_mcp_client() as mcp_client:
        tools_result = await mcp_client.list_tools()
        tools = tools_result.tools

        openai_tools: List[Dict[str, Any]] = []
        for t in tools:
            openai_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.inputSchema,  # MCP uses inputSchema, OpenAI uses parameters
                    },
                }
            )

        llm, model = get_llm_client_and_model()

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
            model=model,
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
                # result from call_tool is CallToolResult
                # It has content (list of TextContent or ImageContent)
                # We should serialize it
                results.append({"tool": call.function.name, "result": result.content})

            return {"type": "tool_result", "data": results}

        return {"type": "text", "content": msg.content}

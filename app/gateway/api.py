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
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.llm import get_llm_client_and_model
from app.core.mcp_client import create_mcp_client
from app.core.config.models import PROVIDER_MODELS, LLMProvider
from app.core.config.agents import AGENTS, AgentType


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: List[Dict[str, str]] = Field(default_factory=list)
    user_id: Optional[str] = None
    model: Optional[str] = None
    agent_id: Optional[str] = None
    mode: Optional[str] = None


app = FastAPI(title="Club AI Gateway", version="0.1.0")


@app.get("/")
async def read_index():
    # Return the frontend index.html
    # Path is relative to this file: ../frontend/index.html
    current_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_path = os.path.join(current_dir, "..", "frontend", "index.html")
    
    if os.path.exists(frontend_path):
        # In a real scenario, we might use a template engine to inject config
        # For simple static file serving, we just return it.
        # The frontend will default to relative paths if window.config is missing.
        return FileResponse(frontend_path)
    return {"error": "Frontend not found"}


@app.get("/ai/models")
async def list_models() -> Dict[str, List[str]]:
    # Dynamic model discovery based on LLM provider
    try:
        from app.core.llm import get_llm_provider, _get_config
        provider = get_llm_provider()
        
        # Determine available models based on provider config
        # In a real app, this might query the provider's API, but for now we infer from config/defaults
        if provider == "openai":
            configured_model = _get_config("OPENAI_MODEL") or "gpt-4o-mini"
            # Return a curated list plus the configured one
            return {"models": list(set([configured_model, "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]))}
        elif provider == "deepseek":
            configured_model = _get_config("DEEPSEEK_MODEL") or "deepseek-chat"
            return {"models": list(set([configured_model, "deepseek-chat", "deepseek-coder"]))}
        elif provider == "kimi":
            configured_model = _get_config("KIMI_MODEL") or "moonshot-v1-8k"
            return {"models": list(set([configured_model, "moonshot-v1-8k", "moonshot-v1-32k"]))}
        else:
            return {"models": ["default-model"]}
    except Exception as e:
        print(f"[WARN] Failed to determine dynamic models: {e}")
        return {"models": ["gpt-4o", "gpt-4o-mini", "deepseek-chat", "kimi-chat"]}


@app.get("/ai/tools")
async def list_tools() -> Dict[str, List[Dict[str, Any]]]:
    """List available MCP tools for frontend selection/display"""
    try:
        async with create_mcp_client() as mcp_client:
            tools_result = await mcp_client.list_tools()
            # Return simplified tool info
            return {
                "tools": [
                    {
                        "name": t.name,
                        "description": t.description,
                        # "schema": t.inputSchema # Optional: include schema if frontend needs it
                    }
                    for t in tools_result.tools
                ]
            }
    except Exception as e:
        print(f"[ERROR] Failed to list tools: {e}")
        return {"tools": []}


@app.get("/ai/agents")
async def list_agents() -> Dict[str, List[Dict[str, str]]]:
    """List available Agents/Rules (Mock for now)"""
    # This would later come from a database or config
    return {
        "agents": [
            {"id": "agent_default", "name": "通用助手", "description": "默认的智能助手，可调用所有工具"},
            {"id": "agent_finance", "name": "财务助理", "description": "专注于财务报销与审批 (Mock)"},
            {"id": "agent_activity", "name": "活动策划", "description": "协助策划社团活动 (Mock)"}
        ]
    }


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

        llm, default_model = get_llm_client_and_model()
        model = req.model or default_model

        # Determine System Prompt based on Agent ID
        system_prompt = AGENTS[AgentType.DEFAULT]["system_prompt"]
        if req.agent_id:
            try:
                # Allow partial match or exact match
                agent_enum = AgentType(req.agent_id)
                system_prompt = AGENTS[agent_enum]["system_prompt"]
            except ValueError:
                pass # Fallback to default

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]
        
        # Append history if valid
        for hist in req.history:
            if "role" in hist and "content" in hist:
                messages.append({"role": hist["role"], "content": hist["content"]})
        
        messages.append(
            {
                "role": "user",
                "content": req.message,
            }
        )

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

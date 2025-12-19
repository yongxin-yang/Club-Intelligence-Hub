# 快速开始与接口集成指南 (Quick Start)

## 1. 环境准备

### 1.1 基础环境
- **操作系统**: Windows (推荐) / macOS / Linux
- **Python**: 3.12+
- **包管理工具**: `uv` (本项目使用 `uv` 进行依赖管理)

### 1.2 依赖安装
在项目根目录下执行：
```bash
uv sync
```

### 1.3 配置文件
在 `config/` 目录下创建 `keys.local.json` (如果不存在)，用于配置 LLM 密钥：
```json
{
  "api_key": "sk-...",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o"
}
```
> 注意：该文件已被 `.gitignore` 排除，请勿提交到版本控制系统。

## 2. 服务启动顺序

本项目由三个独立服务组成，请**按顺序**在不同的终端窗口中启动：

### 步骤 1: 启动业务模拟后端 (Backend1)
模拟现有的社团业务系统 (Database/API)。
- **端口**: `8001`
- **命令**:
```bash
uv run python -m backend1.main
```
- **验证**: 访问 `http://127.0.0.1:8001/docs` 查看 Swagger 文档。

### 步骤 2: 启动 MCP Server (Adapter)
连接 Backend1 并将其能力封装为 MCP 工具。
- **端口**: `3333`
- **依赖**: 需等待 Backend1 启动。
- **命令**:
```bash
uv run python -m app.mcp_server.server
```
- **验证**: 访问 `http://127.0.0.1:3333/sse` (应返回 404 或 method not allowed，但表明服务已起)。

### 步骤 3: 启动 AI Gateway (Core)
对外提供统一的 AI Chat 接口，编排 LLM 与 MCP 调用。
- **端口**: `8000`
- **依赖**: 需等待 MCP Server 启动。
- **命令**:
```bash
uv run uvicorn app.gateway.api:app --host 127.0.0.1 --port 8000 --reload
```
- **验证**: 访问 `http://127.0.0.1:8000/docs` 查看 API 文档。

## 3. 接口集成说明

### 3.1 系统链路图
```
[Frontend] -> (HTTP) -> [AI Gateway :8000] 
                              |
                              v
                        (LLM API) -> [OpenAI/DeepSeek]
                              |
                        (MCP Protocol / SSE)
                              v
                        [MCP Server :3333]
                              |
                        (REST API)
                              v
                        [Backend1 :8001]
```

### 3.2 核心接口定义

#### 智能对话接口 (Chat Mode)
- **URL**: `POST http://127.0.0.1:8000/ai/chat`
- **Content-Type**: `application/json`
- **请求参数**:
  ```json
  {
    "message": "帮我查一下 Alice 的信息",
    "user_id": "user_001",   // 可选
    "mode": "chat"           // 可选，默认 chat
  }
  ```
- **响应示例 (触发工具调用)**:
  ```json
  {
    "type": "tool_result",
    "data": [
      {
        "tool": "search_members",
        "result": [
          {
            "id": "1",
            "name": "Alice",
            "role": "President",
            "email": "alice@club.com"
          }
        ]
      }
    ]
  }
  ```
- **响应示例 (纯文本回复)**:
  ```json
  {
    "type": "text",
    "content": "你好，我是社团智能助手，请问有什么可以帮你？"
  }
  ```

## 4. 快速验证

### 4.1 使用测试脚本
项目中提供了测试脚本来验证 MCP 连接性：
```bash
uv run python test/test_mcp_connection.py
```

### 4.2 使用 cURL 手动测试
```bash
curl -X POST "http://127.0.0.1:8000/ai/chat" \
     -H "Content-Type: application/json" \
     -d "{\"message\": \"查询 Alice 的信息\"}"
```

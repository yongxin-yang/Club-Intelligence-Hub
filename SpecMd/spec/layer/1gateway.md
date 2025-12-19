# Gateway 层规范文档 (app.gateway)

## 1. 层的目的与适用范围

- 目的: 提供统一的 AI HTTP 接口入口，将前端请求转化为对 LLM 与 MCP 工具的调用，并将结果返回给前端。
- 适用范围:
  - 所有与 AI 对话/智能操作相关的 HTTP API。
  - v0.1 仅实现 Chat Mode 接口，路径为 `/ai/chat`。
  - 提供模型列表查询接口 `/ai/models`。

## 2. 输入输出格式与数据流转

### 2.1 输入格式 (HTTP 请求)

#### 模型列表
- 方法: `GET`
- 路径: `/ai/models`
- 返回: `{"models": ["gpt-4o", "deepseek-chat", ...]}`

#### 工具列表
- 方法: `GET`
- 路径: `/ai/tools`
- 返回: `{"tools": [{"name": "search_members", "description": "..."}, ...]}`

#### 智能体列表
- 方法: `GET`
- 路径: `/ai/agents`
- 返回: `{"agents": [{"id": "agent_default", "name": "通用助手", "description": "..."}, ...]}`

#### 聊天请求
- 方法: `POST`
- 路径: `/ai/chat`
- 请求体 JSON 结构:
  - `message: str` 必填，用户输入的自然语言内容。
  - `history: List[Dict[str, str]]` 选填，历史对话记录，格式如 `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]`。
  - `user_id: str | null` 选填，调用者标识 (用于后续权限与上下文扩展)。
  - `model: str | null` 选填，指定使用的 LLM 模型名称。
  - `mode: str | null` 选填，交互模式，v0.1 若为空或未提供，默认视为 `"chat"`。

### 2.2 输出格式 (HTTP 响应)

- 通用返回结构为 JSON:
  - 当 LLM 直接返回文本时:
    - `{"type": "text", "content": "..."}`
  - 当 LLM 触发 MCP 工具调用并返回结构化结果时:
    - `{"type": "tool_result", "data": [{"tool": str, "result": any}, ...]}`

### 2.3 数据流转过程

1. 前端调用 `/ai/chat`，发送 JSON 请求。
2. Gateway 将请求体解析为内部 Pydantic 模型 (ChatRequest)。
3. Gateway 创建/复用 MCP Client，调用其 `list_tools` 获取可用工具列表。
4. 将 MCP 工具列表转换为 OpenAI Chat Completions 支持的 `tools` schema。
5. 构造 messages，调用 OpenAI Chat Completion 接口:
   - system 提示词: “Club/社团智能助手 + 必须通过工具访问系统数据”等。
   - user 消息: 请求中的 `message`。
6. 若返回消息中包含 `tool_calls`:
   - 逐个解析工具名称与参数，调用 MCP Client 对应工具。
   - 收集工具调用结果，按统一结构返回。
7. 若不包含工具调用:
   - 将模型回复作为纯文本返回。

## 3. 验证规则与约束条件

- 请求体验证:
  - `message` 不允许为空字符串。
  - `mode` 若提供，仅允许值: `"chat"` (v0.1)，其余视为保留，当前可忽略或回落到 `chat`。
- 安全与权限 (v0.1 规划阶段约束):
  - Gateway 不直接访问业务数据库或业务 API，只能通过 MCP 工具进行读写操作。
  - 写操作工具在 Gateway 层应支持未来的二次确认机制 (目前可通过 mode 或额外字段预留)。
- 错误处理:
  - 参数校验失败返回 4xx 状态码与明确错误信息。
  - 其余错误允许抛出，由全局异常处理或服务器日志记录，便于调试。

## 4. 与其他层的集成要点

- 与 MCP Server 层:
  - 通过 HTTP MCP Server URL 建立 Client (如 `http://127.0.0.1:3333`)。
  - Gateway 不直接依赖底层 `mcp.client.sse.Client`, 而是通过 `app.core.mcp_client.create_mcp_client` 获取 MCP Client 实例。
  - Gateway 仅依赖 MCP Client 暴露的工具列表与调用接口, 对具体实现无感。
- 与 LLM/core 层:
  - 通过 `app.core.llm.get_llm_client_and_model` 获取统一封装的 LLM 客户端与模型名称。
  - 模型与提供方配置迁移至 `app.core.config.models`，使用枚举类 `LLMProvider` 和 `ModelList` 管理。
  - 智能体/规则配置迁移至 `app.core.config.agents`，使用枚举类 `AgentType` 管理。
  - 支持 OpenAI/DeepSeek/Kimi 等提供方, 具体选择由环境变量 `LLM_PROVIDER` 控制。
- 与前端:
  - 前端只需关注 `/ai/chat` 接口与返回结构，不直接感知 MCP/LLM 细节。
  - 生产环境前端应支持配置 API Base URL，而非硬编码为相对路径，以适应跨域部署场景。

## 5. 代码与文件结构

- 目录: `app/gateway/`
- 主要文件:
  - `api.py`
    - 定义 FastAPI 实例 `app`。
    - 定义请求模型 `ChatRequest` 与响应模型类型注释。
    - 实现 `/ai/chat` 路由与核心逻辑 (LLM + MCP 编排)。

该层的代码实现必须与本规范保持一致，如新增接口或扩展模式，应同步更新本文件。

# Chat Mode 基础工作流规范

## 1. 工作流目的

- 规范 v0.1 中 “AI 对话窗口 (Chat Mode)” 的端到端数据流转过程。
- 确保前端、Gateway、LLM、MCP Server 之间的交互可预测、可追踪。

## 2. 流程概览

1. 用户在前端输入自然语言问题或指令。
2. 前端调用 Gateway 的 `/ai/chat` 接口。
3. Gateway 根据输入构造 LLM 对话上下文，并附带可用 MCP 工具列表。
4. LLM 判断是否需要调用工具:
   - 若需要，返回 tool_calls。
   - 若不需要，直接返回文本回复。
5. 如存在 tool_calls，Gateway 依次调用 MCP Server 的对应工具并收集结果。
6. Gateway 将工具结果或文本回复封装为统一响应 JSON 返回前端。

## 3. 步骤与数据形态详细说明

### 步骤 1: 前端请求

- 请求方式: `POST /ai/chat`
- 请求体示例:
```json
{
  "message": "查一下名字里有 Ali 的成员",
  "user_id": "u123",
  "mode": "chat"
}
```

### 步骤 2: Gateway 预处理

- 解析 JSON 为内部请求模型。
- 基于 `mode` 决定使用 Chat Mode 逻辑 (v0.1 仅支持 chat)。
- 通过 MCP Client 调用 `list_tools` 获取工具列表 (如 `search_members`, `create_ticket` 等)。

### 步骤 3: 调用 LLM

- 构造 messages:
  - system: 描述角色为“社团管理系统 AI 助手”，必须通过工具访问系统数据。
  - user: 用户输入的 `message`。
- 构造 tools 参数: 使用 MCP 返回的工具描述映射为 OpenAI tools 格式。
- 调用 `chat.completions.create`，开启 `tool_choice="auto"`。

### 步骤 4: 处理工具调用

- 如 `response.choices[0].message.tool_calls` 不为空:
  - Gateway 对每个 tool_call:
    - 解析工具名与 JSON 参数。
    - 调用 MCP Client 的对应工具。
    - 收集结果放入数组 `[{"tool": name, "result": result}, ...]`。
  - 返回结构:
```json
{
  "type": "tool_result",
  "data": [
    {
      "tool": "search_members",
      "result": [ { "id": 1, "name": "Alice", "role": "President" } ]
    }
  ]
}
```

### 步骤 5: 直接文本回复

- 如 `tool_calls` 为空:
  - Gateway 直接返回:
```json
{
  "type": "text",
  "content": "模型生成的自然语言回复"
}
```

## 4. 验证与扩展

- 验证方式:
  - 启动 MCP Server 与 Gateway 后，通过 curl/Postman 调用 `/ai/chat`，验证:
    - 查询类请求是否触发工具调用并返回结构化结果。
    - 普通聊天请求是否返回文本内容。
- 扩展方向:
  - 为写操作请求增加 Draft/Confirm 模式，在工具实际执行前向用户展示即将调用的工具与参数。
  - 在工作流中增加操作日志记录与错误处理分支。


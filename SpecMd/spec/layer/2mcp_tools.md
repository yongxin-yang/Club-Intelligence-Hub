# MCP 工具层规范文档 (app.mcp_server)

## 1. 层的目的与适用范围

- 目的: 将现有及未来社团业务系统能力 (成员/活动/工单/审批等) 标准化为 MCP 工具，供 LLM 安全调用。
- 适用范围:
  - 所有 MCP 工具与资源的定义。
  - MCP Server 的运行方式与对外暴露协议。

## 2. 数据结构与流转过程

### 2.1 v0.1 内存模拟数据结构

- 成员列表 `FAKE_MEMBERS: List[dict]`
  - 结构示例:
    - `{ "id": 1, "name": "Alice", "role": "President" }`
- 工单列表 `FAKE_TICKETS: List[dict]`
  - 结构示例:
    - `{ "id": 1, "title": "...", "content": "...", "status": "created" }`

### 2.2 工具输入输出格式

- 查询类工具 `search_members(keyword: str) -> List[dict]`
  - 输入参数:
    - `keyword: str`，匹配成员姓名的关键字 (大小写不敏感)。
  - 返回:
    - 满足 `keyword` 条件的成员字典列表。
- 写操作类工具 `create_ticket(title: str, content: str) -> dict`
  - 输入参数:
    - `title: str`，工单标题。
    - `content: str`，工单内容/描述。
  - 返回:
    - 新创建的工单字典，包含 `id/title/content/status` 等字段。

### 2.3 数据流转过程

1. Gateway/LLM 通过 MCP 协议调用工具，如 `search_members` 或 `create_ticket`。
2. MCP Server 根据工具名称与参数路由至对应 Python 函数。
3. 工具函数在内存结构或后续接入的真实系统中执行操作。
4. 返回结果通过 MCP 协议回传给 Gateway/LLM。

## 3. 验证规则与约束条件

- 工具设计原则:
  - 一个工具对应一个清晰的业务能力。
  - 避免直接暴露底层 CRUD，更多以“业务动作”视角命名工具 (如 `submit_finance_ticket`)。
- 参数与返回值:
  - 参数类型应简单明确，适合 LLM 推断与构造。
  - 返回结构尽量稳定，字段含义清晰，利于前端展示与后续扩展。
- v0.1 特殊约束:
  - 使用内存 FAKE 数据模拟真实系统，方便快速迭代工具设计与验证链路。
  - 后续切换到真实系统时，应保持工具签名与返回结构尽量不变，或通过 SpecMd 同步更新。

## 4. 与其他层的集成要点

- 与 Gateway 层:
  - 通过 MCP HTTP Server URL 对接，不直接暴露 Python 函数调用。
  - Gateway 通过 `list_tools` 自动发现工具，并将工具描述映射到 LLM tools schema。
- 与业务系统/数据库层:
  - v0.1: 不接入真实数据库，仅内存模拟。
  - 未来版本: MCP 工具内部可以调用 REST API、数据库 ORM 等，但要保持对上游接口的稳定。

## 5. 代码与文件结构

- 目录: `app/mcp_server/`
- 主要文件:
  - `server.py`
    - 创建 FastMCP 实例并注册工具/资源。
    - 定义 `search_members` 与 `create_ticket` 等示例工具。
    - 在 `__main__` 分支中调用 `mcp.run(host, port)` 以 HTTP 模式启动。

添加新工具时，必须同时:
- 在代码中实现工具函数与装饰器。
- 在 SpecMd 对应文档中记录工具的输入输出与业务含义。


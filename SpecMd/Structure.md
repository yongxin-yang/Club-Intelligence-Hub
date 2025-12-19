# 项目整体结构说明 (Structure)

## 1. 项目目标与定位

本项目对应 PRD 中的 “Club AI Hub / Club AI Gateway”，目标是构建一个统一的 AI 智能中枢：

- 对接现有与未来的社团 Web 系统 (成员/活动/经费/审批等)。
- 通过 MCP 将业务系统能力标准化为可调用工具。
- 提供多种 AI 交互模式 (Chat/Agent/Draft)，v0.1 专注 Chat Mode。

## 2. 顶层目录结构

项目根目录规划如下 (仅列出核心部分)：

- `SpecMd/` 规范与需求文档目录
  - `Specify.md` 需求迭代总览与版本记录
  - `Structure.md` 全局架构与目录说明 (本文件)
  - `ProjectRules.md` 项目级开发规范与底线
  - `QuickStart.md` 快速开始与接口集成指南 (Startup & Integration)
  - `spec/layer/` 各代码层级规范
  - `spec/workflow/` 关键业务/交互工作流说明
- `app/` Python 代码主目录
  - `gateway/` AI Gateway 层 (FastAPI)
  - `mcp_server/` MCP 能力适配层 (FastMCP)
  - 预留: `core/`, `infra/` 等后续扩展层
- `test/` 测试代码目录
  - 存放各层的基础功能测试与集成测试 (当前包含 MCP Server 基础测试)。
- 其他
  - `pyproject.toml` Python 项目与依赖声明 (uv/PEP621)
  - 后续可添加前端代码等

## 3. 代码模块结构

### 3.1 app.gateway (AI Gateway 层)

- 目录: `app/gateway/`
- 主要职责:
  - 提供统一的 HTTP API 入口 (v0.1: Chat Mode 接口 `/ai/chat`)。
  - 管理与 LLM(OpenAI) 与 MCP Client 的调用流程。
  - 负责权限校验、模式路由 (未来扩展 Agent/Draft Mode)。
- 关键文件:
  - `app/gateway/api.py`
    - 定义 FastAPI 实例与对外暴露的 REST 接口。
    - 实现 Chat Mode 下：
      - 接收用户请求 (文本 + 可选 user_id 等信息)。
      - 从 MCP Server 拉取可用工具列表并映射为 LLM tools schema。
      - 调用 OpenAI Chat Completion，处理工具调用 (tool_calls) 与普通文本回复。

### 3.2 app.mcp_server (能力适配层)

- 目录: `app/mcp_server/`
- 主要职责:
  - 使用 FastMCP 定义 MCP Server，将各业务系统能力包装为工具。
  - 通过 Adapter 模式调用后端业务系统 (Backend1)，屏蔽底层系统差异。
  - v0.1 通过 HTTP 调用 `backend1` 模拟接口，不再直接使用内存 Fake 数据。
- 关键文件:
  - `app/mcp_server/server.py`
    - 定义 MCP 实例、工具与资源。
    - 通过 `backend1_adapter` 转发请求到真实(模拟)后端。
    - 通过 `mcp.run(host, port)` 以 HTTP 模式对外提供 MCP 能力。
  - `app/mcp_server/backend1_adapter/client.py`
    - 封装对 Backend1 (http://127.0.0.1:8001) 的 API 调用。

### 3.6 backend1 (模拟业务系统)

- 目录: `backend1/`
- 主要职责:
  - 模拟现有的社团业务系统后端 API。
  - 提供成员查询与工单创建的 REST 接口。
  - 使用内存列表存储数据 (模拟数据库)。
- 关键文件:
  - `backend1/main.py`: FastAPI 应用入口。

### 3.3 app.core (核心配置、LLM 与 MCP Client 层)

- 目录: `app/core/`
- 主要职责:
  - 统一管理与外部 LLM 服务相关的配置与客户端创建 (OpenAI/DeepSeek/Kimi 等)。
  - 提供 MCP Client 的创建与 MCP Server URL 读取, 为 Gateway 提供统一接口。
  - 抽象提供方选择策略与模型名称配置, 后续扩展日志记录与操作审计能力。
- 关键文件:
  - `app/core/llm.py`
    - 定义 `get_llm_provider` 用于从环境变量选择当前 LLM 提供方 (默认 `openai`)。
    - 定义 `get_llm_client_and_model` 统一根据提供方构造客户端与模型名称, 支持通过环境变量或本地密钥文件配置不同服务。
  - `app/core/config/`
    - `models.py`: 定义 LLM 模型枚举与提供方映射。
    - `agents.py`: 定义智能体/规则枚举与 Prompt 模板。
  - `app/core/mcp_client.py`
    - 定义 `get_mcp_server_url` 用于从环境变量读取 MCP Server URL (默认 `http://127.0.0.1:3333`)。
    - 定义 `create_mcp_client` 基于 URL 创建 SSE 协议的 MCP Client, 供 Gateway 调用。

### 3.4 test 目录 (测试层)

- 目录: `test/`
- 主要职责:
  - 存放针对 `app/` 中各层代码的基础测试与集成测试，用于验证当前实现是否符合 SpecMd 文档描述。
  - 不存放任何包含真实业务数据、数据库文件或含有 API 密钥、Token 等敏感信息的配置文件。
- 现有文件示例:
  - `test/test_mcp_server_basic.py` 用于验证 MCP Server 示例工具 (`search_members` / `create_ticket`) 的基本行为。

### 3.5 数据库与配置层 (安全约束说明)

- 数据库文件与真实业务数据:
  - 不在本项目仓库中存放实际数据库文件 (如 `.db`、`.sqlite` 等)，相关路径在 `.gitignore` 中统一排除。
  - 开发过程中如需本地数据文件，仅作为临时或模拟数据使用，应保存在被忽略的目录 (如 `datas/`、`results/`) 中。
- 配置文件与 API 密钥:
  - 所有敏感配置 (如 OpenAI API Key、数据库连接串、Token 等) 必须通过环境变量或外部安全配置系统提供，禁止直接写入代码或提交到 Git 仓库。
  - 可在仓库中提供不含敏感信息的配置模板文件 (例如 `config/example.env` 或带有 `.example` 后缀的文件)，实际配置文件应被 `.gitignore` 排除。


## 4. 交互模式与层次关系

整体分层关系与 PRD 一致:

- 前端 (待实现，可为 Web/ChatUI/管理后台)
  ↓ 调用
- AI Gateway (`app.gateway.api`) – 统一 AI 入口
  ↓ 通过 LLM & MCP
- LLM (OpenAI) – 推理与工具调度
  ↓ 工具调用
- MCP Server (`app.mcp_server.server`) – 能力适配层
  ↓ 访问
- 业务系统/数据库 – 成员/活动/工单/审批等 (v0.1 用内存模拟)

## 5. 与 SpecMd 其他文档的关系

- `ProjectRules.md` 定义全局编码规范、环境要求与安全约束，本文件仅描述结构。
- `spec/layer/1gateway.md` 详细规范 Gateway 层的输入输出格式、数据流与文件结构。
- `spec/layer/2mcp_tools.md` 详细规范 MCP 工具层的数据结构、验证规则与集成要点。
- `spec/workflow/chat_mode_basic.md` 描述 Chat Mode 从 HTTP 请求到工具调用与响应返回的完整工作流。

本文件在每次新增/调整目录结构或模块职责时必须同步更新，以保持“文档即架构”。

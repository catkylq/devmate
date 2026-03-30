# DevMate

DevMate 是一个用于面试评估的 **AI 编程助手**项目，核心能力包括：

- 通过 **Streamable HTTP** 调用 MCP 网络搜索
- 基于 **Qdrant** 的本地文档 RAG 检索
- Agent Skills（技能加载与任务模式学习）
- 在 `workspace/` 中生成多文件代码项目
- 提供 REST API 服务和现代化 Web 界面


## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| **Agent 框架** | deepagents + LangGraph | 任务编排与执行 |
| **聊天模型** | DeepSeek / OpenAI Compatible | LLM 推理 |
| **向量检索** | Qdrant | RAG 文档存储与检索 |
| **搜索服务** | FastMCP + Tavily | MCP 网络搜索 |
| **Web 界面** | React + TypeScript + Vite | 现代化前端 |
| **代码编辑** | Monaco Editor | 浏览器端 IDE |
| **可观测性** | LangSmith | 调用链路追踪 |
| **容器化** | Docker + Docker Compose | 一键部署 |

## 项目结构

```
DevMate/
├── src/devmate/              # Python 源码
│   ├── agent.py              # Agent 主循环、工具编排
│   ├── api.py                # REST API 服务
│   ├── cli.py                # CLI 命令行工具
│   ├── mcp_server.py         # MCP Server (search_web)
│   ├── mcp_client.py         # MCP Client (streamable HTTP)
│   ├── rag.py                # Qdrant 向量检索
│   ├── skills.py             # Skills 加载与匹配
│   ├── skills_verify.py      # Skills 规范校验
│   └── skill_learning.py     # 自动学习新技能
│
├── frontend/                  # React 前端
│   ├── src/
│   │   ├── api/              # API 调用与 SSE 流处理
│   │   ├── components/       # React 组件
│   │   │   ├── AgentFlow.tsx # Agent 流程可视化
│   │   │   └── FileManager.tsx # 文件管理器
│   │   └── ...
│   └── package.json
│
├── docs/                      # 本地知识库文档
├── examples/skills/           # 示例技能目录
├── .skills/                   # 学习到的技能存储
├── workspace/                 # Agent 生成的项目文件
├── config.toml                # 配置文件
├── pyproject.toml             # Python 依赖
├── docker-compose.yml          # Docker 编排
├── Dockerfile                 # 容器镜像
└── README.md
```

## 快速开始

### 前置要求

- Python `3.13`
- `uv` (环境与依赖管理)
- Docker 和 Docker Compose

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置 API Key

编辑 `config.toml` 或使用环境变量：

```bash
# 方式一：直接编辑 config.toml（不推荐提交到 Git）
# [model.chat]
# api_key = "your-deepseek-api-key"

# 方式二：环境变量（推荐）
export DEEPSEEK_API_KEY="your-deepseek-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
export LANGSMITH_API_KEY="your-langsmith-api-key"
```

### 3. 启动服务（Docker Compose）

```bash
docker compose up -d
```

这将启动以下服务：

| 服务 | 端口 | 说明 |
|------|------|------|
| `qdrant` | 6333/6334 | 向量数据库 |
| `devmate-mcp-search` | 3000 | MCP 搜索服务 |
| `devmate-api` | 8000 | REST API |
| `frontend` | 5173 | Web 界面 |

### 4. 本地开发模式

```bash
# 终端 1: 启动 Qdrant
docker compose up -d qdrant

# 终端 2: 启动 MCP Server
uv run devmate-mcp-search

# 终端 3: 启动 API
uv run devmate-api

# 终端 4: 启动前端
cd frontend && npm install && npm run dev
```

### 5. 文档入库（可选）

```bash
uv run devmate-rag-ingest
```

### 6. 运行 Agent

**CLI 方式：**

```bash
uv run devmate --prompt "我想构建一个展示附近徒步路线的网站项目。"
```

**API 方式：**

```bash
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "我想构建一个展示附近徒步路线的网站项目。"}'
```

**Web 界面：**

打开 http://localhost:5173 访问可视化界面。

## 配置说明

`config.toml` 主要配置项：

```toml
[model.chat]
provider = "deepseek"
base_url = "https://api.deepseek.com/v1"
api_key = "${DEEPSEEK_API_KEY}"   # 推荐使用环境变量
model_name = "deepseek-chat"

[model.embedding]
base_url = "https://api.siliconflow.cn/v1"
api_key = "${SILICONFLOW_API_KEY}"
model_name = "BAAI/bge-m3"

[search]
tavily_api_key = "${TAVILY_API_KEY}"

[langsmith]
langchain_tracing_v2 = true
langchain_api_key = "${LANGSMITH_API_KEY}"

[skills]
skills_dir = ".skills"
extra_skill_dirs = ["examples/skills"]

[mcp]
url = "http://devmate-mcp-search:3000/mcp"

[qdrant]
url = "http://qdrant:6333"

[app]
workspace_dir = "./workspace"
```

## Agent Skills

Agent Skills 允许 DevMate 从成功执行的任务中学习，形成可复用的技能模式。

### 工作原理

1. **学习**：成功生成文件后，Agent 会自动将任务模式写入 `.skills/<slug>/SKILL.md`
2. **复用**：下次发起语义相近的请求时，Agent 会自动匹配并应用相关技能
3. **校验**：使用官方 deepagents Skills 规范

### 校验 Skills

```bash
uv run devmate-verify-skills
```

### 添加示例技能

将 [anthropics/skills](https://github.com/anthropics/skills) 中的技能目录复制到 `.skills/` 或 `extra_skill_dirs` 指定的目录。

## API 接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/healthz` | 健康检查 |
| GET | `/workspace` | 列出工作区文件 |
| GET | `/workspace/{path}` | 读取文件内容 |
| POST | `/workspace` | 创建新文件 |
| PUT | `/workspace/{path}` | 更新文件 |
| DELETE | `/workspace/{path}` | 删除文件 |
| POST | `/run` | 运行 Agent（非流式） |
| POST | `/run/stream` | 运行 Agent（流式 SSE） |

## 代码规范

```bash
# 检查代码格式
uvx ruff check .
uvx black --check .

# 自动修复
uvx black .
uvx ruff check --fix .
```

## 常见问题

### Q: MCP Server 连接失败？

确保 `devmate-mcp-search` 容器已启动：

```bash
docker compose logs devmate-mcp-search
```

### Q: Qdrant 向量检索失败？

检查 Qdrant 服务状态：

```bash
docker compose logs qdrant
curl http://localhost:6333/readyz
```

### Q: 如何查看 Agent 执行日志？

启动时添加 `--verbose` 或查看 LangSmith Trace：

```bash
uv run devmate --prompt "..." --verbose
```

## 注意事项

- 不要将真实 API Key 提交到仓库（使用环境变量或 `.env` 文件）
- 建议将 `config.toml` 添加到 `.gitignore`
- 交付时可提供 LangSmith Trace 分享链接作为可观测性证据

## 许可证

MIT License

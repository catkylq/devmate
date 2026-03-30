# DevMate Frontend

DevMate 的现代化前端界面，基于 React + TypeScript + Vite 构建。

## 功能特性

- **Agent 流程可视化**：实时显示 AI Agent 的执行步骤和状态
- **流式输出**：实时显示 Agent 的思考过程和消息
- **文件管理器**：完整支持创建、编辑、删除代码文件
- **代码编辑器**：集成 Monaco Editor，支持语法高亮
- **响应式设计**：现代化深色主题 UI

## 技术栈

- React 18
- TypeScript
- Vite
- Monaco Editor (代码编辑)
- Lucide React (图标)

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

前端将运行在 http://localhost:3000

### 3. 启动后端服务

确保 DevMate 后端服务运行在 http://localhost:8000

```bash
# 在项目根目录
cd DevMate
uv sync
uv run devmate-api
```

## 项目结构

```
frontend/
├── src/
│   ├── api/           # API 调用和 SSE 流处理
│   ├── components/    # React 组件
│   │   ├── AgentFlow.tsx    # Agent 流程显示
│   │   └── FileManager.tsx  # 文件管理器
│   ├── hooks/         # 自定义 React Hooks
│   ├── styles/         # CSS 样式文件
│   ├── types/          # TypeScript 类型定义
│   ├── App.tsx         # 主应用组件
│   └── main.tsx        # 应用入口
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## API 接口

前端通过 Vite 代理连接后端 API：

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/healthz | 健康检查 |
| GET | /api/workspace | 列出工作区文件 |
| GET | /api/workspace/{path} | 读取文件内容 |
| POST | /api/workspace | 创建新文件 |
| PUT | /api/workspace/{path} | 更新文件 |
| DELETE | /api/workspace/{path} | 删除文件 |
| POST | /api/run | 运行 Agent (非流式) |
| POST | /api/run/stream | 运行 Agent (流式) |

## 使用说明

### 发送请求

1. 在左侧输入框输入你的请求
2. 点击"发送"按钮或按 Ctrl+Enter
3. Agent 开始执行，流程会实时显示
4. 执行完成后，可以在右侧"文件"面板查看生成的文件

### 管理文件

1. 在右侧面板切换到"文件"标签
2. 点击文件名查看和编辑
3. 修改后点击"保存"
4. 使用"新建"按钮创建新文件
5. 选中文件后可以删除

## 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

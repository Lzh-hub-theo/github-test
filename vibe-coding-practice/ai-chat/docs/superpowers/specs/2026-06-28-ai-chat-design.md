# AI Chat 项目设计文档

## 概述

基于 Python + LangChain 的 AI 对话应用，包含 FastAPI 后端和精美静态前端，支持多轮对话和流式响应。

## 技术选型

- **后端**: Python 3 + FastAPI + LangChain + ChatOpenAI
- **前端**: 单文件 HTML/CSS/JS（frontend-design 技能生成）
- **LLM**: OpenAI GPT API
- **通信**: SSE (Server-Sent Events) 流式传输

## 文件结构

```
ai-chat/
├── main.py          # FastAPI 后端 + LangChain 逻辑
├── index.html       # 前端界面
└── .env             # OPENAI_API_KEY 配置
```

## 架构设计

### 后端 (main.py)

- FastAPI 应用，启动时加载 `.env` 中的 `OPENAI_API_KEY`
- LangChain `ChatOpenAI` + `ConversationBufferMemory` 管理多轮对话
- 内存存储对话历史，每个浏览器会话维护独立的对话链

### API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 返回前端页面 |
| POST | `/chat` | 流式对话接口（SSE） |

### 前端 (index.html)

- 单文件 HTML/CSS/JS，由 frontend-design 技能生成精美界面
- 通过 `fetch` + `ReadableStream` 接收 SSE 流式响应
- 聊天气泡式布局，支持输入框发送消息

## 数据流

1. 用户输入消息 → 前端发送 `POST /chat`（body: `{message, session_id}`）
2. 后端根据 `session_id` 获取或创建该会话的 `ConversationChain`
3. LangChain 调用 OpenAI API，通过 SSE 逐 token 流式返回
4. 前端实时渲染 AI 回复到聊天气泡中
5. `ConversationBufferMemory` 自动维护历史上下文

## 会话管理

- 后端用字典 `dict[str, ConversationChain]` 存储各会话的对话链
- 前端首次访问时生成随机 `session_id`（UUID），后续请求携带
- 服务重启后所有会话清空

## 依赖

- fastapi
- uvicorn
- langchain
- langchain-openai
- python-dotenv
- sse-starlette

## 运行方式

```bash
pip install fastapi uvicorn langchain langchain-openai python-dotenv sse-starlette
# 在 .env 中填入 OPENAI_API_KEY=sk-xxx
python main.py
# 浏览器访问 http://localhost:8000
```

## 错误处理

- API Key 缺失 → 启动时提示
- OpenAI 调用失败 → 前端显示错误消息
- 会话不存在 → 自动创建新会话

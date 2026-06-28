# AI Chat

基于 Python + LangChain 的 AI 对话应用，支持多轮对话与流式响应，前后端一体，开箱即用。

![alt text](<屏幕截图 2026-06-28 205324.png>)

## 功能

- 多轮对话上下文记忆
- 流式响应，逐字输出
- 暗色精美聊天界面
- 支持任意 OpenAI 兼容 API（OpenAI、MiniMax、DeepSeek 等）

## 技术栈

- **后端**: Python 3 + FastAPI + LangChain
- **前端**: 单文件 HTML/CSS/JS
- **通信**: NDJSON 流式传输

## 项目结构

```
ai-chat/
├── main.py       # FastAPI 后端 + LangChain 对话逻辑
├── index.html    # 前端聊天界面
├── .env          # API 配置（需自行填写）
```

## 快速开始

### 1. 安装依赖

```bash
pip install fastapi uvicorn langchain langchain-openai python-dotenv
```

### 2. 配置 .env

复制并编辑配置文件：

```env
OPENAI_API_KEY=你的API密钥
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-3.5-turbo
```

**常用 API 配置示例：**

| 平台 | OPENAI_BASE_URL | MODEL_NAME |
|------|----------------|------------|
| OpenAI | `https://api.openai.com/v1` | `gpt-3.5-turbo` |
| MiniMax | `https://api.minimax.chat/v1` | `MiniMax-Text-01` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| 本地 Ollama | `http://localhost:11434/v1` | `llama3` |

### 3. 启动服务

```bash
python main.py
```

### 4. 访问

浏览器打开 http://localhost:8000

## API 接口

### POST /chat

流式对话接口，返回 NDJSON 格式数据。

**请求体：**

```json
{
  "message": "你好",
  "session_id": "可选，不传则自动生成"
}
```

**响应（逐行返回）：**

```json
{"type": "content", "content": "你", "session_id": "xxx"}
{"type": "content", "content": "好", "session_id": "xxx"}
{"type": "done", "session_id": "xxx"}
```

**错误响应：**

```json
{"type": "error", "error": "错误信息", "session_id": "xxx"}
```

## 配置项

| 环境变量 | 必填 | 说明 |
|---------|------|------|
| `OPENAI_API_KEY` | 是 | API 密钥 |
| `OPENAI_BASE_URL` | 否 | API 地址，默认为 OpenAI 官方 |
| `MODEL_NAME` | 否 | 模型名称，默认 `gpt-3.5-turbo` |

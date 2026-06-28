import os
import json
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

load_dotenv()

app = FastAPI()

# 会话存储: session_id -> list[BaseMessage]
sessions: dict[str, list] = {}

llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "gpt-3.5-turbo"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    streaming=True,
    temperature=0.7,
)

SYSTEM_PROMPT = SystemMessage(content="你是一个友好的AI助手，请用中文回答问题。")


def get_or_create_history(session_id: str) -> list:
    """获取或创建指定会话的消息历史"""
    if session_id not in sessions:
        sessions[session_id] = [SYSTEM_PROMPT]
    return sessions[session_id]


@app.get("/", response_class=HTMLResponse)
async def index():
    """返回前端页面"""
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/chat")
async def chat(request: Request):
    """流式对话接口，使用 NDJSON 格式"""
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id", "")

    if not message.strip():
        return JSONResponse({"error": "消息不能为空"}, status_code=400)

    if not session_id:
        session_id = str(uuid.uuid4())

    history = get_or_create_history(session_id)
    history.append(HumanMessage(content=message))

    async def stream_generator():
        collected_content = ""
        try:
            async for chunk in llm.astream(history):
                content = chunk.content
                if content:
                    collected_content += content
                    line = json.dumps(
                        {"type": "content", "content": content, "session_id": session_id},
                        ensure_ascii=False,
                    )
                    yield line + "\n"

            # 将完整的 AI 回复加入历史
            history.append(AIMessage(content=collected_content))

            done_line = json.dumps(
                {"type": "done", "session_id": session_id},
                ensure_ascii=False,
            )
            yield done_line + "\n"

        except Exception as e:
            error_line = json.dumps(
                {"type": "error", "error": str(e), "session_id": session_id},
                ensure_ascii=False,
            )
            yield error_line + "\n"

    return StreamingResponse(
        stream_generator(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "sk-your-api-key-here":
        print("错误: 请在 .env 文件中设置有效的 OPENAI_API_KEY")
        exit(1)

    base_url = os.getenv("OPENAI_BASE_URL")
    model_name = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    print(f"API Base URL: {base_url or 'https://api.openai.com/v1'}")
    print(f"Model: {model_name}")

    print("AI Chat 服务启动中...")
    print("访问 http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

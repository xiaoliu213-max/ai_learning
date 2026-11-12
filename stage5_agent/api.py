from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessageChunk
from starlette.responses import StreamingResponse
from agent_core import agent
import json
app=FastAPI()


#会话储存，{session_id: [消息列表]}   ← 内存版，重启就没了
SESSIONS:dict[str,list]={}

class ChatIn(BaseModel):
    session_id: str
    message: str

class ChatOut(BaseModel):
    reply:str

@app.post("/chat",response_model=ChatOut)
def chat(body: ChatIn):

    history=SESSIONS.get(body.session_id,[])
    #加入用户的问题
    history.append(HumanMessage(content=body.message))

    result=agent.invoke({"messages":history},config={"recursion_limit":10})

    SESSIONS[body.session_id]=[m for m in result["messages"] if m.type !="system"]

    return ChatOut(reply=SESSIONS[body.session_id][-1].content)


@app.post("/chat/stream")
async def chat_stream(body: ChatIn):
    history=SESSIONS.get(body.session_id,[])
    history.append(HumanMessage(content=body.message))

    async def gen():
        final_messages=None

        async for mode,payload in agent.astream(
                {"messages":history},
            stream_mode=["messages","values"],
            config={"recursion_limit":10},

        ):
            if mode=="messages":
                chunk,_meta=payload
                if isinstance(chunk,AIMessageChunk) and isinstance(chunk.content,str) and chunk.content:

                    #只推送有文字的ai片段；工具调用的content是空的
                    yield f"data: {json.dumps({'t':chunk.content},ensure_ascii=False)}\n\n"

            elif mode=="values":
                final_messages=payload.get("messages")
        #流完了就再存历史
        if final_messages:
            SESSIONS[body.session_id]=[m for m in final_messages if m.type != "system"]

        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(),media_type="text/event-stream")
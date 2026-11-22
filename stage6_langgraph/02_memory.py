import json
import os
from datetime import date, timedelta
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver


load_dotenv()

TODAY = date.today()


#假数据代替数据库
BOOKS={
    "三体":{"available":True,"copies":2,"floor":"3楼"},
    "活着":{"available":False,"copies":0,"floor":"2楼"}
}

LOANS = {
    "2023001": [
        {"title": "三体", "due_date": TODAY + timedelta(days=2)},   # 快到期
        {"title": "活着", "due_date": TODAY - timedelta(days=9)},   # 已逾期 9 天
    ],
}


@tool
def get_book_status(title:str)->dict:
    """查一本书的馆藏状态。模型看得到 description，看不到这个函数体。"""
    if title in BOOKS:
        return BOOKS[title]
    return {"error": f"馆藏中没有《{title}》"}


@tool
def get_my_loans(student_id:str)->dict:
    """查询某个学号当前在借的所有图书：到期日、剩余天数、是否逾期、应缴滞纳金。
       当用户问「我的书什么时候到期 / 有没有逾期 / 要交多少钱」时使用。"""
    if student_id not  in LOANS:
        return {"error":f"没有找到学号{student_id}的记录"}

    loans=[]
    for item in LOANS[student_id]:
        days_left=(item["due_date"]-TODAY).days
        overdue=days_left<0
        fine=min(round(-days_left*0.5,2),20.0) if overdue else 0.0
        loans.append(
            {
                "title":item["title"],
                "due_date": item["due_date"].isoformat(),
                "days_left": days_left,
                "overdue": overdue,
                "fine": fine,
            }
        )
    return loans


TOOLS=[get_book_status,get_my_loans]

TOOL_MAP={m.name: m for m in TOOLS}

llm=ChatOpenAI(
    model=os.environ["DEEPSEEK_MODEL"],
    api_key=os.environ["DEEPSEEK_API_KEY"],
    temperature=0,
    base_url=os.environ["DEEPSEEK_BASE_URL"],
).bind_tools(TOOLS)


# ============ ① 状态：整张图共享的那份数据 ===========
class AgentState(TypedDict):
    messages: Annotated[list,add_messages]


# ============ ② 节点 1：chat（调模型） ============
def chat_node(state:AgentState):
    ai=llm.invoke(state["messages"])
    return {"messages":[ai]}

# ============ ③ 节点 2：tools（执行工具） ============
def tools_node(state:AgentState):
    last=state["messages"][-1]
    outputs=[]
    for call in last.tool_calls:
        print(f"模型要求调用:{call['name']}({call['args']})")
        t=TOOL_MAP[call["name"]]
        result=t.invoke(call["args"])
        outputs.append(
            ToolMessage(
                content=json.dumps(result,ensure_ascii=False),
                tool_call_id=call["id"]
            )
        )
    return {"messages":outputs}  #增量：只追加这几条回执

# ============ ④ 条件边：要不要调工具 ============
def should_continue(state:AgentState):
    last=state["messages"][-1]
    if getattr(last,"tool_calls",None):
        return "tools"
    return END

# ============ ⑤ 组装：节点 + 边 ============
graph=StateGraph(AgentState)
graph.add_node("chat",chat_node)
graph.add_node("tools",tools_node)

graph.add_edge(START,"chat") #入口：先进chat
graph.add_conditional_edges("chat",should_continue)  #chat之后看判断
graph.add_edge("tools","chat")  #tools干完固定回chat

#
app=graph.compile(checkpointer=InMemorySaver())
print("图的类型: ",type(app).__name__)


config={"recursion_limit":10,
        "configurable":{"thread_id":"u1"}}


while(True):
    q=input("我： ")
    if q in ("退出","exit"):
        break

    result = app.invoke(
        {"messages": [HumanMessage(content=q)]},
       config
    )
    print("最终回答：", result["messages"][-1].content)


"""

result=app.invoke(
{"messages":[HumanMessage(content="在几楼？")]},
    #{"messages":[HumanMessage(content="《三体》能借吗？")]},
)
print("最终回答：",result["messages"][-1].content)

"""





















import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from openai import base_url

load_dotenv()

llm=ChatOpenAI(
    model=os.environ["DEEPSEEK_MODEL"],
    api_key=os.environ["DEEPSEEK_API_KEY"],
    temperature=0,
    base_url=os.environ["DEEPSEEK_BASE_URL"],
)
#========定义状态
class RoterState(TypedDict):

    messages:Annotated[list,add_messages]

    route:str

#======分类节点
CLASSIFY_PROMPT = """判断用户问题属于哪一类，只输出一个词：
book —— 问某本书能不能借、在馆几本、在几楼
loan —— 问某个学号借了哪些书、是否逾期、滞纳金
rag  —— 问借阅规则、逾期规则、开放时间等制度问题

只输出 book / loan / rag 三者之一，不要输出任何别的字。"""


def classify_node(state:RoterState):
    q=state["messages"][-1].content
    response=llm.invoke(
        [SystemMessage(content=CLASSIFY_PROMPT),HumanMessage(content=q)],
    )
    route=response.content.strip().lower()
    #白名单兜底
    if route not in ("book","loan","rag"):
        print(f"模型输出你唱：{route!r},兜底为rag")
        route="rag"
    print(f"[classify]{q}->{route}")

    return {"route":route} #更改了信息

def book(state:RoterState):
   return  {"messages": [AIMessage(content="[book 分支] 这里将来查馆藏")]}

def loan(state:RoterState):
    return {"messages": [AIMessage(content="[loan 分支] 这里将来查借阅记录")]}

def rag(state:RoterState):
    return {"messages": [AIMessage(content="[rag 分支] 这里将来检索规则文档")]}

#=====路由函数
def route_after_classify(state:RoterState):
    return state["route"]


#=====组装
graph=StateGraph(RoterState)

graph.add_node("classify",classify_node)
graph.add_node("book",book)
graph.add_node("loan",loan)
graph.add_node("rag",rag)

#组装边
graph.add_edge(START,"classify")

#映射表，由函数的返回值-》节点函数
graph.add_conditional_edges(
    "classify",
    route_after_classify,
    {"book":"book","loan":"loan","rag":"rag"},
)

graph.add_edge("book",END)
graph.add_edge("loan",END)
graph.add_edge("rag",END)


app=graph.compile()

#=======跑三个问题
Questions=[
    "《三体》能借吗？",
    "学号 2023001，我借的书逾期了吗？",
    "逾期一天要交多少钱？",
]

for q in Questions:
    print("===============\n")
    print(f"问题{q}")
    result=app.invoke({"messages":[HumanMessage(content=q)]})
    print("回答：",result["messages"][-1].content)

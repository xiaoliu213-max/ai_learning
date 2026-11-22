
from datetime import date, timedelta

from typing import Annotated, TypedDict

from dotenv import load_dotenv

from langgraph.types import Command

from langgraph.graph import END, START, StateGraph


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



class AgentState(TypedDict):
   score:int
   result: str

#=========

def score_node(state:AgentState):
    score=int(input("请输入你的分数"))
    goto="fail"
    if score >= 60:
        goto="success"
    return Command(
        update={"score":score},
        goto=goto,
    )

def success_node(state:AgentState):
    return {"result":"恭喜你通过考试"}


def fail_node(state:AgentState):

    return {"result":"fail"}


#============node
graph=StateGraph(AgentState)
graph.add_node("score_node",score_node)
graph.add_node("success",success_node)
graph.add_node("fail",fail_node)

#======edge
graph.add_edge(START,"score_node")
graph.add_edge("success",END)
graph.add_edge("fail",END)


app=graph.compile()
result=app.invoke({})
print("最终答案: ",result)

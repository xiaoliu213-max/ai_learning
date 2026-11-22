from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt

class HITLState(TypedDict):
    messages: Annotated[list,add_messages]

def reserve_node(state:HITLState):
    print("[reserve]准备预约......")

    decision=interrupt(
        {
            "action":"reserve_book",
            "title":"三体",
            "question":"要预约《三体》吗？（yes/no)",
        }
    )
    print(f"[reserve]人工决定：{decision}")

    if decision == "yes":
        return {"messages":[AIMessage(content="已帮你预约《三体》,取书时请带校园卡。")]}
    return {"messages":[AIMessage(content="好的，已取消预约")]}


graph=StateGraph(HITLState)

graph.add_node("reserve",reserve_node)

config= {"configurable": {"thread_id": "u1"}}

graph.add_edge(START,"reserve")
graph.add_edge("reserve",END)

app=graph.compile(checkpointer=InMemorySaver())

result=app.invoke({"messages":[HumanMessage(content="帮我预约《三体》")]},
                  config
                  )

if "__interrupt__" in result:
    payload=result["__interrupt__"][0].value
    print("\n需要人工确认：",payload)
    answer=input("你的决定(yes/no)：").strip().lower()
    result=app.invoke(Command(resume=answer),config)


print("\n最终回答: ",result["messages"][-1].content)



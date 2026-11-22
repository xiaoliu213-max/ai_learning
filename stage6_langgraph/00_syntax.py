from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages:list
    step:int

def node_a(state: State) -> State:
    print("A 收到：", state)
    return {"messages": state["messages"] + ["A 的输出"], "step": state["step"] + 1}


s: State = {"messages": ["用户问题"], "step": 0}
s2 = node_a(s)
print("A 之后：", s2)

def merge_like_default(old:dict,new:dict)->dict:
    """节点返回的字典，按'键'合并：出现的键覆盖旧值，没出现的保留"""
    result=dict(old)
    result.update(new)
    return result

state = {"messages": ["用户问题"], "step": 0}
new = {"messages": ["B 的输出"]}        # B 节点只返回自己的 messages
print("合并后：", merge_like_default(state, new))


result = add_messages(["旧消息"], ["新消息"])
print("追加后：", [m.content for m in result])



class State2(TypedDict):
    messages: Annotated[list, add_messages]   # 类型=list，合并规则=追加
    step: int                                  # 没贴标签 → 默认覆盖

s1: State2 = {"messages": ["用户问题"], "step": 0}
def noted_B(state: State2) -> State:
    return {"messages": ["我是B说的"],"step": 1}
print("==============================")
s2= noted_B(s1)
print("A 之后：", s2)
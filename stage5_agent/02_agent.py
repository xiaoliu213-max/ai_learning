import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from datetime import date, timedelta

TODAY = date.today()

load_dotenv()

client=OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url=os.environ["DEEPSEEK_BASE_URL"],
)
MODEL=os.environ[("DEEPSEEK_MODEL")]

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



def get_book_status(title:str)->dict:
    """查一本书的馆藏状态。模型看得到 description，看不到这个函数体。"""
    if title in BOOKS:
        return BOOKS[title]
    return {"error": f"馆藏中没有《{title}》"}


def get_my_loans(student_id:str)->dict:
    """查某个学号当前在借的书、到期时间、是否逾期、滞纳金。"""
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




TOOLS=[
    {
        "type":"function",
        "function":{
            "name":"get_book_status",
            "description":"查询某本书当前是否可借,在馆数量,所在楼层。书名必须完整",
            "parameters":{
                "type":"object",
                "properties":{
                    "title":{
                        "type":"string",
                        "description":"书名，例如，三体"
                      }
                },
                "required":["title"]
            }
        }
    },
{
    "type": "function",
    "function": {
        "name": "get_my_loans",
        "description": "查询某个学号当前在借的所有图书，包括到期日、剩余天数、是否逾期、应缴滞纳金。当用户问“我的书什么时候到期/有没有逾期/要交多少钱”时使用。",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "学号，例如：2023001",
                }
            },
            "required": ["student_id"],
        },
    },
}
]


SYSTEM_PROMPT = """你是一个校园图书馆助手。

工具使用规则：
1. 只能通过提供的工具获取数据。涉及馆藏、借阅、逾期、滞纳金的问题，不要凭自己的知识回答。
2. 没有对应的工具时，直接回答「这个我查不了」，不要承诺后续操作。
3. 调用工具前如果缺少必要参数（比如学号），先向用户询问，不要自己编。
4. 回答用中文，简洁；涉及逾期时，把逾期天数和应缴金额说清楚。"""


TOOL_FUNCS = {
    "get_book_status": get_book_status,
    "get_my_loans": get_my_loans,
}

messages = [{"role": "system", "content": SYSTEM_PROMPT}]

while True:
    q=input("我：")
    if q in ("退出","exit"):
        break

    messages.append({"role": "user", "content":q})

    for step in range(1,4):
        print(f"\n=========第{step}轮=======")

        resp=client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )
        msg=resp.choices[0].message

        print("finish_reason:", resp.choices[0].finish_reason)
        print("content:", msg.content)

        #没有 tool_calls = 模型说完了，这是循环的正常出口
        if not msg.tool_calls:
            print("模型最终回答:",msg.content)
            break

        #没有被拦住，说明模型需要调用工具
        #把模型调用工具“这条消息记进对话,先转化为字典，把None的字段去掉
        messages.append(msg.model_dump(exclude_none=True))

        for call in msg.tool_calls:
            #1拆解参数,先变成子带你
            print("原始参数（字符串）：", call.function.arguments)
            args=json.loads(call.function.arguments)
            # 2. 真正执行本地 Python 函数
            print(f"模型要求调用：{call.function.name}({args})")

            func = TOOL_FUNCS[call.function.name]
            result = func(**args)


            print("我们执行得到：", result)

            #3按照严格格式，把结果挂到对话列表
            messages.append(
                {
                    "role":"tool",
                    "tool_call_id":call.id,
                    "content":json.dumps(result,ensure_ascii=False)
                }
            )
    else:#只有在循环没有被打断的时候才会执行else
        print("达到最大轮数，强制停止")



"""def run(question:str):
    messages=[{"role":"user","content":question}]

    for step in range(1,4):
        print(f"\n=========第{step}轮=======")

        resp=client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )
        msg=resp.choices[0].message

        print("finish_reason:", resp.choices[0].finish_reason)
        print("content:", msg.content)

        #没有 tool_calls = 模型说完了，这是循环的正常出口
        if not msg.tool_calls:
            print("模型最终回答:",msg.content)
            return 

        #没有被拦住，说明模型需要调用工具
        #把模型调用工具“这条消息记进对话,先转化为字典，把None的字段去掉
        messages.append(msg.model_dump(exclude_none=True))

        for call in msg.tool_calls:
            #1拆解参数,先变成子带你
            print("原始参数（字符串）：", call.function.arguments)
            args=json.loads(call.function.arguments)
            # 2. 真正执行本地 Python 函数
            print(f"模型要求调用：{call.function.name}({args})")

            result=get_book_status(**args)

            print("我们执行得到：", result)

            #3按照严格格式，把结果挂到对话列表
            messages.append(
                {
                    "role":"tool",
                    "tool_call_id":call.id,
                    "content":json.dumps(result,ensure_ascii=False)
                }
            )

    print("达到最大轮数，强制停止")


if __name__ == "__main__":
    run("《活着》能借吗？")"""

import json
import os
from datetime import date, timedelta

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent


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



llm=ChatOpenAI(
    model=os.environ.get("DEEPSEEK_MODEL"),
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url=os.environ.get("DEEPSEEK_BASE_URL"),
    temperature=0
)

#系统提示词

SYSTEM_PROMPT = """你是一个校园图书馆助手。

工具使用规则：
1. 只能通过提供的工具获取数据。涉及馆藏、借阅、逾期、滞纳金的问题，不要凭自己的知识回答。
2. 没有对应的工具时，直接回答「这个我查不了」，不要承诺后续操作。
3. 调用工具前如果缺少必要参数（比如学号），先向用户询问，不要自己编。
4. 回答用中文，简洁；涉及逾期时，把逾期天数和应缴金额说清楚。
5.只回答用户当前问的问题，不要重复之前的查询结果，除非用户明确要求"""

agent=create_agent(
    model=llm,
    tools=[get_book_status, get_my_loans],
    system_prompt=SYSTEM_PROMPT,
)

import os
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


llm=ChatOpenAI(
    model=os.environ["DEEPSEEK_MODEl"],
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url=os.environ["DEEPSEEK_BASE_URL"],
    temperature=0
)


#=================demo1=========
class Announcement(BaseModel):
    title:str=Field(description="公告标题")
    start_date:str=Field(description="生效日期，格式YYYY-MM-DD,没有则填没有")
    action:str=Field(description="公告要求读者做什么")


structured=llm.with_structured_output(Announcement,method="function_calling")

text = """图书馆公告：自 2026-12-01 起，自助打印机暂停服务两周。
读者如需打印学习资料，请前往一楼服务台人工办理。"""

info=structured.invoke([HumanMessage(content=text)])
print("标题：", info.title)
print("日期：", info.start_date)
print("动作：", info.action)


#================demo2
class Route(BaseModel):
    category: Literal["book","rag","loan","other"]=Field(
        description="book=馆藏问题; loan=借阅记录; rag=规则制度; other=都不属于"

    )

route=llm.with_structured_output(Route,method="function_calling")
for q in [
    "《三体》能借吗？",
    "学号 2023001，我借的书逾期了吗？",
    "逾期一天要交多少钱？",
    "今天天气怎么样？",  # ← 故意问一个无关的
]:
    r=route.invoke([HumanMessage(content=q)])
    print(f"{q}->{r.category}")



#========demo 3================
plain_prompt= """判断用户问题属于哪一类，只输出一个词：book / loan / rag。
只输出这三个词之一，不要输出任何别的字。"""
print("\n--普通llm问一个无关问题----")
print(llm.invoke(plain_prompt+"\n\n问题：今天天气怎么样？").content)
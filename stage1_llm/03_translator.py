import os
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url=os.environ["DEEPSEEK_BASE_URL"],
)
MODEL = os.environ["DEEPSEEK_MODEL"]

SYSTEM_PROMPT="""你是一名专业的中英翻译

规则：
1；只输出英文加译文，不要输出任何解释注释和原文
2：不要加引号，不要加[译文：]这样的前缀
3：保持原文的语气和格式


示例：

输入：今天天气很好。
输出：The weather is nice today.


输入：请把这份报告发给张经理。
输出：Please send this report to Manager Zhang.
"""
def translate(text):
    response=client.chat.completions.create(
        model=MODEL,
        temperature=0,
        max_tokens=500,
        messages=[
            {'role':"system",'content':SYSTEM_PROMPT},
            {'role':"user",'content':text},
        ],
    )
    return response.choices[0].message.content.strip()
# strip 去掉收尾空白


SAMPLES = [
    "这本书我看了三遍，每次都有新的感受。",
    "系统将于今晚 23:00 进行维护，预计持续 30 分钟。",
    "请勿在电梯内吸烟。",
]
for s in SAMPLES:
     print(f"原文： {s}")
     print(translate(s))
     print("-"*50)
import os

import sys
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()


client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url=os.environ["DEEPSEEK_BASE_URL"],
)
MODEL = os.environ["DEEPSEEK_MODEL"]

SYSTEM_PROMPT="""你是一个图书信息抽取器

任务： 从用户给的一端文字里，抽取书名，作者，价格

约束：
1. 只输出一个 JSON 对象，不要输出任何解释文字
2. 不要用 Markdown 代码块包裹（不要出现三个反引号）
3. 字段固定为：title（字符串）、author（字符串）、price（数字）
4. 原文里找不到的字段，值填 null，不要编造


示例：
输入：我在书店看到《活着》余华著，定价 28.00 元。
输出：{"title": "活着", "author": "余华", "price": 28.0}
"""


def extract(text):
    response=client.chat.completions.create(
        model=MODEL,
        temperature=0,
        max_tokens=500,
        messages=[
            {"role":"system","content":SYSTEM_PROMPT},
            {"role":"user","content":text},
        ]
    )
    return response.choices[0].message.content.strip()


print("=" * 62)
print("单次抽取：看原始返回 + 解析结果")
print("=" * 62)

SAMPLES = [
    "《三体》是刘慈欣写的，售价 23 元。",
    "书店新到《人类简史》，尤瓦尔·赫拉利著，标价 68.00 元。",
    "《活着》卖 28 元。",
    "我在看一本叫《三体》的书。",
]
for s in SAMPLES:
     raw=extract(s)
     print(f"原文：{s}")
     print(f"原始返回{raw}")
     try:
         data=json.loads(raw)
         print(f"解析成功-》书名={data['title']}/ 作者={data['author']} / 价格={data['price']}")
     except json.JSONDecodeError as e:
         print(f"解析失败:{e}")

#压力测试

ok=0
for i in range(10):
    raw=extract(SAMPLES[0])
    try:
        json.loads(raw)
        ok+=1
        print(f"第{i+1}次：[ok]")
    except json.JSONDecodeError:
        print(f"第 {i + 1} 次: [FAIL] {raw[:60]}")


print(f"\n结果：{ok}/10 次返回合法 JSON")


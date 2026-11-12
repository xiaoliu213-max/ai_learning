import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url=os.environ["DEEPSEEK_BASE_URL"],
)

response = client.chat.completions.create(
    model=os.environ["DEEPSEEK_MODEL"],
    messages=[
        {"role": "system", "content": "你是一个简洁的助手，回答不超过两句话。"},
        {"role": "user", "content": "用一句话解释什么是 REST API。"},
    ],
)

print("模型回答：", response.choices[0].message.content)
print("本次消耗 token：", response.usage.total_tokens)

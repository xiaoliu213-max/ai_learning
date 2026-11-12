import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url=os.environ["DEEPSEEK_BASE_URL"],
)
MODEL = os.environ["DEEPSEEK_MODEL"]


def ask(messages, temperature=1.0, max_tokens=800):
    """统一入口：发一次请求，返回 (回答文本, 停止原因, 用量)"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    choice = response.choices[0]
    return choice.message.content, choice.finish_reason, response.usage


def line(title):
    print("\n" + "=" * 62)
    print(title)
    print("=" * 62)


QUESTION = "什么是 REST API？"

line("实验 1 · system 决定模型「是谁」")
for label, system in [
    ("简洁助手", "你是一个简洁的助手，回答不超过两句话。"),
    ("唠叨教授", "你是一个爱唠叨的老教授，开口必须先说「年轻人啊」，"
                 "然后至少讲三点，每点不少于两句。"),
]:
    answer, finish, usage = ask([
        {"role": "system", "content": system},
        {"role": "user", "content": QUESTION},
    ])
    print(f"\n--- system = {label} ---")
    print(answer)
    print(f"[completion_tokens = {usage.completion_tokens}]")


line("实验 2 · 没有 assistant，模型就「失忆」")
FOLLOW_UP = "那它有什么缺点？"

answer, _, _ = ask([{"role": "user", "content": FOLLOW_UP}])
print("\n--- A. 只发追问（不带历史）---")
print(answer)

answer, _, _ = ask([
    {"role": "user", "content": QUESTION},
    {"role": "assistant", "content": "REST API 是一种基于 HTTP 协议的接口设计风格，"
                                    "用 URL 标识资源、用标准方法操作资源，交互无状态。"},
    {"role": "user", "content": FOLLOW_UP},
])
print("\n--- B. 带上历史（含 assistant 那条）---")
print(answer)




line("实验 3 · temperature 控制随机性")
NAME_PROMPT = [{"role": "user", "content": "给一家书店起个名字，只输出名字，不要解释。"}]
for temp in [0.0, 1.5]:
    print(f"\n--- temperature = {temp} ---")
    for i in range(3):
        answer, _, _ = ask(NAME_PROMPT, temperature=temp, max_tokens=30)
        print(f"  第 {i + 1} 次：{answer}")




line("实验 4 · max_tokens 是「腰斩」开关")
for mt in [10, 300]:
    answer, finish, usage = ask(
        [{"role": "user", "content": "用三句话介绍杭州。"}],
        max_tokens=mt,
    )
    print(f"\n--- max_tokens = {mt} ---")
    print(answer)
    print(f"[finish_reason = {finish}]  [completion_tokens = {usage.completion_tokens}]")
    print(f"[usage 明细] {usage}")

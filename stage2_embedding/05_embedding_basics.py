import math
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

MODEL = "text-embedding-v4"

def get_embedding(text):
    response=client.embeddings.create(
        model=MODEL,
        input=text,
    )
    return response.data[0].embedding

def cosine_similarity(a, b):
    #计算两个向量的数量积
    dot=0
    for i in range(len(a)):
        dot+=a[i]*b[i]
    #计算向量的模长
    norm_a=0
    for x in a:
        norm_a+=x*x
    norm_a=math.sqrt(norm_a)

    norm_b=0
    for y in b:
        norm_b+=y*y
    norm_b=math.sqrt(norm_b)

    return dot/(norm_a*norm_b)

vec=get_embedding("今天天气很好")
print("向量长度：",len(vec))
print("前5个数字：",vec[:5])
print()

pairs=[
    ("苹果手机很好用", "iPhone 用起来很顺手"),
    ("苹果手机很好用", "我今天吃了一个苹果"),
    ("苹果手机很好用", "今天股市大跌"),
]

for a,b in pairs:
    va=get_embedding(a)
    vb=get_embedding(b)
    score=cosine_similarity(va,vb)
    print(f"{score:.4f} | {a} <-> {b}")
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

DOCUMENTS = [
    "《三体》是刘慈欣创作的科幻小说，讲述地球文明与三体文明的接触与对抗。",
    "《活着》是余华的代表作，讲述农民福贵一生的苦难与坚韧。",
    "《人类简史》梳理了人类从认知革命到科学革命的发展脉络。",
    "《百年孤独》是马尔克斯的魔幻现实主义经典，讲述布恩迪亚家族七代人的故事。",
    "《明朝那些事儿》用通俗语言讲述明朝三百年的历史。",
    "《小王子》是一本写给大人的童话，探讨爱与责任。",
    "《沉默的大多数》是王小波的杂文集，讨论自由与思考。",
    "《球状闪电》是刘慈欣的科幻作品，围绕球状闪电这一自然现象展开。",
    "《许三观卖血记》讲述普通人许三观靠卖血度过人生难关的故事。",
    "《万历十五年》从一年切入，剖析明代政治与社会结构。",
]

QUERIES = [
    "有哪些讲普通人苦难经历的小说？",
    "推荐几本科幻小说",
    "讲中国历史的书",
]

def get_embedding(texts):
    response=client.embeddings.create(
        model=MODEL,
        input=texts,
    )
    vectors=[]
    for item in response.data:
        vectors.append(item.embedding)
    return vectors

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

print("正在把10段文档变成向量（离线，只做一次）。。。")
doc_vector=get_embedding(DOCUMENTS)
print(f"完成：{len(doc_vector)}个向量，每个{len(doc_vector[0])}维\n")

for query in QUERIES:
    query_vector=get_embedding([query])[0]

    scores=[]
    for i in range(len(doc_vector)):
        score=cosine_similarity(doc_vector[i], query_vector)
        scores.append((score,DOCUMENTS[i]))

    #从按余弦值从大到小排序
    scores.sort(reverse=True)

    print("=" * 62)
    print(f"查询：{query}")
    print("=" * 62)

    for rank in range(3):
        score,doc=scores[rank]
        print(f"{rank+1}. [{score:.4f}] {doc}")
    print()

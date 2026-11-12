import math
import os
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

load_dotenv()

client = OpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

MODEL = "text-embedding-v4"
BASE_DIRE=Path(__file__).resolve().parent
DOC_PATH =BASE_DIRE / "docs" /"借阅规则.md"


def spit_text(text,chunk_size,overlap):
    if overlap>=chunk_size:
        raise ValueError("overlap 必须小于chunk_size，否则会死循环")

    chunks=[]
    start=0
    while start< len(text):
        end=start+chunk_size
        chunks.append(text[start:end])
        start=end - overlap
    return chunks

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

with open(DOC_PATH,encoding="utf-8") as f:
    text=f.read()

print(f"文档总长度：{len(text)}")

QUERY="逾期了要交多少钱？"

for size,overlap in [(150,30),(500,100)]:
    chunks=spit_text(text,size,overlap)
    print("="*62)
    print(f"chunk_size={size} overlap={overlap} ->切成{len(chunks)}块")
    print("="*62)

     #向量库
    vectors=get_embedding(chunks)
    #问题向量
    query_vector=get_embedding(QUERY)[0]

    scores=[]

    for i in range(len(vectors)):
        scores.append((cosine_similarity(query_vector,vectors[i]),chunks[i]))

    scores.sort(reverse=True)

    top_scores,top_chunks=scores[0]

    print(f"查询：{QUERY}")
    print(f"最相关的一块({len(top_chunks)})字，分数{top_scores}")
    print(top_chunks)
    print()




import math
import os

from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

load_dotenv()

embed_client = OpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

chat_client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url=os.environ["DEEPSEEK_BASE_URL"],
)

CHAT_MODEL = os.environ["DEEPSEEK_MODEL"]
EMBED_MODEL = "text-embedding-v4"

BASE_DIRE=Path(__file__).resolve().parent

DOCS_DIR =BASE_DIRE / "docs"


def split_text(text,chunk_size,overlap):
    if overlap>=chunk_size:
        raise ValueError("overlap 必须小于chunk_size，否则会死循环")

    chunks=[]
    start=0
    while start< len(text):
        end=start+chunk_size
        chunks.append(text[start:end])
        start=end - overlap
    return chunks


def split_by_heading(text):
    parts=text.split("\n## ")
    chunks=[]
    for i in range(1,len(parts)):
        chunks.append("## "+parts[i].strip())
    return chunks

def read_file(path):
    if path.suffix==".pdf":
        from pypdf import PdfReader
        reader=PdfReader(path)
        pages=[]
        for page in reader.pages:
            pages.append(page.extract_text())
        return "\n\n".join(pages)

    with open(path,"r",encoding="utf-8") as f:
        return f.read()



def get_embedding(texts,batch_size=10):
    vectors=[]
    for i in range(0,len(texts),batch_size):
        batch=texts[i:i+batch_size]
        response=embed_client.embeddings.create(
            model=EMBED_MODEL,
            input=batch,
        )
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


SYSTEM_PROMPT = """你是一个文档问答助手。

规则：
1. 只根据【参考资料】里的内容回答，不要使用你自己的知识
2. 如果参考资料里没有答案，直接回答「文档中没有提到」，不要编造
3. 回答末尾必须标注出处，格式：出处：块 #N
4. 回答要简洁，不要复述整段资料
"""

def retrieve(query,chunks,chunk_vectors,top_k=3):
    #获取问题向量

    query_vectors=get_embedding([query])[0]

    scores=[]
    for i in range(len(chunk_vectors)):
        score=cosine_similarity(query_vectors,chunk_vectors[i])
        scores.append((score,i))
    #排序，取前三
    scores.sort(reverse=True)

    top=[]
    for rank in range(top_k):
        #取第rank+个
        score,index=scores[rank]
        top.append((score,index))
    return top

def build_user_message(query,retrieved,chunks):
    parts=[]
    for score,index in retrieved:
        item=chunks[index]
        parts.append(f"【《{item['source']}》块 #{index}】{item['text']}")

    context="\n\n".join(parts)
    return f"""【参考资料】
{context}


【问题】
{query}"""

def answer(query,chunks,chunk_vectors):
    retrieved=retrieve(query,chunks,chunk_vectors,top_k=3)

    user_message=build_user_message(query,retrieved,chunks)

    response=chat_client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0,
        max_tokens=500,
        messages=[
        {"role":"system","content":SYSTEM_PROMPT},
        {"role":"user","content":user_message}
        ]
    )
    return response.choices[0].message.content


def load_chunks(mode="heading"):
    chunks=[]

    files=sorted(DOCS_DIR.glob("*.md"))+sorted(DOCS_DIR.glob("*.pdf"))

    for path in files:
        text=read_file(path)
        if mode=="heading":
            pieces=split_by_heading(text)
        else:
            pieces=split_text(text,150,30)
        for piece in pieces:
            chunks.append({"source":path.name,"text":piece})

    text=[]
    for c in chunks:
        text.append(c["text"])
    vectors=get_embedding(text)
    return chunks,vectors







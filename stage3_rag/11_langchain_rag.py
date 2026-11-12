import os
from pathlib import Path
import chromadb
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
DB_PATH = BASE_DIR / "chroma_lc_db"


#1)对话模型
llm=ChatOpenAI(
    model=os.environ["DEEPSEEK_MODEL"],
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url=os.environ["DEEPSEEK_BASE_URL"],
    temperature=0
)

#2)向量模型
embeddings =OpenAIEmbeddings(
    model="text-embedding-v4",
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    check_embedding_ctx_length=False,
    chunk_size=10
)

#3)切分器
spliter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#","h1"),("##","h2")],
    strip_headers=False,
)

#4)建立文档列表
documents=[]
for path in sorted(DOCS_DIR.glob("*.md")):
    text=path.read_text(encoding="utf-8")
    for i,piece in enumerate(spliter.split_text(text)):
        piece.metadata["source"]=path.name
        piece.metadata["block"]=i
        documents.append(piece)

print(f"切出{len(documents)}块")
for i ,d in enumerate(documents):
    head = d.page_content.strip().splitlines()[0]
    print(i, d.metadata["source"], head[:24])

#5建库

client=chromadb.PersistentClient(path=str(DB_PATH))

col=client.get_or_create_collection("docs_lc")

print(f"库里现有条数{col.count()}")

vectorstore=Chroma(
    client=client,
    collection_name="docs_lc",
    embedding_function=embeddings,
)

if col.count() == 0:
    batch_size = 10
    for i in range(0,len(documents),batch_size):
        batch=documents[i:i+batch_size]
        vectorstore.add_documents(batch)
    print(f"冷启动：写入 {len(documents)} 条")
else:
    print("库已有数据，跳过写入")


#6)检索器
retriever=vectorstore.as_retriever(search_kwargs={"k":3})


# 7) 提示词模板
prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个文档问答助手。

规则：
1. 只根据【参考资料】里的内容回答，不要使用你自己的知识
2. 如果参考资料里没有答案，直接回答「文档中没有提到」，不要编造
3. 有依据时才标出处，且出处必须带文件名，格式 出处：《文件名》块 #N
4. 回答要简洁，不要复述整段资料
5. 如果是拒答（文档中没有提到），不要标出处"""),

("human", """【参考资料】
{context}

【问题】
{question}"""),
])

def format_docs(docs):
    parts=[]
    for d in docs:
        m=d.metadata
        parts.append(f"【《{m['source']}》块 #{m['block']}】{d.page_content}")
    return "\n\n".join(parts)

#8)串成链
chain=(
    {"context":retriever | format_docs,"question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

QUESTIONS = [
    "逾期了要交多少钱？",
    "研究生能借几本书？",
    "可以续借几次？",
    "图书馆的开放时间是什么？",
]

for q in QUESTIONS:
    print("="*62)
    print(f"问题：{q}")
    print("="*62)
    print(chain.invoke(q))
    print()
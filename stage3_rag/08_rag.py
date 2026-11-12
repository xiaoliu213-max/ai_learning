from rag_core import answer,load_chunks





QUESTIONS=[
    "逾期了要交多少钱？",
    "研究生能借几本书？",
    "可以续借几次？",
    "图书馆的开放时间是什么？",
]

chunks,chunk_vectors=load_chunks(chunk_size=150, overlap=30)
print(f"把文档切成{len(chunks)}块\n")

for q in QUESTIONS:
    print("="*62)
    print(f"问题：{q}")
    print("="*62)
    print(answer(q,chunks,chunk_vectors))
    print()

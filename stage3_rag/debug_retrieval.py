from rag_core import load_chunks,retrieve

chunks,chunk_vector=load_chunks(150,30,"heading")

q="书到期了还能再多留几天吗？"

top= retrieve(q,chunks,chunk_vector,top_k=6)

for score,index in top:
    print(f"----块{index} 分数:{score:.4f}-----")
    print(chunks[index])
    print()

from pathlib import Path
import chromadb

from rag_core import get_embedding,load_chunks,retrieve

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "chroma_db"

QUERY = "书到期了还能再多留几天吗？"

chunks, vectors = load_chunks(mode="heading")
print(f"共 {len(chunks)} 块\n")

client=chromadb.PersistentClient(path=str(DB_PATH))
collection=client.get_or_create_collection(
    name="docs",
    metadata={"hnsw:space":"cosine"}
)
if collection.count()==0:
    ids=[]
    documents=[]
    metadatas=[]
    for i in range(len(chunks)):
        ids.append(f"block-{i}")
        documents.append(chunks[i]["text"])
        metadatas.append({"source":chunks[i]["source"],"block":i})

    collection.add(ids=ids,documents=documents,embeddings=vectors,metadatas=metadatas)
    print("索引已经建立并写入磁盘\n")
else:
    print(f"索引已存在（{collection.count()}条），跳过写入\n")

query_vector=get_embedding([QUERY])[0]

print("=" * 62)
print("【Chroma 检索】")
print("=" * 62)

results=collection.query(query_embeddings=[query_vector],n_results=3)

for i in range(len(results["ids"][0])):
    doc_id=results["ids"][0][i]
    distance = results["distances"][0][i]
    meta = results["metadatas"][0][i]
    text = results["documents"][0][i]
    print(f"{i + 1}. {doc_id}  《{meta['source']}》")
    print(f"   距离 {distance:.4f}  ->  相似度 {1 - distance:.4f}")
    print(f"   {text[:36]}...")
    print()


print("=" * 62)
print("【手写版检索（对照）】")
print("=" * 62)
manual = retrieve(QUERY, chunks,vectors, top_k=3)
for i in range(len(manual)):
    score, index = manual[i]
    print(f"{i + 1}. 块 #{index}  《{chunks[index]['source']}》  相似度 {score:.4f}")


print()
print("=" * 62)
print("【元数据过滤：只在《自习室规定》里找】")
print("=" * 62)
filtered = collection.query(
    query_embeddings=[query_vector],
    n_results=2,
    where={"source": "自习室规定.md"},
)


for i in range(len(filtered["ids"][0])):
    meta = filtered["metadatas"][0][i]
    text = filtered["documents"][0][i]
    print(f"{i + 1}. 《{meta['source']}》块 #{meta['block']}  {text[:36]}...")

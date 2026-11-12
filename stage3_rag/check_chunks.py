from rag_core import load_chunks

chunks, _ = load_chunks(mode="heading")
print(f"共 {len(chunks)} 块\n")

for i in range(len(chunks)):
    print(f"#{i}  《{chunks[i]['source']}》  {chunks[i]['text'][:24]}")

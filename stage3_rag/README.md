# 校园文档问答机器人（RAG）

基于校内规则文档的问答系统：回答只依据 `docs/` 里的材料，**必须标出处**，材料里没有就明确拒答。

同一套行为写了两个版本，用来回答一个问题：**框架到底帮我做了什么、代价是什么。**

| 版本 | 文件 | 行数 |
|---|---|---|
| 手写版 | `rag_core.py` | 176 |
| LangChain 版 | `11_langchain_rag.py` | 109 |

---

## 功能

- 支持 `.md` / `.pdf`（PDF 用 `pypdf`；扫描件需 OCR，未处理）
- **按标题切分**（不是按字数硬切）
- 批量向量化（百炼 `text-embedding-v4`，1024 维，每批 10 条）
- 两种检索：手写余弦全遍历 / Chroma（HNSW，cosine）
- 回答带出处：`出处：《文件名》块 #N`
- 防幻觉：资料里没有就答「文档中没有提到」，且**不标出处**
- 11 题评测集，三维度打分

## 评测结果

| 维度 | 结果 |
|---|---|
| 内容正确 | 11/11 |
| 出处正确 | 11/11 |
| 拒答正确 | 11/11 |

评测集在 `09_eval.py`。**注意**：`expected_block` 与切分方式强绑定，改了切分/块号必须同步改评测集。

## 架构

```
离线（跑一次）
docs/*.md ──read_file──▶ 全文 ──split_by_heading──▶ chunks（11 块）
         ──get_embedding──▶ vectors ──▶ 内存平行列表 / Chroma 落盘

在线（每次提问）
问题 ──向量化──▶ 与 11 个块算余弦 ──▶ 排序取 top-3
     ──拼进提示词──▶ DeepSeek ──▶ 回答 + 出处
```

## 技术栈

- 对话：DeepSeek（OpenAI 兼容接口）
- 向量：阿里百炼 `text-embedding-v4`（1024 维）
- 向量库：Chroma 1.5.9（`hnsw:space = cosine`）
- 框架对照：LangChain（`langchain-openai` / `langchain-chroma` / `langchain-text-splitters`）

## 文件说明

| 文件 | 作用 |
|---|---|
| `rag_core.py` | 核心模块：切分、读文件、向量化、余弦、检索、拼提示词、调模型 |
| `09_eval.py` | 11 题评测集（内容/出处/拒答） |
| `10_chroma.py` | Chroma 版检索 + 与手写版对答案 + 元数据过滤 |
| `11_langchain_rag.py` | LangChain 版（Document / splitter / embeddings / retriever / LCEL） |
| `07_chunking.py` | 切分实验（固定长度 vs 按标题） |
| `check_chunks.py` | 打印「块号 → 来源 → 前 24 字」 |
| `08_rag.py` / `debug_retrieval.py` | 早期脚本，`load_chunks` 签名改过后已过期，仅作历史参考 |

## 怎么跑

```bash
# 1. 依赖（项目根目录的 .venv）
./.venv/Scripts/python.exe -m pip install -r requirements.txt

# 2. 在项目根目录准备 .env（不入库）
#    DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL / DEEPSEEK_MODEL / DASHSCOPE_API_KEY

# 3. 评测（手写版）
./.venv/Scripts/python.exe stage3_rag/09_eval.py

# 4. Chroma 版（首次会建库）
./.venv/Scripts/python.exe stage3_rag/10_chroma.py

# 5. LangChain 版
./.venv/Scripts/python.exe stage3_rag/11_langchain_rag.py
```

> **改文档或切分方式后必须删库重建**：`stage3_rag/chroma_db/`、`stage3_rag/chroma_lc_db/`。
> 索引不会自动更新——`count() == 0` 的守卫只防重复写入，不防“内容过期”。

## 关键设计与踩坑

1. **按标题切优于固定长度**：固定切分会把两个主题切进同一块，向量被「语义稀释」，该块排不上去；按标题切还省掉 overlap 的重复字数。
2. **块号是设计决定**：手写版全局编号 0–10（唯一）；框架版每个文件从 0 重数（两个「块 #3」）。最终用「出处带文件名」解决。
3. **拒答也要写进规则**：早期提示词写的是「回答末尾必须标出处」，导致拒答时出现 `文档中没有提到。出处：块 #0、块 #4`——自相矛盾。规则必须写明「什么时候不适用」。
4. **“11 块 = 11 块”是巧合**：框架切分器把文档大标题并进第一节，块数相同但边界不同；旧评测集直接复用它一定会大面积 FAIL。
5. **id 策略决定重跑行为**：手写版用 `block-0…`（确定性，重跑撞主键）；LangChain 默认 `uuid4()`（随机，重跑全量追加）。要幂等应显式传 `ids`。
6. **满分是危险信号**：评测集全过说明题太简单，没有区分度；好评测集应能考出 70–85 分。

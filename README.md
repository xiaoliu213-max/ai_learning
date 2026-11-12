# ai-learning

AI 应用开发学习项目：从「调通大模型」到「把 Agent 挂成 API 并容器化」。

## 两个可展示的项目

| 项目 | 目录 | 一句话 |
|---|---|---|
| 校园文档问答机器人（RAG） | [`stage3_rag/`](stage3_rag/README.md) | 基于校内规则文档的问答，必须标出处，没有就拒答；手写版与 LangChain 版对照 |
| 图书管理员 Agent | [`stage5_agent/`](stage5_agent/README.md) | 模型自主调用工具查馆藏/借阅；FastAPI + SSE 流式 + Docker |

## 学习阶段与产出

| 阶段 | 内容 | 产出 |
|---|---|---|
| ① 大模型 API + 提示词 | 角色、参数、few-shot、结构化输出 | 翻译器、JSON 抽取（10/10） |
| ② Embedding 与检索 | 文字向量化、手写余弦 | 语义搜索脚本 |
| ③ RAG ★ | 切分、向量化、检索、评测闭环 | 文档问答机器人（11/11 × 3 维度） |
| ④ LangChain | 同一系统重写、读源码、做选型 | 176 → 109 行；300 字选型结论 |
| ⑤ Agent + 部署 | Function Calling、Agent 循环、SSE、Docker | 四版 Agent（220 → 121 → 93 行）、API、容器 |

详见 [`AI_LEARNING_PLAN.md`](AI_LEARNING_PLAN.md)。

## 环境

- Python 3.12，虚拟环境固定在项目根 `.venv`
- 依赖：`requirements.txt`（112 个包，版本钉死）
- 密钥只放 `.env`（不入库）：

```
DEEPSEEK_API_KEY=       # 对话模型
DEEPSEEK_BASE_URL=      # OpenAI 兼容地址
DEEPSEEK_MODEL=
DASHSCOPE_API_KEY=      # 向量模型（百炼 text-embedding-v4）
```

## 快速开始

```bash
./.venv/Scripts/python.exe -m pip install -r requirements.txt

# 项目一：评测
./.venv/Scripts/python.exe stage3_rag/09_eval.py

# 项目二：API
./.venv/Scripts/python.exe -m uvicorn api:app --app-dir stage5_agent --port 8010
# http://127.0.0.1:8010/docs

# 项目二：容器
docker compose up --build
```

## 目录

```
stage1_llm/       ① 调模型与提示词
stage2_embedding/ ② 向量与相似度
stage3_rag/       ③④ RAG（手写 + Chroma + LangChain）
stage5_agent/     ⑤ Agent 四版 + API
Dockerfile / compose.yaml / requirements.txt   ⑤ 部署
.workbuddy-ai/    逐日学习日志
```

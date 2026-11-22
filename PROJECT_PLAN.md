# 校园图书助手 · 完整项目计划

> 目标：把现有两个 demo（RAG 问答 + 图书 Agent）合成**一个完整项目**：
> 有登录、有真实数据库、有会话持久化、有前端、有测试、能容器化部署。
>
> 节奏：每天 2 小时，14 天。**卡住才看课，不先刷课。**

---

## 0. 完成后的样子（验收总标准）

- 打开网页 → 登录 → 聊天 → 回答带出处、能查真实借阅、能问规则
- 换一个账号 → 看不到别人的借阅（403）
- 重启服务 → 历史会话还在
- `docker compose up` 一条命令起（app + MySQL）
- `pytest` 全绿

---

## 1. 技术决定（先定死，避免中途摇摆）

| 决定 | 选择 | 理由 |
|---|---|---|
| 会话存储 | **MySQL**（不引 Redis） | 少一个组件；你已经会 SQLAlchemy |
| Agent | 先用 `create_agent`（已会） | 先跑通产品，LangGraph 版作为进阶分支 |
| RAG | 包成一个工具 `search_docs` | 项目一变成项目二的一个能力 |
| 前端 | 单文件 `index.html` + `fetch` 读 SSE | 不学框架，能演示即可 |
| 鉴权 | JWT（HS256），token 里只放 `user_id` | 不让客户端自报学号 |
| 部署 | Docker Compose（app + mysql） | 与你现有 Docker 知识一致 |

---

## 2. 数据模型（5 张表）

```sql
users      (id, student_id UNIQUE, name, password_hash, created_at)
books      (id, title UNIQUE, author, total_copies, floor, created_at)
loans      (id, user_id→users, book_id→books, borrowed_at, due_at, returned_at NULL)
sessions   (id, user_id→users, title, created_at, updated_at)
messages   (id, session_id→sessions, role, content, created_at)
```

**关键设计**：`books` 里**不要**存 `available_copies`。
可借数量 = `total_copies - 未归还的 loans 数`。存两份就会出现“两处真相不一致”的经典 bug。

索引：`loans(user_id)`、`loans(due_at)`、`sessions(user_id)`、`messages(session_id)`。

可选（做增量索引时再加）：`doc_index(id, filename, md5, updated_at)`。

---

## 3. 目录结构

```
ai-learning/                 ← 现有仓库，新建分支 feat/full-product
  app/
    main.py                  FastAPI 入口
    config.py                .env 读取（DATABASE_URL / JWT_SECRET）
    db.py                    engine / SessionLocal / Base
    models.py                5 张表
    schemas.py               Pydantic 请求/响应
    auth.py                  密码哈希 + JWT 签发/校验
    deps.py                  get_db / get_current_user
    routers/
      auth.py                POST /auth/login  GET /auth/me
      chat.py                POST /chat  POST /chat/stream
    agent/
      tools.py               get_book_status / get_my_loans / search_docs
      core.py                create_agent 装配
    rag/
      search.py              复用 rag_core 的切分与检索
  alembic/                   迁移
  seed.py                    造数据（书、用户、借阅）
  tests/
  frontend/index.html
  compose.yaml               加 mysql 服务
```

---

## 4. 14 天计划

### 第 1 周：把“假”换成“真”

| 天 | 任务 | 当天完成标准 |
|---|---|---|
| D1 | 冻结需求；画 ER 图；建分支 `feat/full-product` | 5 张表的字段和关系定稿 |
| D2 | 装依赖（sqlalchemy / alembic / pymysql / pytest / pyjwt / pwdlib）；`db.py`、`models.py` | 能连上 MySQL，`alembic upgrade head` 建表成功 |
| D3 | `seed.py`：20 本书、2 个用户、每人 2~3 条借阅；`get_book_status` 改查库 | 工具返回真实数据（改一条 loans，回答跟着变） |
| D4 | `get_my_loans` 改查库（算 days_left / overdue / fine） | 滞纳金规则与文档一致：0.5/天，单本封顶 20 |
| D5 | `auth.py` + `deps.py`：登录发 JWT、`get_current_user` | `POST /auth/login` 拿 token；`GET /auth/me` 能验 |
| D6 | 接口鉴权：`/chat` 必须带 token；学号从 token 取 | 不带 token 401；A 用户查不到 B 的借阅 |
| D7 | 会话落库：`sessions` / `messages`；`/chat` 读写数据库 | **重启服务后继续聊，历史还在** |

### 第 2 周：把“能跑”变成“能演示”

| 天 | 任务 | 当天完成标准 |
|---|---|---|
| D8 | 流式改造：`/chat/stream` 流完再写 AI 消息；失败要回滚 | 流式中断不会留下半条脏数据 |
| D9 | RAG 变工具：`search_docs(query)`，复用 `rag_core` + Chroma | 问“逾期多少钱”能引用《借阅规则》 |
| D10 | 工具与 `create_agent` 整合；system prompt 加“只答本校数据” | 三个工具能按问题自动选对 |
| D11 | 前端：登录框 + 聊天框 + SSE 打字机 | 浏览器里能完整演示一遍 |
| D12 | pytest：工具单测、登录 401/200、越权 403、流式 200 | `pytest -q` 全绿 |
| D13 | compose 加 MySQL；启动时跑迁移；健康检查 | 新机器 `docker compose up` 一条命令可用 |
| D14 | README 更新（架构图/接口/演示 GIF）+ 简历条目（STAR） | 3 分钟能讲完整个项目 |

**进阶（可选，不占 14 天）**：把 `create_agent` 换成自建 `StateGraph`（课程第二门 70–86），加 `interrupt` 做“预约前人工确认”（34 集）。

---

## 5. 课程怎么配合（只在卡住时看）

| 卡点 | 看哪集 |
|---|---|
| LangGraph 概念/状态/边 | 第二门 70–86（连续看） |
| 人工审核 | 第二门 34 |
| 短期/长期记忆 | 第二门 21–23 |
| LangSmith 追踪 | 第二门 25 |
| 文件上传 + md5 增量索引 | 第一门 46–50 |
| 聊天页面 | 第一门 54 |

**不要为了“看完”而看**：主线是项目，课是参考书。

---

## 6. 六条原则（贴在显示器上）

1. **卡住才看课**，不要先刷 87 集。
2. **一次只加一个变量**：先真实数据，再登录，再持久化，最后前端。
3. **每天结束要 commit**，并留下“今天能演示什么”。
4. **不追求漂亮**，追求“能点开、能讲清”。
5. **每周自测一次**：不看代码，讲 3 分钟这个项目的架构与取舍。
6. **不过度设计**：不上 Milvus、不上 Redis、不上多 Agent，除非有真实需求。

---

## 7. 已知风险（提前想好）

| 风险 | 应对 |
|---|---|
| MySQL 连不上 | 复用你 FastAPI 项目的连接串；先 `mysql -u root -p` 手连一次 |
| Alembic 自动生成不识别类型 | 先手写第一个迁移，后面再用 autogenerate |
| JWT 与 session 混淆 | token 只放 `user_id`；会话 id 是业务数据，不是身份 |
| 流式 + 数据库事务 | 先写 user 消息并提交；流完再写 assistant 消息；异常则不写 |
| 前端 SSE 解析 | 按 `\n\n` 切事件，跳过 `[DONE]` |
| 范围膨胀 | 每个“想做的新功能”先写进 backlog，不插队 |

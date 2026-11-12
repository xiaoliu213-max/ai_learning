# 图书管理员 Agent

一个能「查馆藏、查借阅」的对话式 Agent：模型自己判断要不要调工具、调哪个、参数填什么；**真正执行的是程序**。

四个版本对照，用来观察框架逐层替代了什么：

| 版本 | 文件 | 总行数 | 框架相关代码 | 你能控制什么 |
|---|---|---|---|---|
| 手写 | `02_agent.py` | 220 | ≈107 | 全部：JSON schema、循环、回执、轮数上限 |
| LangChain 零件版 | `03_langchain_agent.py` | 121 | ≈40 | 循环自己写，schema/消息由框架给 |
| `create_agent` | `04_create_agent.py` | 93 | ≈13 | 只剩配置 |
| API 版 | `agent_core.py` + `api.py` | — | — | HTTP 层、流式、会话 |

> 三个版本约有 70 行是共有的假数据 + 两个工具函数；真正的差异是 **107 → 40 → 13 行**，省掉的是**可观测性**，不是工作量。

## 能力

- 两个工具：
  - `get_book_status(title)` → 是否可借 / 在馆数量 / 楼层
  - `get_my_loans(student_id)` → 在借图书、到期日、剩余天数、是否逾期、滞纳金（0.5 元/天，单本封顶 20）
- 多轮会话：能追问，记得上文
- 行为边界（system prompt）：只用提供的工具；没有对应工具就说「查不了」，**不承诺后续操作**；缺参数先问用户，不自己编
- 工具在本地算好结论（天数、金额）再交给模型——**模型负责说话，工具负责算数**

## 接口

### `POST /chat`

```bash
curl -X POST http://127.0.0.1:8010/chat \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"u1\",\"message\":\"学号 2023001，我借的书哪些逾期了？\"}"
```

```json
{"reply": "你有一本逾期：《活着》已逾期 9 天，应缴滞纳金 4.5 元……"}
```

### `POST /chat/stream`（SSE）

```bash
curl -N -X POST http://127.0.0.1:8010/chat/stream \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"u1\",\"message\":\"三体还能借吗\"}"
```

```
data: {"t": "《"}
data: {"t": "三"}
data: {"t": "体"}
...
data: [DONE]
```

- 每条事件以 `data: ` 开头、以**两个换行**结束
- `-N` 必须加，否则 curl 会缓冲、看不到流式

## 怎么跑

### CLI

```bash
./.venv/Scripts/python.exe stage5_agent/02_agent.py            # 手写版
./.venv/Scripts/python.exe stage5_agent/03_langchain_agent.py  # 零件版
./.venv/Scripts/python.exe stage5_agent/04_create_agent.py     # create_agent 版
```

输入问题回车；`退出` / `exit` 结束。

### API

```bash
./.venv/Scripts/python.exe -m uvicorn api:app --app-dir stage5_agent --port 8010 --reload
```

打开 http://127.0.0.1:8010/docs 。

> 端口用 8010（8000 在本机被占用）。

### Docker

```bash
docker compose up --build     # 首次构建会装 112 个包，几分钟
docker compose logs -f        # 看日志
docker compose down           # 停止并删除容器
```

访问 http://127.0.0.1:8010/docs 。

## 设计要点

1. **模型只“提议”**：它返回 `tool_calls`（要调哪个函数、参数是什么），执行、校验、错误处理全在程序里——安全边界因此可控。
2. **docstring 就是工具说明书**：`@tool` 从函数名、docstring、类型注解生成 schema。写含糊，模型就选错工具或填错参数。
3. **会话 = 一个 id 一个消息列表**：`SESSIONS[session_id]`；`messages` 只能追加，不能重建（重建会丢 system prompt 和历史）。
4. **上限是保护，不是流程**：手写版 `range(1,4)`；`create_agent` 版 `recursion_limit`。
5. **`0.0.0.0` 是监听地址，不是访问地址**：容器里 `--host 0.0.0.0`（所有网卡 listen）+ compose `ports: 8010:8010`（宿主机侧绑定）两道门都满足，局域网设备才能访问；浏览器要访问 `127.0.0.1` / `localhost`。

## 已知限制

- **会话存在进程内存**：容器/进程重启即丢失；多实例不共享
- **无鉴权**：`session_id` 由客户端自报，可被冒充；生产应由登录态（JWT）生成
- **工具是假数据**：`BOOKS` / `LOANS` 是字典，未接真实数据库
- **未做公网部署**：只验证了本机容器访问；公网需服务器 + 安全组 + `.env` 上传

## 踩坑记录

| 现象 | 原因 | 解法 |
|---|---|---|
| `ChatOpenAI model: Input should be a valid string` | `load_dotenv` 只 import 没调用，`os.environ.get` 返回 None | 调用 `load_dotenv()`；用 `os.environ["X"]` 让错误当场爆 |
| `attempted relative import with no known parent package` | `--app-dir` 下 `api` 是顶层模块 | `from agent_core import agent`（去掉点） |
| 重跑库翻倍 | 框架默认 `uuid4()` 生成 id | 显式传确定性 `ids` |
| 滞纳金少 0.5 元 | `round(4.5)` = 4（银行家舍入） | `round(x, 2)` |
| 浏览器 `ERR_ADDRESS_INVALID` | 把 `0.0.0.0` 当访问地址 | 浏览器用 `127.0.0.1`；`0.0.0.0` 只写在配置里 |
| Docker API 连不上 | Docker Desktop 没启动 | `docker ps` 验证引擎，而不只是 `docker --version` |

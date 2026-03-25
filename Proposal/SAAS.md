一个 SaaS 化路径分析。

---

## SaaS 化核心挑战

### 1. 当前架构的问题
现有项目是**单用户、单机运行**的：
- LLM API Key 存在 .env 文件里（单租户）
- 任务是**阻塞同步**执行的（`graph.stream()`）
- 无用户身份、无数据隔离、无计费

---

## SaaS 架构设计

### 租户模型选择

| 模型 | 描述 | 适合场景 |
|---|---|---|
| **BYOK（自带 Key）** | 用户填写自己的 LLM API Key | 中小型 SaaS，成本低 |
| **Platform Key** | 平台统一调用，按用量计费 | 高端 SaaS，需要精确计费 |
| **混合** | 默认 BYOK，付费套餐用平台 Key | 推荐 |

---

### 技术架构全景

```
Browser (WebUI)
    │
    ▼
[API Gateway / Nginx]
    │
    ├── Auth Service (JWT)          ← 用户注册/登录
    ├── FastAPI Backend             ← 现有 webui/backend，扩展
    │       ├── /api/auth           ← 认证
    │       ├── /api/users          ← 用户管理
    │       ├── /api/apikeys        ← 用户的 LLM Key 管理
    │       ├── /api/analyze        ← 提交分析任务
    │       ├── /api/jobs           ← 任务历史查询
    │       └── /api/billing        ← 用量/订阅
    │
    ├── Task Queue (Celery + Redis) ← 替换现在的 threading
    │       └── Worker(s)           ← 可水平扩展
    │
    ├── PostgreSQL                  ← 用户/任务/报告持久化
    └── Object Storage (S3/MinIO)   ← 报告 .md 文件存储
```

---

### 需要新增的核心模块

#### ① 用户 & 认证
```python
# 新表：users, api_keys, sessions
# 推荐库：fastapi-users 或 authlib
# 关键：每个任务绑定 user_id，LLM Key 加密存储（AES-256）
```

#### ② API Key 安全存储
```python
# 用户的 OPENAI_API_KEY 等不能明文存 DB
# 推荐：HashiCorp Vault 或 AWS KMS
# 最简：Fernet 对称加密存 PostgreSQL，密钥在环境变量
from cryptography.fernet import Fernet
```

#### ③ 任务队列（关键改造）

当前 jobs.py 用 `threading` 直接运行，SaaS 场景需要：

```
用户请求 → FastAPI → 写入 DB（status=pending）→ 推入 Celery Queue
                                                        ↓
                                               Worker 消费任务
                                               运行 TradingAgentsGraph
                                               SSE 通过 Redis PubSub 推回
                                                        ↓
                                               DB 更新结果 + S3 存报告
```

#### ④ 计量计费
```python
# 每次分析记录：
# - tokens_in / tokens_out（从 StatsCallbackHandler 获取）
# - 使用的模型
# - 用时
# 对接 Stripe：订阅套餐 or 按次付费
```

#### ⑤ 多租户数据隔离
- DB 层：所有表加 `user_id` / `tenant_id` 外键
- 查询层：所有接口强制 `WHERE user_id = current_user.id`
- 文件层：S3 路径 `reports/{user_id}/{job_id}/`

---

### 数据库模型（核心表）

```
users           [id, email, hashed_password, tier, created_at]
user_api_keys   [id, user_id, provider, encrypted_key, created_at]
jobs            [id, user_id, ticker, date, status, config_json, created_at]
job_reports     [id, job_id, section, content_url, created_at]
usage_records   [id, user_id, job_id, tokens_in, tokens_out, model, cost]
subscriptions   [id, user_id, stripe_sub_id, tier, quota_per_month]
```

---

### 订阅套餐设计建议

| 套餐 | 价格 | 分析次数/月 | 功能 |
|---|---|---|---|
| Free | $0 | 5次 | BYOK，yfinance only |
| Pro | $29/月 | 50次 | BYOK，所有数据源 |
| Business | $99/月 | 200次 | BYOK + 优先队列，历史报告 90 天 |
| Enterprise | 定制 | 无限 | 私有部署选项 |

---

### 最小可行路径（MVP 顺序）

1. **Week 1-2**: 加 PostgreSQL + 用户注册/登录（JWT）+ LLM Key 加密存储
2. **Week 3**: 将 `threading` 替换为 Celery + Redis，SSE 改用 Redis PubSub
3. **Week 4**: 报告存 MinIO/S3，任务历史页面
4. **Week 5-6**: 对接 Stripe，加限流（`slowapi`），加用量统计
5. **Week 7+**: 管理后台（用户管理、用量监控）

---

### 现有代码可以直接复用的部分

| 文件 | 复用方式 |
|---|---|
| jobs.py | 改造为 Celery task，保留核心 graph 调用逻辑 |
| providers.py | 直接复用 |
| main.py | 加认证中间件，扩展路由 |
| frontend | 加登录页/注册页/历史报告页/账户设置页 |
| stats_handler.py | 直接用于计量 token 用量 |

---

你想先从哪部分开始实现？建议从**用户认证 + LLM Key 管理**入手，因为这是所有其他功能的基础。
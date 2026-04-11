# 狸梦小说 Lymo Story — 多智能体 AI 中文长篇小说生成系统

人类提供题材/思路，7 个专用 AI Agent 通过 LangGraph 编排协作，自动完成世界构建、情节推进、章节撰写和标题命名。

> Brand: 狸梦小说 / Lymo Story｜作者：zhuiye（追夜）

## 系统架构

```
用户输入题材 → Director Agent → Story Bible（故事圣经）
                                      ↓
循环生成每章:  World → Planner → Camera → Writer → Consistency → Titler
              (推进世界)  (规划剧情)  (选视角)  (写正文)   (一致性校验)  (生成标题)
                                                           ↓
                                                    通过 → 保存章节 → 提取角色记忆
                                                    失败 → 重试(最多3次) / 警告保存
```

### Agent 职责

| Agent | 职责 | 输出 |
|-------|------|------|
| Director | 将用户题材转化为完整的故事圣经 | StoryBible JSON |
| World | 推进世界时间，生成事件（不写叙事） | 事件列表 + 世界状态更新 |
| Plot Planner | 将世界事件转化为章节剧情结构 | 剧情节拍（beats） |
| Camera | 决定 POV 视角、可见/隐藏事件、叙事节奏 | 摄影决策 |
| Writer | 根据剧情+视角+角色生成中文小说正文 | 2000-4000字章节 |
| Consistency | 检查人设/时间线/世界规则一致性 | 通过/失败 + 问题列表 |
| Titler | 基于章节正文生成简短文学标题 | 2-8字章节标题 |

## 技术栈

- **后端**: Python 3.11 / FastAPI / LangGraph / LiteLLM
- **管理端**: Next.js 16 (TypeScript) / Tailwind CSS 4 — 故事创建、生成控制、LLM 管理
- **阅读端**: Next.js 16 / Tailwind CSS 4 — 独立部署的读者前端，Web + 移动双端适配
- **存储**: SQLite + JSON 文件 + ChromaDB（向量检索）
- **模型**: 通过 LiteLLM 支持 100+ 模型（OpenAI / Claude / DeepSeek / Qwen / 本地模型等）
- **包管理**: 后端 pip（conda env "story"）/ 前端与阅读端 pnpm

## 环境要求

- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 或 Anaconda
- Node.js >= 18
- 一个LLM API Key（OpenAI / Claude / 其他LiteLLM支持的模型）

## 快速开始

### 1. 创建Python环境（Miniconda）

```bash
conda create -n story python=3.11 -y
conda activate story
```

### 2. 安装后端依赖

```bash
cd C:\Files\work\story
pip install -e ".[dev]"
```

### 3. 配置默认LLM（环境变量）

复制模板并编辑：

```bash
cp .env.example .env
```

`.env` 文件配置一个默认模型作为保底（未在管理中心绑定的Agent会使用此模型）：

```env
# DeepSeek（推荐，中文能力强，成本低）
STORY_LITELLM_MODEL=deepseek/deepseek-chat
STORY_LITELLM_API_KEY=sk-your-deepseek-key
STORY_LITELLM_API_BASE=https://api.deepseek.com

# 或 OpenAI
# STORY_LITELLM_MODEL=gpt-4o
# STORY_LITELLM_API_KEY=sk-your-key-here

# 或 Claude
# STORY_LITELLM_MODEL=claude-sonnet-4-20250514
# STORY_LITELLM_API_KEY=sk-ant-your-key-here

# 或 通义千问
# STORY_LITELLM_MODEL=qwen/qwen-max
# STORY_LITELLM_API_KEY=sk-your-dashscope-key

# 或 本地模型（Ollama）
# STORY_LITELLM_MODEL=ollama/qwen2.5:14b
# STORY_LITELLM_API_BASE=http://localhost:11434
```

> 注：这只是保底配置。启动后可在 http://localhost:3000/admin 管理中心配置多个模型，并为每个Agent绑定不同模型。

### 4. 启动后端

```bash
conda activate story
uvicorn backend.main:app --reload --port 8000
```

验证：访问 http://localhost:8000/api/health 应返回 `{"status":"ok"}`

### 5. 安装并启动管理端（创作者）

```bash
cd frontend
pnpm install
pnpm run dev   # http://localhost:3000
```

### 6. 安装并启动阅读端（读者）

```bash
cd reader
pnpm install
pnpm run dev   # http://localhost:4000
```

阅读端（狸梦小说）是独立的 Next.js 应用，消费后端 `/api/public/books/*` 接口展示已发布的小说，支持：
- 书架 / 发现 / 我的 三 Tab 导航（移动端底部 / 桌面端顶部）
- Eastern Noir 水墨风格的深色/亮色双模式
- 沉浸式阅读页 + 字号/主题/翻页模式设置
- 默认亮色模式，用户可手动切换

## 使用流程

1. 管理端首页输入故事题材（如"一个失忆的剑客在末世废墟中寻找自己的过去"）
2. 系统自动生成故事圣经（世界观、角色、规则）
3. 点击"生成下一章"，观察 7 个 Agent 协作流程
4. 在管理端章节阅读器中查看生成的中文小说
5. 发布故事后，读者访问 http://localhost:4000 阅读

## LLM 管理中心

访问 http://localhost:3000/admin 进入管理中心：

### 模型配置
- 添加多个LLM模型（支持OpenAI / Claude / Qwen / 本地模型等）
- 配置API Key、API Base、默认温度、Token成本
- 每个模型可单独启用/禁用

### Agent-模型绑定
- 为每个Agent（导演/世界/规划/摄影/写作/一致性检查）绑定不同模型
- 未绑定的Agent使用环境变量中的默认模型
- 支持按Agent覆盖温度和max_tokens

### 用量监控
- 总调用次数、Token用量、成本估算
- 按Agent维度的用量柱状图
- 平均延迟统计

### 请求日志（/admin/logs）
- 每次LLM调用的完整记录
- 可查看完整的system_prompt、user_prompt、response
- 按Agent/故事过滤
- 显示Token数、耗时、成本、状态

## 项目结构

```
story/
├── backend/
│   ├── main.py                 # FastAPI 入口
│   ├── config.py                # Pydantic Settings（环境变量）
│   ├── deps.py                  # 依赖注入
│   ├── models/                  # Pydantic 数据模型
│   ├── agents/                  # 7 个 Agent（director / world / planner / camera / writer / consistency / titler）
│   ├── prompts/                 # 对应的中文提示词模板
│   ├── graph/                   # LangGraph 编排
│   │   ├── init_graph.py        # 故事初始化图
│   │   ├── chapter_graph.py     # 章节生成图（含重试循环）
│   │   └── nodes.py             # 节点函数
│   ├── memory/                  # 记忆系统
│   │   ├── layered_memory.py    # 4 层记忆架构
│   │   ├── chapter_extractor.py # 章节后记忆提取
│   │   └── knowledge_graph.py   # 时间性知识三元组
│   ├── storage/
│   │   ├── sqlite_store.py      # SQLite 主库
│   │   ├── json_store.py        # JSON 文件（圣经/事件图）
│   │   └── vector_store.py      # ChromaDB（角色记忆向量）
│   ├── llm/
│   │   ├── client.py            # LiteLLM 统一网关
│   │   ├── model_registry.py    # 模型注册表
│   │   └── logger.py            # 调用日志记录器
│   └── api/
│       ├── stories.py           # 故事 CRUD + 生成触发
│       ├── chapters.py          # 章节读取
│       ├── control.py           # 生成状态控制
│       ├── llm_admin.py         # LLM 管理中心 API
│       └── public.py            # 阅读端公开接口（/api/public/books/*）
├── frontend/                    # 管理端 Next.js 16
│   ├── app/                     # 故事仪表盘 + LLM 管理 + 请求日志
│   ├── components/
│   ├── lib/
│   └── types/
├── reader/                      # 阅读端 Next.js 16（独立部署）
│   ├── app/
│   │   ├── (tabs)/              # 共享底部/顶部导航的 Tab 路由组
│   │   │   ├── page.tsx         # 书架
│   │   │   ├── discover/        # 发现
│   │   │   └── profile/         # 我的
│   │   └── book/[id]/           # 详情 + 阅读页
│   ├── components/              # BottomNav / TopBar / EmptyState / ReadingSettings 等
│   └── public/mascot/           # Lymo 狸猫吉祥物贴纸（点赞/庆祝/伤心/爱心）
├── data/                        # 运行时数据（gitignored）
├── pyproject.toml
├── .env.example
└── CLAUDE.md                    # Claude Code 项目指引
```

## API 端点

### 管理端
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/health | 健康检查 |
| POST | /api/stories | 创建故事 |
| GET | /api/stories | 列出所有故事 |
| GET | /api/stories/{id} | 获取故事详情 |
| GET | /api/stories/{id}/bible | 获取故事圣经 |
| POST | /api/stories/{id}/generate | 生成下一章 |
| GET | /api/stories/{id}/chapters | 列出章节 |
| GET | /api/stories/{id}/chapters/{num} | 读取章节 |
| GET | /api/stories/{id}/control/status | 生成状态 |
| GET | /api/stories/{id}/control/progress | 阶段级进度 |
| GET | /api/admin/models | 列出模型配置 |
| POST | /api/admin/models | 创建模型配置 |
| PUT | /api/admin/models/{id} | 更新模型配置 |
| DELETE | /api/admin/models/{id} | 删除模型配置 |
| GET | /api/admin/bindings | 获取 Agent-模型绑定 |
| PUT | /api/admin/bindings/{agent} | 设置 Agent 绑定 |
| GET | /api/admin/logs | 查询调用日志 |
| GET | /api/admin/logs/{id} | 日志详情（含完整 prompt） |
| GET | /api/admin/usage | 用量统计 |

### 阅读端（公开）
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/public/books | 列出已发布小说 |
| GET | /api/public/books/{id} | 获取小说详情 |
| GET | /api/public/books/{id}/chapters/{num} | 读取已发布章节 |

## 开发路线

- [x] **P0 核心 MVP** — 6 个 Agent 线性章节生成
- [x] **LLM 管理中心** — 模型配置、Agent 绑定、用量监控、请求日志
- [x] **记忆系统** — 4 层分层记忆 + 章节后记忆提取 + 时间性知识图谱
- [x] **章节命名** — Titler Agent 为每章生成简短文学标题
- [x] **阅读端** — 独立 reader 应用，Web + 移动双端适配，Eastern Noir 水墨风格
- [x] **发布系统** — 管理端发布小说，阅读端消费公开接口
- [ ] **P2 世界引擎** — 事件 DAG + 并行叙事线 + Camera 升级
- [ ] **P3 微调闭环** — 角色数据提取 + LoRA 训练 + 热切换
- [ ] **P4 人机协同** — 导演界面 + 实时干预 + 版本管理

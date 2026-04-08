# Story Engine — 多智能体AI中文长篇小说生成系统

人类提供题材/思路，6个专用AI Agent通过LangGraph编排协作，自动完成世界构建、情节推进、章节撰写。

## 系统架构

```
用户输入题材 → Director Agent → Story Bible（故事圣经）
                                      ↓
循环生成每章:  World → Planner → Camera → Writer → Consistency
              (推进世界)  (规划剧情)  (选视角)  (写正文)   (一致性校验)
                                                           ↓
                                                    通过 → 保存章节
                                                    失败 → 重试(最多3次)
```

### Agent 职责

| Agent | 职责 | 输出 |
|-------|------|------|
| Director | 将用户题材转化为完整的故事圣经 | StoryBible JSON |
| World | 推进世界时间，生成事件（不写叙事） | 事件列表 + 世界状态更新 |
| Plot Planner | 将世界事件转化为章节剧情结构 | 剧情节拍（beats） |
| Camera | 决定POV视角、可见/隐藏事件、叙事节奏 | 摄影决策 |
| Writer | 根据剧情+视角+角色生成中文小说正文 | 2000-4000字章节 |
| Consistency | 检查人设/时间线/世界规则一致性 | 通过/失败 + 问题列表 |

## 技术栈

- **后端**: Python 3.11 / FastAPI / LangGraph / LiteLLM
- **前端**: Next.js (TypeScript) / Tailwind CSS
- **存储**: SQLite + JSON文件 + ChromaDB（向量检索）
- **模型**: 通过LiteLLM支持100+模型（OpenAI / Claude / Qwen / 本地模型等）

## 环境要求

- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 或 Anaconda
- Node.js >= 18
- 一个LLM API Key（OpenAI / Claude / 其他LiteLLM支持的模型）

## 快速开始

### 1. 创建Python环境

```bash
conda create -n story python=3.11 -y
conda activate story
```

### 2. 安装后端依赖

```bash
cd C:\Files\work\story
pip install -e ".[dev]"
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的API Key：

```env
# 使用OpenAI
STORY_LITELLM_MODEL=gpt-4o
STORY_LITELLM_API_KEY=sk-your-key-here

# 或使用Claude
# STORY_LITELLM_MODEL=claude-sonnet-4-20250514
# STORY_LITELLM_API_KEY=sk-ant-your-key-here

# 或使用通义千问
# STORY_LITELLM_MODEL=qwen/qwen-max
# STORY_LITELLM_API_KEY=sk-your-dashscope-key

# 或使用本地模型（如Ollama）
# STORY_LITELLM_MODEL=ollama/qwen2.5:14b
# STORY_LITELLM_API_BASE=http://localhost:11434
```

### 4. 启动后端

```bash
conda activate story
uvicorn backend.main:app --reload --port 8000
```

验证：访问 http://localhost:8000/api/health 应返回 `{"status":"ok"}`

### 5. 安装并启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:3000

## 使用流程

1. 在首页输入故事题材（如"一个失忆的剑客在末世废墟中寻找自己的过去"）
2. 系统自动生成故事圣经（世界观、角色、规则）
3. 点击"生成下一章"，观察6个Agent协作流程
4. 在章节阅读器中查看生成的中文小说

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
│   ├── main.py              # FastAPI入口
│   ├── config.py             # 配置（环境变量）
│   ├── models/               # Pydantic数据模型（7个）
│   ├── agents/               # 6个Agent实现
│   ├── prompts/              # 6套中文提示词模板
│   ├── graph/                # LangGraph编排（核心）
│   │   ├── init_graph.py     # 故事初始化图
│   │   ├── chapter_graph.py  # 章节生成图（含重试循环）
│   │   └── nodes.py          # 节点函数
│   ├── storage/              # 持久化层
│   │   ├── sqlite_store.py   # SQLite（故事/世界状态/章节）
│   │   ├── json_store.py     # JSON文件（圣经/事件图）
│   │   └── vector_store.py   # ChromaDB（角色记忆）
│   ├── llm/
│   │   ├── client.py         # LiteLLM统一模型网关（per-agent模型+自动日志）
│   │   ├── model_registry.py # 模型注册表（DB驱动的模型配置管理）
│   │   └── logger.py         # LLM调用日志记录器
│   └── api/                  # FastAPI路由
│       ├── stories.py        # 故事CRUD + 生成触发
│       ├── chapters.py       # 章节读取
│       ├── control.py        # 生成状态控制
│       └── llm_admin.py      # LLM管理中心API（模型/绑定/日志/用量）
├── frontend/                 # Next.js前端
│   ├── app/                  # 页面
│   │   ├── page.tsx          # 首页
│   │   ├── stories/          # 故事仪表盘 + 章节阅读器
│   │   └── admin/            # LLM管理中心 + 请求日志
│   ├── components/           # UI组件
│   ├── lib/                  # API客户端（api.ts + admin-api.ts）
│   └── types/index.ts        # TypeScript类型
├── data/                     # 运行时数据（gitignored）
├── pyproject.toml
├── .env.example
└── .gitignore
```

## API端点

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
| GET | /api/admin/models | 列出模型配置 |
| POST | /api/admin/models | 创建模型配置 |
| PUT | /api/admin/models/{id} | 更新模型配置 |
| DELETE | /api/admin/models/{id} | 删除模型配置 |
| GET | /api/admin/bindings | 获取Agent-模型绑定 |
| PUT | /api/admin/bindings/{agent} | 设置Agent绑定 |
| GET | /api/admin/logs | 查询调用日志 |
| GET | /api/admin/logs/{id} | 日志详情（含完整prompt） |
| GET | /api/admin/usage | 用量统计 |

## 开发路线

- [x] **P0 核心MVP** — 6个Agent线性章节生成
- [x] **LLM管理中心** — 模型配置、Agent绑定、用量监控、请求日志
- [ ] **P1 角色系统** — 独立角色Agent + 记忆 + 知识图谱
- [ ] **P2 世界引擎** — 事件DAG + 并行叙事线 + Camera升级
- [ ] **P3 微调闭环** — 角色数据提取 + LoRA训练 + 热切换
- [ ] **P4 人机协同** — 导演界面 + 实时干预 + 版本管理

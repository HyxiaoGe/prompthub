# PromptHub — 统一提示词管理平台

## 项目概述

PromptHub 是一个面向多 AI 项目团队的统一提示词管理与智能优化平台。解决提示词碎片化、跨项目复用困难、缺乏数据驱动优化三大核心问题。

### 核心业务场景

用户有多个 AI 项目（音频摘要、AI 生图、会议纪要、AI 视频生成），这些项目的提示词存在交叉依赖：
- 会议纪要系统需要调用 AI 生图的提示词来生成配图
- AI 视频生成需要复用 AI 生图的提示词来生成宣传图
- 平台通过 API 统一提供提示词，供各业务系统调用

### 核心差异化能力

**组合编排引擎**：把提示词当作可组合的函数，支持跨项目引用、继承、条件分支和变量覆写。业务系统只需一个 API 调用 `scenes.resolve("meeting_summary_image", variables={...})`，编排引擎自动解析依赖链，返回组装好的最终提示词。

---

## 技术栈

### 后端
- **语言**: Python 3.12+
- **框架**: FastAPI
- **ORM**: SQLAlchemy 2.0 (async) + Alembic (数据库迁移)
- **数据验证**: Pydantic v2
- **异步**: asyncio + httpx (异步 HTTP 客户端)
- **任务队列**: Celery + Redis (异步任务)
- **模板引擎**: Jinja2 (提示词模板渲染)

### 前端
- **框架**: Next.js 15 (App Router)
- **语言**: TypeScript
- **UI 库**: shadcn/ui + Tailwind CSS
- **状态管理**: Zustand
- **数据获取**: TanStack Query (React Query)
- **图表**: Recharts
- **依赖图可视化**: React Flow

### 数据库与基础设施
- **主数据库**: PostgreSQL 16
- **缓存**: Redis 7
- **搜索**: PostgreSQL 全文搜索 (初期，后续可迁移 Elasticsearch)
- **本地开发**: Docker Compose
- **API 文档**: Swagger / ReDoc (FastAPI 内置)

### LLM 集成
- **网关**: LiteLLM (统一多模型接口)
- **支持模型**: Claude / OpenAI / 本地模型

---

## 项目结构

```
prompthub/
├── CLAUDE.md                     # 本文件 - Claude Code 的项目上下文
├── PRD.md                        # 产品需求与分阶段任务清单
├── docker-compose.yml            # 本地开发环境
├── .env.example                  # 环境变量模板
├── Makefile                      # 常用命令快捷方式
│
├── backend/                      # FastAPI 后端
│   ├── pyproject.toml            # Python 依赖管理 (uv)
│   ├── alembic/                  # 数据库迁移
│   │   ├── alembic.ini
│   │   └── versions/
│   ├── app/
│   │   ├── main.py               # FastAPI 应用入口
│   │   ├── config.py             # 配置管理
│   │   ├── database.py           # 数据库连接与会话
│   │   ├── models/               # SQLAlchemy 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── prompt.py         # 提示词模型
│   │   │   ├── version.py        # 版本模型
│   │   │   ├── scene.py          # 场景编排模型
│   │   │   ├── project.py        # 项目模型
│   │   │   ├── user.py           # 用户模型
│   │   │   └── call_log.py       # 调用日志模型
│   │   ├── schemas/              # Pydantic 请求/响应模型
│   │   │   ├── __init__.py
│   │   │   ├── prompt.py
│   │   │   ├── scene.py
│   │   │   ├── project.py
│   │   │   └── analytics.py
│   │   ├── api/                  # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── router.py         # 路由汇总
│   │   │   ├── prompts.py        # 提示词 CRUD API
│   │   │   ├── versions.py       # 版本管理 API
│   │   │   ├── scenes.py         # 场景编排 API
│   │   │   ├── projects.py       # 项目管理 API
│   │   │   ├── optimize.py       # AI 优化 API
│   │   │   └── analytics.py      # 数据分析 API
│   │   ├── services/             # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── prompt_service.py
│   │   │   ├── version_service.py
│   │   │   ├── scene_engine.py   # ⭐ 组合编排引擎
│   │   │   ├── template_engine.py # 模板渲染引擎
│   │   │   ├── dependency_resolver.py # DAG 依赖解析
│   │   │   ├── optimizer.py      # AI 优化服务
│   │   │   └── analytics_service.py
│   │   ├── core/                 # 核心公共模块
│   │   │   ├── __init__.py
│   │   │   ├── auth.py           # 认证鉴权 (API Key)
│   │   │   ├── exceptions.py     # 自定义异常
│   │   │   ├── pagination.py     # 分页工具
│   │   │   └── cache.py          # Redis 缓存封装
│   │   └── tests/                # 测试
│   │       ├── conftest.py
│   │       ├── test_prompts.py
│   │       ├── test_scenes.py
│   │       └── test_engine.py
│   └── scripts/                  # 工具脚本
│       └── seed_data.py          # 种子数据
│
├── frontend/                     # Next.js 前端
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── src/
│   │   ├── app/                  # App Router 页面
│   │   │   ├── layout.tsx        # 全局布局
│   │   │   ├── page.tsx          # 首页 / Dashboard
│   │   │   ├── prompts/          # 提示词管理页面
│   │   │   │   ├── page.tsx      # 列表
│   │   │   │   ├── [id]/
│   │   │   │   │   └── page.tsx  # 详情 / 编辑
│   │   │   │   └── new/
│   │   │   │       └── page.tsx  # 新建
│   │   │   ├── scenes/           # 场景编排页面
│   │   │   │   ├── page.tsx
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx
│   │   │   ├── projects/         # 项目管理页面
│   │   │   │   ├── page.tsx
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx
│   │   │   └── analytics/        # 数据分析页面
│   │   │       └── page.tsx
│   │   ├── components/           # 公共组件
│   │   │   ├── ui/               # shadcn/ui 组件
│   │   │   ├── layout/           # 布局组件 (Sidebar, Header)
│   │   │   ├── prompt/           # 提示词相关组件
│   │   │   ├── scene/            # 场景相关组件
│   │   │   └── analytics/        # 分析相关组件
│   │   ├── lib/                  # 工具库
│   │   │   ├── api.ts            # API 客户端
│   │   │   ├── utils.ts
│   │   │   └── constants.ts
│   │   ├── hooks/                # 自定义 Hooks
│   │   │   ├── use-prompts.ts
│   │   │   ├── use-scenes.ts
│   │   │   └── use-analytics.ts
│   │   ├── stores/               # Zustand 状态管理
│   │   │   └── app-store.ts
│   │   └── types/                # TypeScript 类型定义
│   │       ├── prompt.ts
│   │       ├── scene.ts
│   │       └── api.ts
│   └── public/
│       └── ...
│
└── sdk/                          # Python SDK (供外部系统调用)
    ├── pyproject.toml
    ├── prompthub/
    │   ├── __init__.py
    │   ├── client.py             # SDK 客户端
    │   ├── resources/
    │   │   ├── prompts.py
    │   │   └── scenes.py
    │   └── types.py
    └── examples/
        └── basic_usage.py
```

---

## 数据模型

### 核心表

```sql
-- 项目
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 提示词
CREATE TABLE prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    format VARCHAR(20) DEFAULT 'text',         -- text | json | yaml | chat
    template_engine VARCHAR(20) DEFAULT 'jinja2', -- jinja2 | mustache | none
    variables JSONB DEFAULT '[]',               -- 变量定义
    tags TEXT[] DEFAULT '{}',
    category VARCHAR(100),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    is_shared BOOLEAN DEFAULT false,            -- 是否发布到共享仓库
    current_version VARCHAR(20) DEFAULT '1.0.0',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(project_id, slug)
);

-- 提示词版本
CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id UUID REFERENCES prompts(id) ON DELETE CASCADE,
    version VARCHAR(20) NOT NULL,               -- 语义化版本 1.2.3
    content TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    changelog TEXT,
    status VARCHAR(20) DEFAULT 'draft',         -- draft | published | deprecated
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(prompt_id, version)
);

-- 场景编排
CREATE TABLE scenes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) NOT NULL,
    description TEXT,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    pipeline JSONB NOT NULL,                    -- 编排管道配置
    merge_strategy VARCHAR(20) DEFAULT 'concat', -- concat | chain | select_best
    separator VARCHAR(50) DEFAULT '\n\n',
    output_format VARCHAR(50),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(project_id, slug)
);

-- 提示词引用关系
CREATE TABLE prompt_refs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_prompt_id UUID REFERENCES prompts(id) ON DELETE CASCADE,
    target_prompt_id UUID REFERENCES prompts(id) ON DELETE CASCADE,
    source_project_id UUID REFERENCES projects(id),
    target_project_id UUID REFERENCES projects(id),
    ref_type VARCHAR(20) NOT NULL,              -- extends | includes | composes
    override_config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 调用日志
CREATE TABLE call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id UUID REFERENCES prompts(id),
    scene_id UUID REFERENCES scenes(id),
    prompt_version VARCHAR(20),
    caller_system VARCHAR(100),                 -- 调用方系统名称
    caller_ip VARCHAR(45),
    input_variables JSONB,
    rendered_content TEXT,
    token_count INTEGER,
    response_time_ms INTEGER,
    quality_score FLOAT,                        -- 0-5 质量评分
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 用户
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(20) DEFAULT 'editor',          -- admin | editor | viewer
    api_key VARCHAR(64) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## API 设计规范

### 基础约定
- 基础路径: `/api/v1/`
- 认证: `Authorization: Bearer {api_key}` 请求头
- 分页: `?page=1&page_size=20` 查询参数
- 排序: `?sort_by=created_at&order=desc`
- 过滤: `?project_id=xxx&tags=image-gen,base`
- 响应格式: 统一包装

```json
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

### 错误响应

```json
{
  "code": 40001,
  "message": "Prompt not found",
  "detail": "No prompt with slug 'xxx' in project 'yyy'"
}
```

### 核心 API 端点

```
# 提示词管理
POST   /api/v1/prompts                    创建提示词
GET    /api/v1/prompts                    列表（支持过滤、分页、搜索）
GET    /api/v1/prompts/{id}               获取详情
PUT    /api/v1/prompts/{id}               更新
DELETE /api/v1/prompts/{id}               软删除
GET    /api/v1/prompts/{id}/versions      版本历史
POST   /api/v1/prompts/{id}/publish       发布新版本
POST   /api/v1/prompts/{id}/render        渲染模板（传入变量，返回渲染结果）

# 场景编排
POST   /api/v1/scenes                     创建场景
GET    /api/v1/scenes                     列表
GET    /api/v1/scenes/{id}                获取场景配置
PUT    /api/v1/scenes/{id}                更新
POST   /api/v1/scenes/{id}/resolve        ⭐ 解析场景 → 返回组装后的最终提示词
GET    /api/v1/scenes/{id}/dependencies   查看依赖图

# 项目管理
POST   /api/v1/projects                   创建项目
GET    /api/v1/projects                   列表
GET    /api/v1/projects/{id}              详情
GET    /api/v1/projects/{id}/prompts      项目下的提示词

# 共享仓库
GET    /api/v1/shared/prompts             浏览共享提示词
POST   /api/v1/shared/prompts/{id}/fork   Fork 到自己项目

# 数据分析
GET    /api/v1/analytics/overview         全局概览
GET    /api/v1/analytics/trending         热门提示词
GET    /api/v1/analytics/prompts/{id}     单个提示词统计
```

---

## 编码规范

### Python 后端
- 使用 `uv` 管理依赖（不用 pip/poetry）
- 使用 `ruff` 做代码检查和格式化
- 类型注解：所有函数必须有参数和返回值类型注解
- 异步优先：数据库操作和外部调用全部使用 async/await
- 异常处理：自定义异常类，在 API 层统一捕获
- 日志：使用 `structlog` 结构化日志
- 测试：pytest + pytest-asyncio，覆盖核心业务逻辑

### TypeScript 前端
- 严格模式：`strict: true`
- 组件规范：函数式组件 + Hooks
- 命名规范：组件 PascalCase，函数/变量 camelCase，常量 UPPER_SNAKE_CASE
- API 调用：统一通过 TanStack Query + api client
- 样式：Tailwind CSS 优先，避免自定义 CSS

### Git 规范
- 分支：`main` (生产) / `develop` (开发) / `feature/*` / `fix/*`
- 提交信息：Conventional Commits 格式
  - `feat: add prompt version management`
  - `fix: resolve circular dependency detection`
  - `docs: update API documentation`

---

## 开发环境启动

```bash
# 1. 克隆项目后，复制环境变量
cp .env.example .env

# 2. 启动基础设施 (PostgreSQL + Redis)
docker-compose up -d

# 3. 后端
cd backend
uv sync                    # 安装依赖
alembic upgrade head       # 执行数据库迁移
python scripts/seed_data.py  # 初始化种子数据
uvicorn app.main:app --reload --port 8000

# 4. 前端
cd frontend
pnpm install
pnpm dev                   # 启动 Next.js 开发服务器 (端口 3000)

# 5. 访问
# 前端: http://localhost:3000
# API 文档: http://localhost:8000/docs
```

---

## 重要约束与注意事项

1. **场景编排是核心**：`scene_engine.py` 和 `dependency_resolver.py` 是整个系统最重要的模块，必须有完善的单元测试
2. **循环依赖检测**：提示词引用链必须做 DAG 检测，防止 A→B→C→A 的循环
3. **版本锁定**：场景引用提示词时可以指定版本，避免上游变更意外影响下游
4. **缓存策略**：热点提示词缓存到 Redis，TTL 5 分钟，提示词更新时主动失效
5. **API 兼容性**：所有 API 都带版本前缀 `/api/v1/`，后续升级不破坏旧接口
6. **前后端分离**：Next.js 前端通过 HTTP 调用 FastAPI 后端，不共享运行时

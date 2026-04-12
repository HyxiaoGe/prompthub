# PromptHub 架构

## 项目概述

PromptHub 是面向多 AI 项目的统一提示词管理与智能优化平台。解决提示词碎片化、跨项目复用困难、缺乏数据驱动优化三大核心问题。

核心差异化能力：**组合编排引擎** — 把提示词当作可组合的函数，支持跨项目引用、继承、条件分支和变量覆写。

## 技术栈

- **后端**: Python 3.12 + FastAPI + SQLAlchemy 2.0 (async) + Alembic + Redis + Jinja2
- **前端**: Next.js 15 (App Router) + TypeScript + shadcn/ui + Tailwind CSS + Zustand + TanStack Query
- **数据库**: PostgreSQL 16 + Redis 7
- **LLM**: LiteLLM 网关（Claude / OpenAI / 本地模型）

## 分层架构

```
API (app/api/)  →  Service (app/services/)  →  Models (app/models/)
                       ↓
                  Core (app/core/)  — 公共模块（auth、exceptions、pagination、response）
```

依赖方向只能向下，不能反向：
- API 层可以调用 Service 和 Core
- Service 层可以调用 Models 和 Core
- Models 和 Core 不能调用 API 或 Service

## 项目结构

```
prompthub/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI 路由（prompts, scenes, projects, ai, versions, shared）
│   │   ├── services/     # 业务逻辑（prompt_service, scene_engine, template_engine, dependency_resolver...）
│   │   ├── models/       # SQLAlchemy 数据模型（prompt, version, scene, project, user, call_log, prompt_ref）
│   │   ├── schemas/      # Pydantic 请求/响应模型
│   │   ├── core/         # 公共模块（auth, exceptions, pagination, response, enums）
│   │   └── tests/        # pytest 测试
│   └── scripts/          # 工具脚本
├── frontend/             # Next.js 前端
├── sdk/                  # Python SDK（供外部系统调用）
└── docs/                 # 文档
```

## 核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| 组合编排引擎 | `services/scene_engine.py` | 解析场景编排管道，组装最终提示词 |
| 依赖解析 | `services/dependency_resolver.py` | DAG 依赖解析，循环检测 |
| 模板引擎 | `services/template_engine.py` | Jinja2 沙箱渲染 |
| AI 服务 | `services/ai_service.py` + `llm_client.py` | 提示词优化、评估、变体生成 |

## 数据模型

核心表：projects → prompts → prompt_versions → scenes → prompt_refs → call_logs → users

关键关系：
- prompt 属于 project，通过 (project_id, slug) 唯一标识
- prompt_versions 记录版本历史，语义化版本号
- scenes 通过 pipeline (JSONB) 定义编排管道
- prompt_refs 记录提示词间的引用关系（extends/includes/composes）
- call_logs 记录每次调用的输入、输出、耗时、质量评分

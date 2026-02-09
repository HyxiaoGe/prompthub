# PromptHub — 产品需求文档 (PRD)

## Phase 1: 项目骨架与基础 CRUD（MVP 基础）

### 1.1 项目初始化
- [x] 创建 `docker-compose.yml`（PostgreSQL 16 + Redis 7）
- [x] 创建 `.env.example` 和 `.env` 配置
- [x] 创建 `Makefile` 常用命令

### 1.2 后端骨架
- [x] 初始化 Python 项目（`pyproject.toml`，使用 uv）
- [x] 安装核心依赖：fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, pydantic, redis, jinja2, structlog, ruff
- [x] 创建 `app/main.py` FastAPI 应用入口（含 CORS、异常处理）
- [x] 创建 `app/config.py` 配置管理（从环境变量读取）
- [x] 创建 `app/database.py` 异步数据库连接（SQLAlchemy async session）
- [x] 配置 Alembic 数据库迁移

### 1.3 数据模型
- [x] 创建 `models/user.py` 用户模型
- [x] 创建 `models/project.py` 项目模型
- [x] 创建 `models/prompt.py` 提示词模型
- [x] 创建 `models/version.py` 提示词版本模型
- [x] 创建 `models/scene.py` 场景编排模型
- [x] 创建 `models/prompt_ref.py` 提示词引用关系模型
- [x] 创建 `models/call_log.py` 调用日志模型
- [x] 生成初始 Alembic 迁移文件并执行

### 1.4 提示词 CRUD API
- [x] 创建 Pydantic schemas（`schemas/prompt.py`）
- [x] 实现 `services/prompt_service.py` 业务逻辑
- [x] 实现 `api/prompts.py` 路由：
  - [x] `POST /api/v1/prompts` 创建
  - [x] `GET /api/v1/prompts` 列表（分页、过滤、搜索）
  - [x] `GET /api/v1/prompts/{id}` 详情
  - [x] `PUT /api/v1/prompts/{id}` 更新
  - [x] `DELETE /api/v1/prompts/{id}` 软删除
- [x] 统一响应格式封装
- [x] 统一异常处理

### 1.5 版本管理 API
- [x] 创建 Pydantic schemas（`schemas/version.py`）
- [x] 实现 `services/version_service.py`
- [x] 实现 `api/versions.py` 路由：
  - [x] `GET /api/v1/prompts/{id}/versions` 版本列表
  - [x] `POST /api/v1/prompts/{id}/publish` 发布新版本
  - [x] `GET /api/v1/prompts/{id}/versions/{version}` 获取特定版本
- [x] 语义化版本号自动递增逻辑

### 1.6 项目管理 API
- [x] 创建 Pydantic schemas（`schemas/project.py`）
- [x] 实现 `services/project_service.py`
- [x] 实现 `api/projects.py` 路由：
  - [x] `POST /api/v1/projects` 创建
  - [x] `GET /api/v1/projects` 列表
  - [x] `GET /api/v1/projects/{id}` 详情
  - [x] `GET /api/v1/projects/{id}/prompts` 项目下的提示词

### 1.7 认证
- [x] 实现 API Key 认证中间件（`core/auth.py`）
- [x] 请求头：`Authorization: Bearer {api_key}`
- [x] 种子数据脚本创建默认用户和 API Key

### 1.8 基础测试
- [x] 配置 pytest + pytest-asyncio + httpx（测试客户端）
- [x] 提示词 CRUD 测试
- [x] 版本管理测试
- [x] 项目管理测试

---

## Phase 2: 组合编排引擎（核心差异化）

### 2.1 模板渲染引擎
- [ ] 实现 `services/template_engine.py`
  - [ ] Jinja2 模板渲染
  - [ ] 变量校验（必填、类型、枚举）
  - [ ] 安全沙箱（禁止危险操作）
- [ ] 实现 `POST /api/v1/prompts/{id}/render` 接口

### 2.2 依赖解析器
- [ ] 实现 `services/dependency_resolver.py`
  - [ ] 构建 DAG 依赖图
  - [ ] 循环引用检测（拓扑排序）
  - [ ] 依赖树可视化数据输出
- [ ] 实现 `GET /api/v1/scenes/{id}/dependencies` 接口

### 2.3 场景编排引擎 ⭐
- [ ] 实现 `services/scene_engine.py`
  - [ ] 解析场景 pipeline 配置
  - [ ] 逐步骤执行：获取提示词 → 条件检查 → 变量合并 → 模板渲染
  - [ ] 变量优先级：场景覆写 > 输入变量 > 提示词默认值
  - [ ] 合并策略实现（concat / chain / select_best）
  - [ ] 跨项目引用权限检查（只能引用 is_shared=true 的提示词）
- [ ] 实现场景 CRUD API（`api/scenes.py`）
- [ ] 实现 `POST /api/v1/scenes/{id}/resolve` 核心接口

### 2.4 共享仓库
- [ ] 实现提示词发布到共享（`POST /api/v1/prompts/{id}/share`）
- [ ] 实现共享浏览（`GET /api/v1/shared/prompts`）
- [ ] 实现 Fork（`POST /api/v1/shared/prompts/{id}/fork`）

### 2.5 引用关系管理
- [ ] 提示词引用 CRUD（自动维护 prompt_refs 表）
- [ ] 变更影响分析：当共享提示词更新时，列出所有受影响的下游场景
- [ ] 版本锁定：场景可指定引用特定版本或 latest

### 2.6 编排引擎测试
- [ ] 单提示词模板渲染测试
- [ ] 多步骤编排解析测试
- [ ] 循环依赖检测测试
- [ ] 跨项目引用测试
- [ ] 条件分支测试
- [ ] 变量覆写优先级测试

---

## Phase 3: 前端界面

### 3.1 前端项目初始化
- [ ] 创建 Next.js 15 项目（App Router, TypeScript）
- [ ] 安装和配置：Tailwind CSS, shadcn/ui, Zustand, TanStack Query, React Flow, Recharts
- [ ] 创建 API 客户端（`lib/api.ts`）
- [ ] 创建全局布局（侧边栏导航 + 顶栏）

### 3.2 提示词管理页面
- [ ] 提示词列表页（搜索、过滤、标签筛选、分页）
- [ ] 提示词新建/编辑页（内容编辑器 + 变量定义 + 标签管理）
- [ ] 提示词详情页（基本信息 + 版本历史 + 引用关系）
- [ ] 模板预览面板（实时输入变量 → 预览渲染结果）

### 3.3 场景编排页面
- [ ] 场景列表页
- [ ] 场景编辑器（可视化 pipeline 编辑）
- [ ] 依赖图可视化（React Flow 展示引用关系 DAG）
- [ ] 场景测试面板（输入变量 → 调用 resolve → 查看结果）

### 3.4 项目管理页面
- [ ] 项目列表和创建
- [ ] 项目详情（含项目下的提示词和场景）
- [ ] 共享仓库浏览和 Fork

### 3.5 Dashboard
- [ ] 概览统计卡片（总提示词数、总调用量、活跃场景数）
- [ ] 热门提示词排行
- [ ] 最近活动时间线

---

## Phase 4: 数据分析与缓存

### 4.1 调用日志记录
- [ ] 在 resolve 和 render 接口中自动记录调用日志
- [ ] 记录：调用方、提示词/场景、版本、变量、Token 数、响应时间

### 4.2 分析 API
- [ ] `GET /api/v1/analytics/overview` 全局概览
- [ ] `GET /api/v1/analytics/trending` 热门排行（按调用量）
- [ ] `GET /api/v1/analytics/prompts/{id}` 单个提示词的趋势

### 4.3 分析 Dashboard 页面
- [ ] 全局统计看板（Recharts 图表）
- [ ] 热门提示词排行
- [ ] 调用趋势图（按天/周）
- [ ] 项目维度对比

### 4.4 Redis 缓存
- [ ] 热点提示词缓存（TTL 5分钟）
- [ ] 场景 resolve 结果缓存（相同输入参数）
- [ ] 缓存主动失效（提示词更新时清除相关缓存）

---

## Phase 5: AI 智能优化（后续迭代）

### 5.1 提示词优化
- [ ] 集成 LiteLLM 统一模型调用
- [ ] 实现基础优化：分析 → 生成候选 → 评估 → 选最优
- [ ] `POST /api/v1/optimize` 接口

### 5.2 推荐引擎
- [ ] 基于标签和使用场景的推荐
- [ ] 「使用此提示词的项目也在用…」协同过滤

### 5.3 Prompt Linting
- [ ] 检查常见反模式（过长、矛盾指令、冗余）
- [ ] 变量未使用/未定义检测

---

## Phase 6: Python SDK

### 6.1 SDK 开发
- [ ] 创建 `prompthub-sdk` 包
- [ ] 实现 `PromptHubClient` 核心类
- [ ] 提示词获取和渲染
- [ ] 场景 resolve 调用
- [ ] 错误处理和重试
- [ ] 本地缓存（可选）

### 6.2 SDK 示例
- [ ] 基础用法示例
- [ ] 音频摘要系统集成示例
- [ ] 会议纪要生图集成示例

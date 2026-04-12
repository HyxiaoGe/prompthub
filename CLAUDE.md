# PromptHub

统一提示词管理与智能优化平台。后端 FastAPI + PostgreSQL + Redis，前端 Next.js 15 + shadcn/ui。

## 架构速览

四层架构，依赖只能向下：API → Service → Models，Core 为公共模块。
核心：组合编排引擎（scene_engine + dependency_resolver），提示词 DAG 编排。
详见 → docs/ARCHITECTURE.md

## 工作流程

1. **变更前**：超过 3 个文件的改动，先输出影响分析
2. **编码中**：遵守 docs/ARCHITECTURE_RULES.md，分层依赖不能反向
3. **变更后**：运行 `ruff check .` + `ruff format --check .`
4. **提交前**：确认 CI 门禁通过（架构检查 + Ruff lint）

## 关键约束

- 循环依赖检测：提示词引用链必须 DAG 检测
- 版本锁定：场景引用提示词可指定版本
- 缓存：Redis TTL 5min，更新时主动失效
- API 兼容：`/api/v1/` 前缀，升级不破坏旧接口

## 开发命令

```bash
cd backend && uv sync && uvicorn app.main:app --reload --port 8000  # 后端
cd frontend && pnpm dev                                              # 前端
ruff check . && ruff format --check .                                # lint
python scripts/check_architecture.py                                 # 架构检查
```

## 文档索引

- [架构设计](docs/ARCHITECTURE.md) — 分层架构、数据模型、核心模块
- [架构约束](docs/ARCHITECTURE_RULES.md) — 分层规则、关键约束
- [API 参考](docs/API_REFERENCE.md) — 端点一览、请求/响应格式
- [编码规范](docs/CODING_CONVENTIONS.md) — Python/TypeScript/Git 规范
- [SDK 集成](docs/sdk-integration-guide.md) — 外部系统接入指南

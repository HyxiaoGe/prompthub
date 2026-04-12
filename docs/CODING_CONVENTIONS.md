# PromptHub 编码规范

## Python 后端

- 依赖管理: `uv`（不用 pip/poetry）
- Lint + Format: `ruff`（line-length: 120, rules: E/F/I/N/UP/B/SIM）
- 类型注解: 所有函数必须有参数和返回值类型注解
- 异步优先: 数据库操作和外部调用全部 async/await
- 异常处理: 自定义异常类（app/core/exceptions.py），API 层统一捕获
- 日志: `structlog` 结构化日志
- 测试: pytest + pytest-asyncio，覆盖核心业务逻辑

## TypeScript 前端

- 严格模式: `strict: true`
- 组件: 函数式组件 + Hooks
- 命名: 组件 PascalCase，函数/变量 camelCase，常量 UPPER_SNAKE_CASE
- API 调用: TanStack Query + api client
- 样式: Tailwind CSS 优先，避免自定义 CSS

## Git 规范

- 分支: `main`(生产) / `develop`(开发) / `feature/*` / `fix/*`
- 提交: Conventional Commits — `feat:` / `fix:` / `docs:` / `refactor:`

## 开发环境

```bash
# 后端
cd backend && uv sync && alembic upgrade head && uvicorn app.main:app --reload --port 8000

# 前端
cd frontend && pnpm install && pnpm dev

# 基础设施
docker-compose up -d  # PostgreSQL + Redis
```

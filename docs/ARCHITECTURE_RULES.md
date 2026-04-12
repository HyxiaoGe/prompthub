# PromptHub 架构约束

## 分层依赖规则

依赖只能向下，违反将被 CI 拦截：

| 层 | 可以 import | 禁止 import |
|----|------------|------------|
| `app/api/` | services, models, schemas, core | — |
| `app/services/` | models, core | api |
| `app/models/` | core | api, services |
| `app/core/` | — | api, services, models |

## 关键约束

1. **循环依赖检测**：提示词引用链必须做 DAG 检测，防止 A→B→C→A 循环
2. **版本锁定**：场景引用提示词时可指定版本，避免上游变更意外影响下游
3. **缓存策略**：热点提示词缓存到 Redis，TTL 5 分钟，更新时主动失效
4. **API 兼容性**：所有 API 带版本前缀 `/api/v1/`，升级不破坏旧接口
5. **前后端分离**：Next.js 前端通过 HTTP 调用 FastAPI 后端，不共享运行时
6. **场景编排是核心**：`scene_engine.py` 和 `dependency_resolver.py` 必须有完善测试

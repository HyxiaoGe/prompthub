# PromptHub API Reference

## 基础约定

- 基础路径: `/api/v1/`
- 认证: `Authorization: Bearer {api_key}`
- 分页: `?page=1&page_size=20`
- 排序: `?sort_by=created_at&order=desc`
- 过滤: `?project_id=xxx&tags=image-gen,base`

## 响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "meta": { "page": 1, "page_size": 20, "total": 100 }
}
```

## 端点一览

### 提示词管理
```
POST   /api/v1/prompts                    创建提示词
GET    /api/v1/prompts                    列表（过滤、分页、搜索）
GET    /api/v1/prompts/{id}               详情
PUT    /api/v1/prompts/{id}               更新
DELETE /api/v1/prompts/{id}               软删除
GET    /api/v1/prompts/{id}/versions      版本历史
POST   /api/v1/prompts/{id}/publish       发布新版本
POST   /api/v1/prompts/{id}/render        渲染模板
```

### 场景编排
```
POST   /api/v1/scenes                     创建场景
GET    /api/v1/scenes                     列表
GET    /api/v1/scenes/{id}                场景配置
PUT    /api/v1/scenes/{id}                更新
POST   /api/v1/scenes/{id}/resolve        解析场景 → 组装最终提示词
GET    /api/v1/scenes/{id}/dependencies   依赖图
```

### 项目管理
```
POST   /api/v1/projects                   创建项目
GET    /api/v1/projects                   列表
GET    /api/v1/projects/{id}              详情
GET    /api/v1/projects/{id}/prompts      项目下的提示词
```

### 共享仓库
```
GET    /api/v1/shared/prompts             浏览共享提示词
POST   /api/v1/shared/prompts/{id}/fork   Fork 到自己项目
```

### AI 能力
```
POST   /api/v1/ai/generate               AI 生成提示词
POST   /api/v1/ai/enhance                AI 优化提示词
POST   /api/v1/ai/variants               生成变体
POST   /api/v1/ai/evaluate               评估提示词质量
POST   /api/v1/ai/evaluate/batch          批量评估
POST   /api/v1/ai/lint                   提示词 lint 检查
```

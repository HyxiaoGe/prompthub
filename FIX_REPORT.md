# Prompt 修复报告

**日期**: 2026-02-15

---

## 修复汇总

| # | Prompt | 项目 | 问题 | 操作 | Lint 分数变化 |
|---|--------|------|------|------|--------------|
| 1 | `image-gen-v2` | ai-image-gen | `undefined_variable: subject` (error) | 在 variables 中补充 subject 定义 | 70 → **90** (+20) |
| 2a | `visual-outline-general-zh` | audio-visual | `unused_variable: quality_notice` (warning) | 在 transcript 后插入 `{{ quality_notice }}` | 80 → **90** (+10) |
| 2b | `visual-outline-explainer-zh` | audio-visual | `unused_variable: quality_notice` (warning) | 同上 | 80 → **90** (+10) |
| 2c | `visual-outline-documentary-zh` | audio-visual | `unused_variable: quality_notice` (warning) | 同上 | 80 → **90** (+10) |
| 3 | `summary-actionitems-en` | audio-summary | `unused_variable: format_rules` (warning) | 在 transcript 后插入 `{{ format_rules }}` | 70 → **70** (±0) |

---

## Fix 1: image-gen-v2 — `undefined_variable: subject`

**问题**: 模板中使用 `{{subject}}` 但 variables 定义为空 `[]`，渲染时会失败。

**操作**: 在 variables 中添加：
```json
{"name": "subject", "type": "string", "required": true, "description": "The subject/topic for image generation"}
```

**结果**:
- `undefined_variable` 已消除 ✅
- 剩余 `vague` (LLM warning) — 内容本身就很短 (`Create {{subject}}`)
- Lint: 70 → **90**

---

## Fix 2: audio-visual 三个 prompt — `unused_variable: quality_notice`

**问题**: `quality_notice` 定义在 variables 中但模板内容未引用。这是一个跨项目共享变量（来自 audio-shared），其他项目（如 audio-summary）已正确使用。

**操作**: 在 `{{ transcript }}` 之后、输出要求之前插入 `{{ quality_notice }}`。

三个 prompt 的修改位置一致：
```
{{ transcript }}

{{ quality_notice }}    ← 新增

生成要求：...
```

**结果**:
- 三个 prompt 的 `unused_variable` 全部消除 ✅
- 剩余的 `redundant` 是 LLM 发现的内容风格问题，非变量相关
- Lint: 80 → **90**（三个都一样）

---

## Fix 3: summary-actionitems-en — `unused_variable: format_rules`

**问题**: `format_rules` 定义在 variables 中但模板未引用。该 prompt 已有硬编码的格式规则段落。

**操作**: 在 `{{ transcript }}` 之后插入 `{{ format_rules }}`，使其可通过变量覆写格式要求。

```
{{ transcript }}

{{ format_rules }}    ← 新增

Output format:
# Action Items & Plans
...
```

**结果**:
- `unused_variable` 已消除 ✅
- 分数未变（70 → 70）：因为 LLM 重新分析后发现了一个新的 `ambiguous` issue（"if speaker info available" 含义不清），抵消了 unused_variable 的修复
- 剩余 issues: `redundant`（格式规则重复）、`vague`（"clear, actionable items" 定义不明确）、`ambiguous`（"if speaker info available" 条件不清）

---

## 修复前后对比

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| Error 级 issue | 1 (undefined_variable) | **0** ✅ |
| unused_variable warnings | 4 | **0** ✅ |
| 5 个 prompt 平均 lint 分 | 76.0 | **86.0** |

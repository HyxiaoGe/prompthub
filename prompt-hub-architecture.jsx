import { useState } from "react";

const modules = [
  {
    id: "api-gateway",
    label: "API Gateway",
    category: "access",
    x: 400,
    y: 60,
    w: 200,
    h: 56,
    desc: "统一入口层",
    detail: {
      title: "API Gateway / 统一接入层",
      points: [
        "RESTful API + GraphQL 双协议支持",
        "API Key / OAuth2 认证鉴权",
        "限流、熔断、降级保护",
        "请求日志与审计追踪",
        "SDK 封装（Python / Node / Java）",
      ],
      example: `GET  /api/v1/prompts/{id}?version=latest
POST /api/v1/prompts/resolve
     Body: { "scene": "meeting_summary_image",
             "variables": { "style": "商务" } }

→ 自动解析依赖链，返回组装后的最终提示词`,
    },
  },
  {
    id: "prompt-core",
    label: "提示词核心引擎",
    category: "core",
    x: 130,
    y: 190,
    w: 220,
    h: 56,
    desc: "CRUD · 版本 · 模板",
    detail: {
      title: "Prompt Core Engine / 提示词核心引擎",
      points: [
        "提示词 CRUD 管理（创建/读取/更新/删除）",
        "Git-like 版本控制：分支、标签、回滚",
        "Jinja2/Mustache 模板引擎，支持变量插值",
        "多格式支持：纯文本、JSON、YAML、Chat 格式",
        "元数据管理：标签、分类、作者、场景绑定",
      ],
      example: `prompt:
  id: "img_gen_base_v2"
  template: |
    Generate a {{style}} image of {{subject}},
    with {{mood}} atmosphere, {{resolution}}
  variables:
    style: { type: enum, values: [realistic, cartoon, watercolor] }
    subject: { type: string, required: true }
    mood: { type: string, default: "professional" }
    resolution: { type: string, default: "1024x1024" }
  tags: [image-gen, base, shared]
  version: 2.3.1`,
    },
  },
  {
    id: "compose-engine",
    label: "组合编排引擎",
    category: "core",
    x: 400,
    y: 190,
    w: 200,
    h: 56,
    desc: "依赖 · 继承 · 编排",
    detail: {
      title: "Composition Engine / 组合编排引擎 ⭐ 核心差异化",
      points: [
        "提示词引用与继承（extends / $ref）",
        "DAG 依赖图解析，防循环检测",
        "场景化编排：一个场景可组合多个提示词片段",
        "条件分支：根据输入参数动态选择提示词路径",
        "跨项目共享：会议纪要 → 调用生图基础提示词",
      ],
      example: `# 会议纪要生图场景的编排定义
scene: "meeting_summary_image"
pipeline:
  - ref: "prompts/img_gen_base_v2"      # 引用生图基础提示词
    override:
      style: "商务简约"
      mood: "professional"
  - ref: "prompts/meeting_visual_addon"  # 叠加会议可视化增强
    condition: "input.has_chart == true"
  - merge_strategy: "concat_with_separator"
    separator: "\\n\\n"

# 视频宣传图也可以引用同一个 img_gen_base_v2
scene: "video_promo_thumbnail"
pipeline:
  - ref: "prompts/img_gen_base_v2"
    override:
      style: "活力动感"
      resolution: "1920x1080"`,
    },
  },
  {
    id: "project-mgr",
    label: "项目空间管理",
    category: "core",
    x: 650,
    y: 190,
    w: 200,
    h: 56,
    desc: "隔离 · 共享 · 权限",
    detail: {
      title: "Project Space / 项目空间管理",
      points: [
        "项目级隔离：每个项目独立的提示词空间",
        "共享仓库：可发布提示词到公共/团队仓库",
        "权限模型：Owner / Editor / Viewer 三级",
        "引用审计：追踪谁在用哪个共享提示词",
        "项目模板：快速初始化新项目的提示词集",
      ],
      example: `projects:
  - name: "音频摘要生成"
    own_prompts: [audio_summary, outline_gen, meeting_minutes]
    shared_refs: []

  - name: "AI 生图"
    own_prompts: [img_gen_base, style_presets, negative_prompts]
    published_to_shared: [img_gen_base, style_presets]  # 发布到共享

  - name: "AI 视频生成"
    own_prompts: [video_script, transition_prompts]
    shared_refs: [img_gen_base, style_presets]  # 引用共享

  - name: "会议纪要"
    own_prompts: [minutes_template, action_items]
    shared_refs: [img_gen_base]  # 引用共享生图提示词`,
    },
  },
  {
    id: "ai-optimize",
    label: "AI 智能优化",
    category: "intelligence",
    x: 130,
    y: 340,
    w: 220,
    h: 56,
    desc: "优化 · 推荐 · 评估",
    detail: {
      title: "AI Optimization / 智能优化引擎",
      points: [
        "自动优化：基于历史效果数据，用 LLM 改写提示词",
        "A/B 测试框架：对比不同版本的实际产出质量",
        "推荐引擎：根据场景和历史偏好推荐提示词模板",
        "质量评估：自动打分 + 人工反馈闭环",
        "Prompt Linting：检查常见反模式和冗余",
      ],
      example: `# 优化请求示例
POST /api/v1/optimize
{
  "prompt_id": "meeting_minutes_v3",
  "objective": "提高摘要的结构化程度和要点提取准确率",
  "constraints": {
    "max_tokens": 500,
    "must_include": ["参会人", "决议事项", "待办"]
  },
  "eval_dataset": "meeting_samples_50",
  "strategy": "iterative"  // iterative | ab_test | genetic
}

→ 返回优化后的提示词 + 对比评估报告`,
    },
  },
  {
    id: "analytics",
    label: "数据分析平台",
    category: "intelligence",
    x: 400,
    y: 340,
    w: 200,
    h: 56,
    desc: "统计 · 追踪 · 洞察",
    detail: {
      title: "Analytics Platform / 数据分析平台",
      points: [
        "调用量统计：按项目/场景/提示词维度聚合",
        "热门提示词排行：全局 & 项目级 Top N",
        "效果追踪：Token 消耗、响应质量评分趋势",
        "成本分析：各项目/场景的 LLM 调用成本分摊",
        "异常告警：突发调用量、质量下降自动通知",
      ],
      example: `Dashboard 核心指标：
┌────────────────────────────────────┐
│ 今日调用量    12,847  ↑ 12%       │
│ 活跃提示词    89 / 234             │
│ 平均质量评分  4.2 / 5.0  ↑ 0.3    │
│ Token 消耗    2.1M     ↓ 5%       │
│ 热门 Top 3:                        │
│   1. img_gen_base_v2   (3,201 次)  │
│   2. meeting_minutes   (2,847 次)  │
│   3. video_script_v1   (1,923 次)  │
└────────────────────────────────────┘`,
    },
  },
  {
    id: "personalize",
    label: "个性化引擎",
    category: "intelligence",
    x: 650,
    y: 340,
    w: 200,
    h: 56,
    desc: "用户画像 · 偏好学习",
    detail: {
      title: "Personalization Engine / 个性化引擎",
      points: [
        "用户/团队画像：常用场景、偏好风格、质量标准",
        "智能默认值：根据历史自动填充变量参数",
        "上下文感知：根据当前项目推荐相关提示词",
        "偏好学习：从用户的编辑行为中学习偏好模式",
        "协作推荐：「使用此提示词的团队也在用…」",
      ],
      example: `# 个性化推荐示例
GET /api/v1/recommendations?user=zhang_san&project=video_gen

Response:
{
  "recommended": [
    {
      "prompt": "cinematic_lighting_addon",
      "reason": "你常用的 img_gen_base 搭配此提示词效果评分+18%",
      "used_by": ["视频团队 85%", "设计团队 62%"]
    },
    {
      "prompt": "emotion_style_preset",
      "reason": "基于你最近偏好的「温暖治愈」风格",
      "match_score": 0.91
    }
  ]
}`,
    },
  },
  {
    id: "storage",
    label: "存储层",
    category: "infra",
    x: 220,
    y: 480,
    w: 180,
    h: 52,
    desc: "PostgreSQL · Redis · S3",
    detail: {
      title: "Storage Layer / 存储层",
      points: [
        "PostgreSQL：提示词元数据、版本、用户、项目",
        "Redis：热点提示词缓存、会话状态、限流计数",
        "S3/MinIO：提示词快照归档、评估数据集",
        "Elasticsearch：全文搜索、标签检索",
      ],
      example: `核心表设计：
prompts         → id, content, template, project_id, created_by
prompt_versions → id, prompt_id, version, content, changelog
prompt_refs     → source_id, target_id, ref_type, override_config
scenes          → id, name, pipeline_config, project_id
projects        → id, name, owner, shared_prompts[]
call_logs       → id, prompt_id, scene, caller, tokens, score
user_profiles   → id, preferences, usage_patterns`,
    },
  },
  {
    id: "queue",
    label: "消息队列",
    category: "infra",
    x: 440,
    y: 480,
    w: 160,
    h: 52,
    desc: "Kafka / RabbitMQ",
    detail: {
      title: "Message Queue / 消息与异步任务",
      points: [
        "异步优化任务：提示词优化、批量评估",
        "事件驱动：提示词变更 → 通知下游依赖方",
        "调用日志采集：高吞吐写入分析管道",
        "Webhook 通知：提示词更新推送到外部系统",
      ],
      example: `事件流示例：
prompt.updated(img_gen_base_v2)
  → notify: [meeting_summary_image, video_promo_thumbnail]
  → trigger: re-evaluate dependent scenes
  → log: changelog entry`,
    },
  },
  {
    id: "llm-pool",
    label: "LLM 网关",
    category: "infra",
    x: 640,
    y: 480,
    w: 180,
    h: 52,
    desc: "多模型路由 · 降级",
    detail: {
      title: "LLM Gateway / 模型网关",
      points: [
        "多模型支持：OpenAI / Claude / 本地模型统一接口",
        "智能路由：根据任务类型自动选择最优模型",
        "降级策略：主模型不可用时自动切换备用模型",
        "成本控制：Token 预算管理与告警",
      ],
      example: `routing_rules:
  - task: "prompt_optimize"
    primary: "claude-sonnet-4-20250514"
    fallback: "gpt-4o"
  - task: "prompt_lint"
    primary: "claude-haiku"  # 轻量任务用小模型
  - task: "quality_eval"
    primary: "claude-sonnet-4-20250514"
    ensemble: true  # 多模型投票评估`,
    },
  },
];

const categories = {
  access: { color: "#0ea5e9", bg: "#f0f9ff", label: "接入层" },
  core: { color: "#8b5cf6", bg: "#f5f3ff", label: "核心服务层" },
  intelligence: { color: "#f59e0b", bg: "#fffbeb", label: "智能层" },
  infra: { color: "#64748b", bg: "#f8fafc", label: "基础设施层" },
};

const connections = [
  { from: "api-gateway", to: "prompt-core", label: "" },
  { from: "api-gateway", to: "compose-engine", label: "" },
  { from: "api-gateway", to: "project-mgr", label: "" },
  { from: "prompt-core", to: "compose-engine", label: "模板解析", dashed: true },
  { from: "compose-engine", to: "project-mgr", label: "跨项目引用", dashed: true },
  { from: "prompt-core", to: "ai-optimize", label: "" },
  { from: "prompt-core", to: "analytics", label: "" },
  { from: "compose-engine", to: "analytics", label: "" },
  { from: "ai-optimize", to: "personalize", label: "", dashed: true },
  { from: "analytics", to: "personalize", label: "数据驱动", dashed: true },
  { from: "ai-optimize", to: "storage", label: "" },
  { from: "analytics", to: "queue", label: "" },
  { from: "personalize", to: "llm-pool", label: "" },
  { from: "ai-optimize", to: "llm-pool", label: "" },
  { from: "prompt-core", to: "storage", label: "" },
];

const externalSystems = [
  { label: "音频摘要系统", x: 80, y: 10 },
  { label: "AI 生图系统", x: 310, y: 10 },
  { label: "会议纪要系统", x: 530, y: 10 },
  { label: "AI 视频生成", x: 740, y: 10 },
];

function getCenter(m) {
  return { cx: m.x + m.w / 2, cy: m.y + m.h / 2 };
}

export default function PromptHubArchitecture() {
  const [selected, setSelected] = useState(null);
  const [hoveredModule, setHoveredModule] = useState(null);

  const selectedModule = modules.find((m) => m.id === selected);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#0c0c10",
        color: "#e2e8f0",
        fontFamily: "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "32px 40px 0",
          borderBottom: "1px solid #1e1e2a",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 8 }}>
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              background: "linear-gradient(135deg, #8b5cf6, #0ea5e9)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 18,
            }}
          >
            ⬡
          </div>
          <h1
            style={{
              fontSize: 22,
              fontWeight: 700,
              margin: 0,
              letterSpacing: "-0.02em",
              background: "linear-gradient(135deg, #e2e8f0, #94a3b8)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            PromptHub — 系统架构设计
          </h1>
        </div>
        <p style={{ color: "#64748b", fontSize: 13, margin: "8px 0 20px", lineHeight: 1.6 }}>
          统一提示词管理 · 跨项目编排 · AI 智能优化 · API 驱动
          <span style={{ color: "#475569", margin: "0 8px" }}>|</span>
          点击模块查看详细设计
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: selected ? "1fr 1fr" : "1fr",
          gap: 0,
          height: "calc(100vh - 110px)",
          transition: "all 0.3s ease",
        }}
      >
        {/* Architecture Diagram */}
        <div
          style={{
            padding: "24px 20px",
            overflow: "auto",
            borderRight: selected ? "1px solid #1e1e2a" : "none",
          }}
        >
          <svg viewBox="0 0 920 560" style={{ width: "100%", maxWidth: 920 }}>
            <defs>
              <marker id="arrow" viewBox="0 0 10 7" refX="10" refY="3.5" markerWidth="8" markerHeight="6" orient="auto-start-reverse">
                <polygon points="0 0, 10 3.5, 0 7" fill="#475569" />
              </marker>
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* External systems */}
            {externalSystems.map((sys, i) => (
              <g key={i}>
                <rect x={sys.x} y={sys.y} width={120} height={32} rx={6} fill="#1a1a2e" stroke="#334155" strokeWidth={1} strokeDasharray="4 3" />
                <text x={sys.x + 60} y={sys.y + 20} textAnchor="middle" fill="#94a3b8" fontSize={11} fontFamily="system-ui, sans-serif">
                  {sys.label}
                </text>
                {/* Arrow down to gateway */}
                <line x1={sys.x + 60} y1={sys.y + 32} x2={500} y2={55} stroke="#334155" strokeWidth={1} strokeDasharray="3 3" markerEnd="url(#arrow)" opacity={0.5} />
              </g>
            ))}

            {/* Layer backgrounds */}
            {[
              { y: 45, h: 70, label: "接入层", color: "#0ea5e9" },
              { y: 170, h: 90, label: "核心服务层", color: "#8b5cf6" },
              { y: 320, h: 90, label: "智能层", color: "#f59e0b" },
              { y: 460, h: 80, label: "基础设施层", color: "#64748b" },
            ].map((layer, i) => (
              <g key={i}>
                <rect x={10} y={layer.y} width={900} height={layer.h} rx={8} fill={layer.color} opacity={0.04} stroke={layer.color} strokeWidth={0.5} strokeOpacity={0.15} />
                <text x={24} y={layer.y + 16} fill={layer.color} fontSize={10} opacity={0.6} fontFamily="system-ui, sans-serif">
                  {layer.label}
                </text>
              </g>
            ))}

            {/* Connections */}
            {connections.map((conn, i) => {
              const fromM = modules.find((m) => m.id === conn.from);
              const toM = modules.find((m) => m.id === conn.to);
              const f = getCenter(fromM);
              const t = getCenter(toM);
              const isHighlighted = hoveredModule === conn.from || hoveredModule === conn.to;
              return (
                <g key={i}>
                  <line
                    x1={f.cx}
                    y1={f.cy}
                    x2={t.cx}
                    y2={t.cy}
                    stroke={isHighlighted ? "#8b5cf6" : "#334155"}
                    strokeWidth={isHighlighted ? 1.5 : 0.8}
                    strokeDasharray={conn.dashed ? "5 4" : "none"}
                    opacity={isHighlighted ? 0.9 : 0.5}
                  />
                  {conn.label && (
                    <text x={(f.cx + t.cx) / 2} y={(f.cy + t.cy) / 2 - 6} textAnchor="middle" fill="#64748b" fontSize={9} fontFamily="system-ui, sans-serif">
                      {conn.label}
                    </text>
                  )}
                </g>
              );
            })}

            {/* Modules */}
            {modules.map((m) => {
              const cat = categories[m.category];
              const isSelected = selected === m.id;
              const isHovered = hoveredModule === m.id;
              return (
                <g
                  key={m.id}
                  onClick={() => setSelected(isSelected ? null : m.id)}
                  onMouseEnter={() => setHoveredModule(m.id)}
                  onMouseLeave={() => setHoveredModule(null)}
                  style={{ cursor: "pointer" }}
                >
                  <rect
                    x={m.x}
                    y={m.y}
                    width={m.w}
                    height={m.h}
                    rx={10}
                    fill={isSelected ? cat.color + "22" : isHovered ? "#1e1e30" : "#141420"}
                    stroke={isSelected ? cat.color : isHovered ? cat.color + "88" : "#2a2a3e"}
                    strokeWidth={isSelected ? 2 : 1}
                    filter={isSelected ? "url(#glow)" : "none"}
                  />
                  <text x={m.x + m.w / 2} y={m.y + 24} textAnchor="middle" fill={isSelected || isHovered ? cat.color : "#e2e8f0"} fontSize={13} fontWeight="600" fontFamily="system-ui, sans-serif">
                    {m.label}
                  </text>
                  <text x={m.x + m.w / 2} y={m.y + 42} textAnchor="middle" fill="#64748b" fontSize={10} fontFamily="system-ui, sans-serif">
                    {m.desc}
                  </text>
                  {/* Category dot */}
                  <circle cx={m.x + 14} cy={m.y + 14} r={4} fill={cat.color} opacity={0.7} />
                </g>
              );
            })}
          </svg>
        </div>

        {/* Detail Panel */}
        {selected && selectedModule && (
          <div
            style={{
              padding: "28px 32px",
              overflow: "auto",
              background: "#0f0f16",
              animation: "slideIn 0.25s ease",
            }}
          >
            <style>{`@keyframes slideIn { from { opacity: 0; transform: translateX(16px); } to { opacity: 1; transform: translateX(0); } }`}</style>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
              <div>
                <div
                  style={{
                    display: "inline-block",
                    padding: "3px 10px",
                    borderRadius: 4,
                    background: categories[selectedModule.category].color + "18",
                    color: categories[selectedModule.category].color,
                    fontSize: 11,
                    fontWeight: 600,
                    marginBottom: 10,
                    letterSpacing: "0.04em",
                  }}
                >
                  {categories[selectedModule.category].label}
                </div>
                <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: "#f1f5f9", fontFamily: "system-ui, sans-serif" }}>
                  {selectedModule.detail.title}
                </h2>
              </div>
              <button
                onClick={() => setSelected(null)}
                style={{
                  background: "none",
                  border: "1px solid #2a2a3e",
                  color: "#64748b",
                  borderRadius: 6,
                  padding: "4px 12px",
                  cursor: "pointer",
                  fontSize: 12,
                }}
              >
                ✕ 关闭
              </button>
            </div>

            {/* Key Features */}
            <div style={{ marginBottom: 28 }}>
              <h3
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  color: "#94a3b8",
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  marginBottom: 14,
                }}
              >
                核心能力
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {selectedModule.detail.points.map((point, i) => (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      alignItems: "flex-start",
                      gap: 10,
                      padding: "10px 14px",
                      background: "#16162266",
                      borderRadius: 8,
                      borderLeft: `2px solid ${categories[selectedModule.category].color}44`,
                    }}
                  >
                    <span
                      style={{
                        color: categories[selectedModule.category].color,
                        fontSize: 12,
                        fontWeight: 700,
                        minWidth: 20,
                        opacity: 0.7,
                      }}
                    >
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span style={{ fontSize: 13, color: "#cbd5e1", lineHeight: 1.5, fontFamily: "system-ui, sans-serif" }}>{point}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Code Example */}
            <div>
              <h3
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  color: "#94a3b8",
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  marginBottom: 14,
                }}
              >
                设计示例
              </h3>
              <pre
                style={{
                  background: "#0a0a12",
                  border: "1px solid #1e1e2a",
                  borderRadius: 10,
                  padding: "18px 20px",
                  fontSize: 12,
                  lineHeight: 1.7,
                  color: "#a5b4c8",
                  overflow: "auto",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                }}
              >
                {selectedModule.detail.example}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

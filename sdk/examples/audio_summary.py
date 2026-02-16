"""PromptHub SDK — Audio Summary Integration Example

Shows how an audio transcription service migrates from hardcoded prompts
to centralized management via PromptHub.
"""

# ============================================================
# BEFORE: Prompts hardcoded in the audio service
# ============================================================
#
# SYSTEM_PROMPT = """你是一个专业的音频内容分析师。
# 请根据以下音频转录文本，生成一份结构化的内容摘要。
#
# 要求:
# - 风格: {style}
# - 语言: 中文
# - 包含关键要点、核心观点、行动项
# """
#
# def summarize(audio_text: str, style: str = "professional") -> str:
#     prompt = SYSTEM_PROMPT.format(content=audio_text, style=style)
#     return call_llm(prompt)
#
# 问题:
# - 提示词散落在代码各处，无法统一管理
# - 修改提示词需要改代码、走发版流程
# - 无法跨项目复用，每个系统各自维护一份
# - 没有版本控制，无法回滚


# ============================================================
# AFTER: Centralized prompt management via PromptHub SDK
# ============================================================

from prompthub import PromptHubClient

# Initialize once at service startup
client = PromptHubClient(
    base_url="http://localhost:8000",
    api_key="ph-audio-service-key",
    cache_ttl=300,  # cache prompts for 5 minutes
)


def summarize(audio_text: str, style: str = "professional") -> str:
    """Generate a structured summary from audio transcription text.

    The prompt is managed in PromptHub — product managers can update it
    via the Web UI without touching code.
    """
    # Option A: Direct render by slug (single prompt)
    prompt = client.prompts.get_by_slug(
        "audio-summary-zh",
        project_id="<audio-project-uuid>",
    )
    result = client.prompts.render(
        prompt.id,
        variables={"content": audio_text, "style": style},
    )
    return call_llm(result.rendered_content)


def summarize_with_scene(audio_text: str, style: str = "professional") -> str:
    """Generate summary using a scene (multi-step pipeline).

    The scene orchestration engine automatically:
    - Resolves the dependency chain
    - Renders each step with merged variables
    - Combines results using the configured merge strategy
    """
    result = client.scenes.resolve(
        "<summary-scene-uuid>",
        variables={"content": audio_text, "style": style},
        caller_system="audio-transcription-service",
    )
    return call_llm(result.final_content)


# 优势:
# - 提示词在 PromptHub 统一管理，业务系统只关心调用
# - 产品经理可直接在 Web UI 修改提示词，无需改代码
# - 版本管理 + 回滚，出问题可秒级恢复
# - 场景编排自动组合跨项目提示词
# - 调用日志 + 质量评分，数据驱动优化


def call_llm(prompt: str) -> str:
    """Placeholder — replace with your actual LLM call."""
    print(f"Calling LLM with prompt ({len(prompt)} chars)...")
    return "Summary result..."


if __name__ == "__main__":
    text = "今天的会议讨论了 Q2 产品路线图，主要包括三个方向..."
    print(summarize(text))

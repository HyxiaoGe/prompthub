"""PromptHub SDK — Meeting Notes + Image Generation Example

Demonstrates cross-project prompt orchestration: the meeting notes system
calls a scene that references prompts from both the "meeting" project and
the "image-gen" project. PromptHub's scene engine resolves the dependency
chain automatically.

Workflow:
    1. Meeting notes system records meeting content
    2. Scene "meeting-summary-image" is resolved:
       - Step 1: Summarize meeting (prompt from "meeting" project)
       - Step 2: Generate image prompt (prompt from "image-gen" project)
       - Step 3: Compose final output (combines summary + image prompt)
    3. Business system receives the assembled prompts
"""

from prompthub import PromptHubClient, SceneResolveResult

client = PromptHubClient(
    base_url="http://localhost:8000",
    api_key="ph-meeting-service-key",
)


def generate_meeting_output(
    meeting_content: str,
    attendees: list[str],
    image_style: str = "professional",
) -> SceneResolveResult:
    """Resolve the meeting-summary-image scene.

    The scene pipeline:
      step-1: meeting/summarize-zh → generates meeting summary
      step-2: image-gen/text-to-image-prompt → generates image prompt
                (receives step-1 output via chain strategy)
      step-3: meeting/compose-output → combines everything

    All prompt content is managed in PromptHub — this code only passes
    variables and receives the final assembled result.
    """
    result = client.scenes.resolve(
        "<meeting-summary-image-scene-uuid>",
        variables={
            "meeting_content": meeting_content,
            "attendees": ", ".join(attendees),
            "image_style": image_style,
            "language": "zh",
        },
        caller_system="meeting-notes-service",
    )

    print(f"Scene resolved: {result.scene_name}")
    print(f"Steps executed: {len(result.steps)}")
    for step in result.steps:
        status = "SKIPPED" if step.skipped else "OK"
        print(f"  [{status}] {step.step_id}: {step.prompt_name} (v{step.version})")

    print(f"\nFinal output ({result.total_token_estimate} tokens):")
    print(result.final_content[:200] + "...")

    return result


def check_dependencies() -> None:
    """Inspect the dependency graph for the scene."""
    graph = client.scenes.dependencies("<meeting-summary-image-scene-uuid>")
    print(f"Dependency graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    for node in graph.nodes:
        shared_tag = " [SHARED]" if node.is_shared else ""
        print(f"  {node.name} v{node.version}{shared_tag}")


if __name__ == "__main__":
    meeting_text = """
    会议主题: Q2 产品规划
    参会人: 张三, 李四, 王五
    讨论内容:
    1. 新增 AI 视频生成功能
    2. 优化现有的音频摘要准确率
    3. 会议纪要系统支持自动生成配图
    """
    generate_meeting_output(
        meeting_content=meeting_text,
        attendees=["张三", "李四", "王五"],
        image_style="watercolor",
    )

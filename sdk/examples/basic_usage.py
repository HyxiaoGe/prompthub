"""PromptHub SDK — Basic Usage Example

Demonstrates the full CRUD lifecycle: projects, prompts, versions,
rendering, scene orchestration, and shared prompt forking.

Prerequisites:
    1. Backend running: make up && make backend
    2. Seed data loaded: make seed
    3. SDK installed: cd sdk && uv sync
"""

from prompthub import PromptHubClient

API_KEY = "ph-admin-key"  # from seed data
BASE_URL = "http://localhost:8000"


def main() -> None:
    with PromptHubClient(base_url=BASE_URL, api_key=API_KEY) as client:
        # ── Projects ──────────────────────────────────────────────
        print("=== Projects ===")
        projects = client.projects.list()
        for p in projects:
            print(f"  {p.name} ({p.slug})")

        if not projects.items:
            print("  No projects found — run 'make seed' first.")
            return

        project = client.projects.get(projects.items[0].id)
        print(f"\n  Detail: {project.name}")
        print(f"    {project.prompt_count} prompts, {project.scene_count} scenes")

        # ── Prompts ───────────────────────────────────────────────
        print("\n=== Prompts ===")
        prompts = client.prompts.list(project_id=project.id)
        for p in prompts:
            print(f"  [{p.current_version}] {p.name} ({p.slug})")

        if prompts.items:
            prompt = client.prompts.get(prompts.items[0].id)
            print(f"\n  Content preview: {prompt.content[:80]}...")

            # Render with variables
            if prompt.variables:
                sample_vars = {v["name"]: f"<{v['name']}>" for v in prompt.variables}
                rendered = client.prompts.render(prompt.id, variables=sample_vars)
                print(f"  Rendered: {rendered.rendered_content[:80]}...")

            # Version history
            versions = client.prompts.list_versions(prompt.id)
            print(f"  Versions: {[v.version for v in versions]}")

        # ── Scenes ────────────────────────────────────────────────
        print("\n=== Scenes ===")
        scenes = client.scenes.list(project_id=project.id)
        for s in scenes:
            print(f"  {s.name} ({s.merge_strategy})")

        if scenes.items:
            scene = client.scenes.get(scenes.items[0].id)
            print(f"\n  Resolving scene '{scene.name}'...")
            result = client.scenes.resolve(scene.id, variables={})
            print(f"  Final content ({result.total_token_estimate} tokens):")
            print(f"    {result.final_content[:120]}...")
            print(f"  Steps: {[s.step_id for s in result.steps]}")

        # ── Shared ────────────────────────────────────────────────
        print("\n=== Shared Prompts ===")
        shared = client.shared.list_prompts()
        for p in shared:
            print(f"  {p.name} (from project {p.project_id})")

    print("\nDone!")


if __name__ == "__main__":
    main()

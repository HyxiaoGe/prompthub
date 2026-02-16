# prompthub-sdk Integration Guide

> Target audience: AI agents and developers integrating PromptHub into external projects.
> SDK version: 0.1.0 | Python >=3.10 | Dependencies: httpx, pydantic v2

---

## 1. Installation

The SDK is a local package. Install in editable mode from your project:

```bash
# From your project root (adjust relative path as needed)
pip install -e ../prompthub/sdk

# Or with uv
uv add --editable ../prompthub/sdk
```

If added to `pyproject.toml` dependencies:

```toml
[project]
dependencies = [
    "prompthub-sdk @ file:///${PROJECT_ROOT}/../prompthub/sdk",
]
```

### Required environment variables

```bash
PROMPTHUB_BASE_URL=http://localhost:8000   # PromptHub API server
PROMPTHUB_API_KEY=ph-dev-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa  # API key from seed data
PROMPTHUB_CACHE_TTL=300                    # Optional: local cache TTL in seconds
```

---

## 2. Quick Start

```python
from prompthub import PromptHubClient

client = PromptHubClient(
    base_url="http://localhost:8000",
    api_key="ph-xxx",
    cache_ttl=300,  # optional: cache GET results for 5 min
)

# Most common pattern: fetch prompt by slug
prompt = client.prompts.get_by_slug("summary-overview-meeting-zh", project_id="<uuid>")

# Render with variables
rendered = client.prompts.render(prompt.id, variables={"transcript": "..."})
print(rendered.rendered_content)

# Scene orchestration: one call, engine resolves the full dependency chain
result = client.scenes.resolve("<scene-uuid>", variables={"style": "watercolor"})
print(result.final_content)
```

### Async usage

```python
from prompthub import AsyncPromptHubClient

async with AsyncPromptHubClient(base_url="...", api_key="...") as client:
    result = await client.scenes.resolve("<scene-uuid>", variables={...})
```

---

## 3. Client Initialization

### `PromptHubClient` (sync)

```python
PromptHubClient(
    base_url: str,        # PromptHub server URL (trailing slash stripped automatically)
    api_key: str,         # Bearer token for Authorization header
    timeout: float = 30.0,  # HTTP request timeout in seconds
    cache_ttl: int | None = None,  # Optional local TTL cache (seconds). None = disabled.
)
```

- Context manager: `with PromptHubClient(...) as client:`
- Manual cleanup: `client.close()`

### `AsyncPromptHubClient` (async)

Same constructor signature. Uses `async with` and `await`.

### Resource accessors

| Accessor | Type | Description |
|----------|------|-------------|
| `client.prompts` | `PromptsResource` | Prompt CRUD, render, share, versions |
| `client.scenes` | `ScenesResource` | Scene CRUD, resolve, dependencies |
| `client.projects` | `ProjectsResource` | Project CRUD, list project prompts |
| `client.shared` | `SharedResource` | Browse shared repository, fork prompts |

---

## 4. API Reference

### 4.1 Prompts

#### `client.prompts.create(**kwargs) -> Prompt`

Create a new prompt with an initial version `1.0.0`.

```python
prompt = client.prompts.create(
    name="Summary System Role",         # required
    slug="summary-system-role-zh",      # required, kebab-case
    content="You are a {{role}}...",    # required, template content
    project_id="<uuid>",               # required
    description="System role for ...",  # optional
    format="text",                      # "text" | "json" | "yaml" | "chat", default "text"
    template_engine="jinja2",           # "jinja2" | "mustache" | "none", default "jinja2"
    variables=[{"name": "role", "type": "string", "required": True}],  # optional
    tags=["summary", "system"],         # optional
    category="summary",                 # optional
    is_shared=False,                    # default False
)
```

**Returns:** `Prompt`

---

#### `client.prompts.list(**kwargs) -> PaginatedList[PromptSummary]`

List prompts with filtering and pagination.

```python
results = client.prompts.list(
    page=1,                           # default 1
    page_size=20,                     # default 20
    project_id="<uuid>",             # optional filter
    slug="summary-overview-zh",      # optional exact slug filter
    tags=["summary"],                # optional, matches any overlap
    category="summary",              # optional exact match
    is_shared=True,                  # optional bool filter
    search="keyword",                # optional name/description ilike search
    sort_by="created_at",            # default "created_at". Options: created_at, updated_at, name, slug, current_version
    order="desc",                    # "asc" | "desc", default "desc"
)

print(results.total, results.total_pages)
for p in results:
    print(p.slug, p.current_version)
```

**Returns:** `PaginatedList[PromptSummary]`

---

#### `client.prompts.get(prompt_id) -> Prompt`

Fetch a single prompt by UUID. Cached if `cache_ttl` is set.

```python
prompt = client.prompts.get("22222222-2222-2222-2222-222222222222")
print(prompt.content, prompt.variables)
```

**Returns:** `Prompt`

---

#### `client.prompts.get_by_slug(slug, *, project_id=None) -> Prompt`

Look up a prompt by exact slug. This is the **highest-frequency business pattern** — external systems know the slug, not the UUID.

Internally calls `list(slug=..., page_size=1)` then `get(id)`.

```python
prompt = client.prompts.get_by_slug(
    "summary-overview-meeting-zh",
    project_id="<uuid>",  # optional, narrows search to one project
)
```

**Returns:** `Prompt`
**Raises:** `NotFoundError` if no prompt matches the slug.

---

#### `client.prompts.update(prompt_id, **kwargs) -> Prompt`

Update prompt fields. Only pass the fields you want to change.

```python
prompt = client.prompts.update(
    "<uuid>",
    name="New Name",
    content="Updated content...",
    tags=["updated"],
)
```

**Returns:** `Prompt`

---

#### `client.prompts.delete(prompt_id) -> None`

Soft-delete a prompt (sets `deleted_at`).

```python
client.prompts.delete("<uuid>")
```

---

#### `client.prompts.render(prompt_id, variables=None) -> RenderResult`

Render the prompt template with the given variables. The rendering happens server-side using the configured template engine (Jinja2/Mustache).

```python
result = client.prompts.render(
    "<uuid>",
    variables={"transcript": "Today we discussed...", "style": "professional"},
)
print(result.rendered_content)
print(result.version)           # which version was rendered
print(result.variables_used)    # echo of input variables
```

**Returns:** `RenderResult`

---

#### `client.prompts.share(prompt_id) -> Prompt`

Mark a prompt as shared (visible in the shared repository).

```python
prompt = client.prompts.share("<uuid>")
assert prompt.is_shared is True
```

**Returns:** `Prompt`

---

#### `client.prompts.list_versions(prompt_id) -> list[Version]`

Get the version history for a prompt.

```python
versions = client.prompts.list_versions("<uuid>")
for v in versions:
    print(v.version, v.status, v.changelog)
```

**Returns:** `list[Version]`

---

#### `client.prompts.publish(prompt_id, *, bump="patch", changelog=None, content=None) -> Version`

Publish a new version of a prompt. Bumps the version number automatically.

```python
version = client.prompts.publish(
    "<uuid>",
    bump="minor",                    # "patch" | "minor" | "major"
    changelog="Improved accuracy",   # optional
    content="New content...",        # optional, updates content in new version
)
print(version.version)  # e.g. "1.1.0"
```

**Returns:** `Version`

---

#### `client.prompts.get_version(prompt_id, version) -> Version`

Fetch a specific version.

```python
v = client.prompts.get_version("<uuid>", "1.0.0")
print(v.content)
```

**Returns:** `Version`

---

### 4.2 Scenes

#### `client.scenes.create(**kwargs) -> Scene`

Create a new scene with a pipeline configuration.

```python
scene = client.scenes.create(
    name="Meeting Summary + Image",     # required
    slug="meeting-summary-image",       # required
    project_id="<uuid>",               # required
    pipeline={                          # required
        "steps": [
            {
                "id": "summarize",
                "prompt_ref": {"prompt_id": "<uuid>", "version": "1.0.0"},
                "variables": {},
            },
            {
                "id": "gen-image",
                "prompt_ref": {"prompt_id": "<uuid>"},
                "variables": {"style": "watercolor"},
                "condition": {"variable": "need_image", "operator": "eq", "value": True},
            },
        ]
    },
    description="Summarize then generate image",  # optional
    merge_strategy="concat",           # "concat" | "chain" | "select_best", default "concat"
    separator="\n\n",                  # default "\n\n"
    output_format=None,                # optional
)
```

**Returns:** `Scene`

---

#### `client.scenes.list(**kwargs) -> PaginatedList[Scene]`

```python
scenes = client.scenes.list(
    page=1, page_size=20,
    project_id="<uuid>",    # optional
    sort_by="created_at", order="desc",
)
```

**Returns:** `PaginatedList[Scene]`

---

#### `client.scenes.get(scene_id) -> Scene`

Fetch a scene by UUID. Cached if `cache_ttl` is set.

```python
scene = client.scenes.get("<uuid>")
print(scene.pipeline, scene.merge_strategy)
```

**Returns:** `Scene`

---

#### `client.scenes.update(scene_id, **kwargs) -> Scene`

```python
scene = client.scenes.update("<uuid>", merge_strategy="chain")
```

**Returns:** `Scene`

---

#### `client.scenes.delete(scene_id) -> None`

```python
client.scenes.delete("<uuid>")
```

---

#### `client.scenes.resolve(scene_id, *, variables=None, caller_system=None) -> SceneResolveResult`

**Core feature.** Resolves the full scene pipeline: evaluates conditions, fetches prompts (with version locking), renders templates, merges outputs.

```python
result = client.scenes.resolve(
    "<uuid>",
    variables={"transcript": "...", "style": "watercolor"},
    caller_system="audio-summary-service",  # optional, logged for analytics
)

print(result.final_content)           # the assembled prompt text
print(result.total_token_estimate)    # approximate token count
for step in result.steps:
    if step.skipped:
        print(f"  SKIP {step.step_id}: {step.skip_reason}")
    else:
        print(f"  OK   {step.step_id}: {step.prompt_name} v{step.version}")
```

**Returns:** `SceneResolveResult`

---

#### `client.scenes.dependencies(scene_id) -> DependencyGraph`

Get the DAG dependency graph for a scene.

```python
graph = client.scenes.dependencies("<uuid>")
for node in graph.nodes:
    print(f"{node.name} v{node.version} shared={node.is_shared}")
for edge in graph.edges:
    print(f"{edge.source} -> {edge.target} ({edge.ref_type})")
```

**Returns:** `DependencyGraph`

---

### 4.3 Projects

#### `client.projects.create(**kwargs) -> Project`

```python
project = client.projects.create(
    name="Audio Summary",
    slug="audio-summary",
    description="Audio transcription and summarization prompts",
)
```

**Returns:** `Project`

---

#### `client.projects.list(**kwargs) -> PaginatedList[Project]`

```python
projects = client.projects.list(page=1, page_size=50)
```

**Returns:** `PaginatedList[Project]`

---

#### `client.projects.get(project_id) -> ProjectDetail`

Returns project info with `prompt_count` and `scene_count`.

```python
detail = client.projects.get("<uuid>")
print(f"{detail.name}: {detail.prompt_count} prompts, {detail.scene_count} scenes")
```

**Returns:** `ProjectDetail`

---

#### `client.projects.list_prompts(project_id, **kwargs) -> PaginatedList[PromptSummary]`

```python
prompts = client.projects.list_prompts("<uuid>", page=1, page_size=50)
```

**Returns:** `PaginatedList[PromptSummary]`

---

### 4.4 Shared

#### `client.shared.list_prompts(**kwargs) -> PaginatedList[PromptSummary]`

Browse prompts published to the shared repository.

```python
shared = client.shared.list_prompts(search="summary", page_size=10)
```

**Returns:** `PaginatedList[PromptSummary]`

---

#### `client.shared.fork(prompt_id, *, target_project_id, slug=None) -> Prompt`

Fork a shared prompt into your project.

```python
forked = client.shared.fork(
    "<shared-prompt-uuid>",
    target_project_id="<your-project-uuid>",
    slug="my-custom-slug",  # optional, auto-generated if omitted
)
```

**Returns:** `Prompt`

---

## 5. Type Reference

### Response models

| Type | Key fields |
|------|------------|
| `Prompt` | `id`, `name`, `slug`, `content`, `format`, `template_engine`, `variables`, `tags`, `category`, `project_id`, `is_shared`, `current_version`, `created_at`, `updated_at` |
| `PromptSummary` | Same as `Prompt` but without `content`, `template_engine`, `variables`, `created_by` |
| `RenderResult` | `prompt_id`, `version`, `rendered_content`, `variables_used` |
| `Version` | `id`, `prompt_id`, `version`, `content`, `variables`, `changelog`, `status`, `created_at` |
| `Project` | `id`, `name`, `slug`, `description`, `created_at`, `updated_at` |
| `ProjectDetail` | extends `Project` with `prompt_count`, `scene_count` |
| `Scene` | `id`, `name`, `slug`, `project_id`, `pipeline`, `merge_strategy`, `separator`, `output_format`, `created_at`, `updated_at` |
| `SceneResolveResult` | `scene_id`, `scene_name`, `merge_strategy`, `final_content`, `steps: list[StepResult]`, `total_token_estimate` |
| `StepResult` | `step_id`, `prompt_id`, `prompt_name`, `version`, `rendered_content`, `skipped`, `skip_reason` |
| `DependencyGraph` | `nodes: list[DependencyNode]`, `edges: list[DependencyEdge]` |

### `PaginatedList[T]`

Returned by all `list()` methods. Supports `len()` and `for item in results`.

| Field | Type | Description |
|-------|------|-------------|
| `items` | `list[T]` | Current page items |
| `page` | `int` | Current page number |
| `page_size` | `int` | Items per page |
| `total` | `int` | Total items across all pages |
| `total_pages` | `int` | Total number of pages |

---

## 6. Error Handling

All exceptions inherit from `PromptHubError`. Each maps to a backend error code.

```python
from prompthub import (
    PromptHubError,           # base — catch-all
    AuthenticationError,      # 40100 — invalid or missing API key
    PermissionDeniedError,    # 40300 — insufficient permissions
    NotFoundError,            # 40400 — resource not found
    ConflictError,            # 40900 — duplicate slug, etc.
    CircularDependencyError,  # 40901 — A -> B -> C -> A in pipeline
    ValidationError,          # 42200 — invalid request data
    TemplateRenderError,      # 42201 — Jinja2/Mustache rendering failed
)
```

### Exception attributes

```python
try:
    client.prompts.get("nonexistent-uuid")
except NotFoundError as e:
    print(e.code)     # 40400
    print(e.message)  # "Prompt not found"
    print(e.detail)   # "No prompt with id 'nonexistent-uuid'"
```

### Recommended error handling pattern

```python
from prompthub import PromptHubClient, NotFoundError, PromptHubError

def get_prompt_safely(client: PromptHubClient, slug: str) -> str | None:
    try:
        prompt = client.prompts.get_by_slug(slug, project_id="<uuid>")
        result = client.prompts.render(prompt.id, variables={"topic": "AI"})
        return result.rendered_content
    except NotFoundError:
        log.warning("Prompt '%s' not found — check PromptHub configuration", slug)
        return None
    except PromptHubError as e:
        log.error("PromptHub error [%d]: %s", e.code, e.message)
        return None
```

---

## 7. Audio System Integration

### 7.1 Current implementation (raw httpx)

The audio system (`ai-audio-assistant-web`) currently uses a hand-rolled `PromptManager` class (`app/prompts/manager.py`, 432 lines) that:

1. **Manually manages an httpx.Client** with lazy init and Bearer auth headers
2. **Builds a slug-to-UUID index** by paginating through `GET /api/v1/prompts` and caching slug->id mappings
3. **Implements its own TTL cache** (`dict[str, tuple[float, str]]`) for prompt content
4. **Renders Jinja2 templates locally** after fetching raw content from PromptHub
5. **Constructs slugs from parameters** (`_build_prompt_slug(category, prompt_type, locale, content_style)`)

Key pain points in the current 432-line implementation:
- Duplicates caching logic that the SDK already provides
- Duplicates template rendering that the backend `/render` endpoint already does
- The two-phase fetch (index + individual) adds complexity and double the HTTP calls
- No typed responses — works with raw `dict` from `resp.json()`
- Manual error handling with generic `except Exception`

### 7.2 Replacement with SDK

#### Environment configuration

Keep the existing settings in `app/config.py` (no change needed):

```python
# app/config.py — already exists, no modification required
PROMPTHUB_BASE_URL: Optional[str] = Field(default=None)
PROMPTHUB_API_KEY: Optional[str] = Field(default=None)
PROMPTHUB_CACHE_TTL: int = Field(default=300)
```

`.env`:
```bash
PROMPTHUB_BASE_URL=http://localhost:8000
PROMPTHUB_API_KEY=ph-dev-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
PROMPTHUB_CACHE_TTL=300
```

#### Rewritten PromptManager

Replace the 432-line `app/prompts/manager.py` with:

```python
"""Prompt manager — backed by PromptHub SDK."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from prompthub import PromptHubClient, NotFoundError, PromptHubError

from app.core.exceptions import BusinessError
from app.i18n.codes import ErrorCode

log = logging.getLogger(__name__)


class PromptManager:
    _instance: Optional[PromptManager] = None

    def __new__(cls) -> PromptManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self.prompts_dir = Path(__file__).parent / "templates"
        self._config_cache: Dict[str, Dict] = {}

        from app.config import settings

        hub_url = getattr(settings, "PROMPTHUB_BASE_URL", None)
        hub_key = getattr(settings, "PROMPTHUB_API_KEY", None)
        hub_ttl = getattr(settings, "PROMPTHUB_CACHE_TTL", 300)

        if not hub_url or not hub_key:
            self._client: PromptHubClient | None = None
            log.warning("PromptHub not configured")
            return

        # One line replaces 40+ lines of httpx.Client setup, header injection,
        # index building, and cache management
        self._client = PromptHubClient(
            base_url=hub_url,
            api_key=hub_key,
            cache_ttl=hub_ttl,
        )
        log.info("PromptHub SDK initialized: %s (TTL=%ds)", hub_url, hub_ttl)

    def get_prompt(
        self,
        category: str,
        prompt_type: str,
        locale: str = "zh-CN",
        variables: Optional[Dict[str, Any]] = None,
        content_style: Optional[str] = None,
    ) -> Dict[str, Any]:
        if self._client is None:
            raise BusinessError(ErrorCode.SYSTEM_ERROR, reason="PromptHub not configured")

        if content_style is None:
            content_style = (variables or {}).get("content_style", "meeting")

        slug = self._build_prompt_slug(category, prompt_type, locale, content_style)

        try:
            # SDK handles: slug lookup, HTTP call, caching, response parsing
            prompt = self._client.prompts.get_by_slug(slug)

            # Merge shared vars + caller vars, then render server-side
            shared_vars = self._resolve_shared_vars(locale)
            all_vars = {**shared_vars, **(variables or {})}

            # Server-side render replaces local Jinja2 rendering
            rendered = self._client.prompts.render(prompt.id, variables=all_vars)
            user_prompt = rendered.rendered_content

        except NotFoundError:
            raise BusinessError(
                ErrorCode.SYSTEM_ERROR,
                reason=f"Prompt not found in PromptHub: {slug}",
            )
        except PromptHubError as e:
            raise BusinessError(
                ErrorCode.SYSTEM_ERROR,
                reason=f"PromptHub error [{e.code}]: {e.message}",
            )

        # System message
        system_message = self._get_system_from_hub(category, locale, content_style)

        # model_params still from local config.json (not managed in PromptHub)
        config_data = self._load_config(category)
        if "prompt_types" in config_data and prompt_type in config_data["prompt_types"]:
            model_params = config_data["prompt_types"][prompt_type].get("model_params", {})
        else:
            model_params = config_data.get("model_params", {}).get(prompt_type, {})

        return {
            "system": system_message or "",
            "user_prompt": user_prompt,
            "model_params": model_params,
            "metadata": {
                "category": category,
                "type": prompt_type,
                "locale": locale,
                "content_style": content_style,
                "version": config_data.get("version", "unknown"),
                "source": "prompthub-sdk",
            },
        }

    def get_image_prompt(
        self,
        content_style: str,
        image_type: str,
        description: str,
        key_texts: list[str],
        locale: str = "zh-CN",
    ) -> str:
        if self._client is None:
            raise BusinessError(ErrorCode.SYSTEM_ERROR, reason="PromptHub not configured")

        config = self._load_config("images")
        lang = "zh" if locale.startswith("zh") else "en"
        style_config = config.get("content_style_mapping", {}).get(
            content_style, config["content_style_mapping"]["general"]
        )

        template_vars = self._build_image_template_vars(
            config, style_config, lang, image_type, content_style, description, key_texts
        )

        loc_short = locale.split("-")[0]
        slug = f"images-baseprompt-{loc_short}"

        try:
            prompt = self._client.prompts.get_by_slug(slug)
            rendered = self._client.prompts.render(prompt.id, variables=template_vars)
            return rendered.rendered_content
        except PromptHubError as e:
            raise BusinessError(
                ErrorCode.SYSTEM_ERROR,
                reason=f"Failed to fetch image prompt: {e.message}",
            )

    def clear_cache(self) -> None:
        self._config_cache.clear()
        # SDK cache is managed internally by the TTLCache

    # --- Private helpers (unchanged from current implementation) ---

    def _build_prompt_slug(
        self, category: str, prompt_type: str, locale: str, content_style: str,
    ) -> str:
        loc_short = locale.split("-")[0]
        type_slug = prompt_type.replace("_", "")
        if prompt_type == "action_items":
            return f"{category}-{type_slug}-{loc_short}"
        return f"{category}-{type_slug}-{content_style}-{loc_short}"

    def _resolve_shared_vars(self, locale: str) -> Dict[str, str]:
        if self._client is None:
            return {}
        loc_short = locale.split("-")[0]
        shared: Dict[str, str] = {}
        try:
            fmt = self._client.prompts.get_by_slug(f"shared-format-rules-{loc_short}")
            shared["format_rules"] = fmt.content
        except NotFoundError:
            pass
        try:
            img = self._client.prompts.get_by_slug(f"shared-image-req-{loc_short}")
            shared["image_requirements"] = img.content
        except NotFoundError:
            pass
        return shared

    def _get_system_from_hub(
        self, category: str, locale: str, content_style: str,
    ) -> Optional[str]:
        if self._client is None:
            return None
        loc_short = locale.split("-")[0]
        try:
            prompt = self._client.prompts.get_by_slug(f"shared-system-role-{loc_short}")
            rendered = self._client.prompts.render(
                prompt.id, variables={"content_style": content_style},
            )
            return rendered.rendered_content
        except PromptHubError:
            return None

    def _build_image_template_vars(
        self, config: dict, style_config: dict, lang: str,
        image_type: str, content_style: str, description: str, key_texts: list[str],
    ) -> dict:
        visual_style_key = style_config.get("visual_style", "flat_vector")
        visual_styles = config.get("visual_styles", {})
        lang_key = f"prompt_{lang}"
        visual_style_prompt = visual_styles.get(visual_style_key, {}).get(
            lang_key, visual_styles.get("flat_vector", {}).get(lang_key, "")
        )
        layout_key = style_config.get("layout", "flexible")
        layout_templates = config.get("layout_templates", {}).get(lang, {})
        layout_instructions = layout_templates.get(layout_key, layout_templates.get("flexible", ""))
        colors = style_config.get("color_scheme", {})
        image_type_name = config.get("image_type_names", {}).get(lang, {}).get(image_type, image_type)
        content_style_name = config.get("content_style_names", {}).get(lang, {}).get(content_style, content_style)
        if key_texts:
            key_texts_formatted = "\n".join([f"- {text}" for text in key_texts])
        elif lang == "zh":
            key_texts_formatted = "- (根据主题自动生成合适的标签)"
        else:
            key_texts_formatted = "- (Auto-generate appropriate labels based on topic)"
        return {
            "image_type": image_type_name,
            "content_style_name": content_style_name,
            "visual_style_prompt": visual_style_prompt,
            "primary_color": colors.get("primary", "#3B82F6"),
            "secondary_color": colors.get("secondary", "#10B981"),
            "background_color": colors.get("background", "#FFFFFF"),
            "description": description,
            "key_texts_formatted": key_texts_formatted,
            "layout_instructions": layout_instructions,
        }

    def _load_config(self, category: str) -> Dict:
        cache_key = f"{category}:config"
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
        config_file = self.prompts_dir / category / "config.json"
        if not config_file.exists():
            return {"version": "1.0.0", "model_params": {}}
        with open(config_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._config_cache[cache_key] = data
        return data

    def get_visual_config(self, visual_type: str) -> Dict[str, Any]:
        config = self._load_config("visual")
        return config.get("prompt_types", {}).get(visual_type, {})

    def get_image_config(self, content_style: str) -> Dict[str, Any]:
        config = self._load_config("images")
        mapping = config.get("content_style_mapping", {})
        return mapping.get(content_style, mapping.get("general", {}))


_prompt_manager = PromptManager()


def get_prompt_manager() -> PromptManager:
    return _prompt_manager
```

### 7.3 What changed — line-by-line diff summary

| Before (raw httpx) | After (SDK) | Lines saved |
|---------------------|-------------|-------------|
| `_get_http_client()` — lazy httpx.Client init, manual headers | `PromptHubClient(...)` constructor | ~15 lines |
| `_ensure_hub_index()` — paginate list endpoint, build slug->id dict | `get_by_slug(slug)` — SDK does this internally | ~30 lines |
| `_fetch_hub_prompt()` — TTL cache check, index lookup, GET by id, cache store | `get_by_slug()` + SDK's built-in `cache_ttl` | ~35 lines |
| `_render_jinja2()` + `_simple_render()` — local Jinja2 with fallback | `client.prompts.render()` — server-side rendering | ~20 lines |
| Manual `resp.json()` parsing, `data.get("data", {})` unwrapping | SDK returns typed `Prompt`, `RenderResult` objects | scattered |
| Generic `except Exception` | Typed `except NotFoundError`, `except PromptHubError` | clearer intent |
| **Total: 432 lines** | **~210 lines** | **~220 lines (51% reduction)** |

### 7.4 Key behavioral differences

1. **No more index preloading.** The SDK's `get_by_slug()` calls `list(slug=..., page_size=1)` which uses the backend's new exact `slug` filter — one precise query instead of paginating all prompts.

2. **Server-side rendering.** The `/render` endpoint handles Jinja2 rendering on the backend, so the audio system no longer needs `jinja2` as a dependency for prompt rendering.

3. **Typed errors.** Instead of catching `Exception` and logging a warning, you catch `NotFoundError` specifically and can distinguish between "prompt doesn't exist" vs "auth failed" vs "template error".

4. **Automatic cache invalidation.** The SDK's TTL cache auto-invalidates on write operations (`update`, `delete`, `publish`). The current implementation has no invalidation — stale data persists until TTL expires.

---

## 8. Caching Behavior

When `cache_ttl` is set, `get()` results for prompts and scenes are cached locally:

- **Cache key format:** `"prompts:{id}"`, `"scenes:{id}"`
- **Write operations** (`create`, `update`, `delete`, `publish`, `share`) automatically invalidate related cache entries
- **`list()` results are NOT cached** — they always hit the server
- **`get_by_slug()` internally calls `list()` then `get()`** — the `get()` result is cached

To disable caching, omit `cache_ttl` (default `None`).

---

## 9. Async Integration

For FastAPI or other async frameworks, use `AsyncPromptHubClient`:

```python
from contextlib import asynccontextmanager
from prompthub import AsyncPromptHubClient

_client: AsyncPromptHubClient | None = None

@asynccontextmanager
async def lifespan(app):
    global _client
    _client = AsyncPromptHubClient(
        base_url=settings.PROMPTHUB_BASE_URL,
        api_key=settings.PROMPTHUB_API_KEY,
        cache_ttl=settings.PROMPTHUB_CACHE_TTL,
    )
    yield
    await _client.close()

async def get_summary_prompt(transcript: str) -> str:
    prompt = await _client.prompts.get_by_slug("summary-overview-meeting-zh")
    result = await _client.prompts.render(prompt.id, variables={"transcript": transcript})
    return result.rendered_content
```

All methods on `AsyncPromptHubClient` resources are `async` — same signatures as sync, just add `await`.

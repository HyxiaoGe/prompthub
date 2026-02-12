import time
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, PermissionError
from app.models.call_log import CallLog
from app.models.prompt import Prompt
from app.models.version import PromptVersion
from app.schemas.scene import (
    PipelineConfig,
    SceneResolveRequest,
    SceneResolveResponse,
    StepCondition,
    StepResult,
)
from app.services import template_engine
from app.services.scene_service import get_scene


def evaluate_condition(condition: StepCondition, variables: dict[str, Any]) -> bool:
    """Evaluate a step condition against provided variables."""
    val = variables.get(condition.variable)
    match condition.operator.value:
        case "eq":
            return val == condition.value
        case "neq":
            return val != condition.value
        case "in":
            if not isinstance(condition.value, list):
                return False
            return val in condition.value
        case "not_in":
            if not isinstance(condition.value, list):
                return True
            return val not in condition.value
        case "exists":
            return val is not None
        case _:
            return False


def merge_variables(
    variable_definitions: list[dict],
    input_variables: dict[str, Any],
    step_overrides: dict[str, Any],
) -> dict[str, Any]:
    """
    Merge variables with three-tier priority:
    1. prompt defaults (lowest)
    2. input_variables + chain_context (middle)
    3. step_overrides (highest)
    """
    result: dict[str, Any] = {}
    for defn in variable_definitions:
        name = defn.get("name", "")
        if defn.get("default") is not None:
            result[name] = defn["default"]
    result.update(input_variables)
    result.update(step_overrides)
    return result


async def fetch_prompt_content(
    db: AsyncSession,
    prompt_id: uuid.UUID,
    version: str | None,
    scene_project_id: uuid.UUID,
) -> tuple[Prompt, str, str]:
    """
    Fetch prompt content, respecting version lock and cross-project sharing.
    Returns (prompt, content, version_str).
    """
    result = await db.execute(
        select(Prompt).where(Prompt.id == prompt_id, Prompt.deleted_at.is_(None))
    )
    prompt = result.scalar_one_or_none()
    if prompt is None:
        raise NotFoundError(
            message="Prompt not found",
            detail=f"No prompt with id '{prompt_id}'",
        )

    # Cross-project access check
    if prompt.project_id != scene_project_id and not prompt.is_shared:
        raise PermissionError(
            message="Cross-project reference denied",
            detail=f"Prompt '{prompt.name}' is not shared and belongs to another project",
        )

    if version is not None:
        # Version-locked: fetch from prompt_versions table
        ver_result = await db.execute(
            select(PromptVersion).where(
                PromptVersion.prompt_id == prompt_id,
                PromptVersion.version == version,
            )
        )
        ver = ver_result.scalar_one_or_none()
        if ver is None:
            raise NotFoundError(
                message="Version not found",
                detail=f"No version '{version}' for prompt '{prompt.name}'",
            )
        return prompt, ver.content, version
    else:
        # Latest: fetch content from prompt_versions for current_version
        ver_result = await db.execute(
            select(PromptVersion).where(
                PromptVersion.prompt_id == prompt_id,
                PromptVersion.version == prompt.current_version,
            )
        )
        ver = ver_result.scalar_one_or_none()
        content = ver.content if ver is not None else prompt.content
        return prompt, content, prompt.current_version


async def resolve_scene(
    db: AsyncSession,
    scene_id: uuid.UUID,
    request: SceneResolveRequest,
    caller_ip: str | None = None,
) -> SceneResolveResponse:
    """Main scene resolve orchestrator."""
    start_time = time.monotonic()

    scene = await get_scene(db, scene_id)
    pipeline = PipelineConfig.model_validate(scene.pipeline)

    # Cycle detection is performed at scene create/update time (scene_service.py).
    # No need to re-check on every resolve call.

    chain_context: dict[str, Any] = {}
    step_results: list[StepResult] = []

    for step in pipeline.steps:
        # Build evaluation variables for condition check
        eval_vars = {**request.variables, **chain_context, **step.variables}

        # Condition evaluation
        if step.condition is not None and not evaluate_condition(step.condition, eval_vars):
            step_results.append(
                StepResult(
                    step_id=step.id,
                    prompt_id=step.prompt_ref.prompt_id,
                    prompt_name="",
                    version="",
                    rendered_content="",
                    skipped=True,
                    skip_reason="Condition not met",
                )
            )
            continue

        # Fetch prompt content
        prompt, content, version_str = await fetch_prompt_content(
            db,
            step.prompt_ref.prompt_id,
            step.prompt_ref.version,
            scene.project_id,
        )

        # Variable merge priority (three tiers):
        #   1. prompt variable defaults (lowest)
        #   2. request.variables + chain_context (middle) — chain_context intentionally
        #      overrides request.variables so pipeline outputs flow through to downstream steps
        #   3. step.variables (highest, scene-level overrides)
        var_defs = prompt.variables or []
        merged = merge_variables(
            var_defs,
            {**request.variables, **chain_context},
            step.variables,
        )

        # Render template
        rendered = template_engine.render_prompt(content, var_defs, merged)

        # Chain strategy: pass output to next step
        if scene.merge_strategy == "chain":
            key = step.output_key or step.id
            chain_context[key] = rendered

        step_results.append(
            StepResult(
                step_id=step.id,
                prompt_id=prompt.id,
                prompt_name=prompt.name,
                version=version_str,
                rendered_content=rendered,
                skipped=False,
            )
        )

    # Merge strategy
    non_skipped = [sr for sr in step_results if not sr.skipped]
    if scene.merge_strategy == "concat":
        final_content = scene.separator.join(sr.rendered_content for sr in non_skipped)
    elif scene.merge_strategy == "chain":
        final_content = non_skipped[-1].rendered_content if non_skipped else ""
    elif scene.merge_strategy == "select_best":
        # Phase 5: LLM evaluation. For now, use first non-skipped.
        final_content = non_skipped[0].rendered_content if non_skipped else ""
    else:
        final_content = scene.separator.join(sr.rendered_content for sr in non_skipped)

    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    # Record call log
    call_log = CallLog(
        scene_id=scene.id,
        caller_system=request.caller_system,
        caller_ip=caller_ip,
        input_variables=request.variables,
        rendered_content=final_content,
        token_count=len(final_content) // 4,
        response_time_ms=elapsed_ms,
    )
    db.add(call_log)
    await db.flush()

    return SceneResolveResponse(
        scene_id=scene.id,
        scene_name=scene.name,
        merge_strategy=scene.merge_strategy,
        final_content=final_content,
        steps=step_results,
        total_token_estimate=len(final_content) // 4,
    )

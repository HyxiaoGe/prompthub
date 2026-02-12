import uuid
from collections import defaultdict, deque

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CircularDependencyError, NotFoundError
from app.models.prompt import Prompt
from app.models.prompt_ref import PromptRef
from app.models.scene import Scene
from app.schemas.scene import (
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    PipelineConfig,
)


def topological_sort_with_cycle_detection(
    graph: dict[uuid.UUID, set[uuid.UUID]],
) -> list[uuid.UUID]:
    """
    Kahn's algorithm for topological sort with cycle detection.
    graph: {node: set(nodes it depends on)}
    Returns topological order (dependencies first).
    """
    if not graph:
        return []

    # Build adjacency list and in-degree map
    all_nodes: set[uuid.UUID] = set()
    # adjacency: from -> [to] means "from" is depended on by "to"
    adjacency: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
    in_degree: dict[uuid.UUID, int] = defaultdict(int)

    for node, deps in graph.items():
        all_nodes.add(node)
        all_nodes.update(deps)

    for node in all_nodes:
        if node not in in_degree:
            in_degree[node] = 0

    for node, deps in graph.items():
        for dep in deps:
            adjacency[dep].append(node)
            in_degree[node] += 1

    # BFS with queue of nodes with in-degree 0
    queue: deque[uuid.UUID] = deque()
    for node in all_nodes:
        if in_degree[node] == 0:
            queue.append(node)

    result: list[uuid.UUID] = []
    while queue:
        current = queue.popleft()
        result.append(current)
        for neighbor in adjacency[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(result) < len(all_nodes):
        cycle_nodes = all_nodes - set(result)
        raise CircularDependencyError(
            detail=f"Cycle detected among nodes: {[str(n) for n in cycle_nodes]}",
        )

    return result


async def build_prompt_ref_graph(
    db: AsyncSession,
    prompt_ids: set[uuid.UUID],
) -> dict[uuid.UUID, set[uuid.UUID]]:
    """Build adjacency table {source -> {targets}} from prompt_refs table."""
    graph: dict[uuid.UUID, set[uuid.UUID]] = {pid: set() for pid in prompt_ids}

    if not prompt_ids:
        return graph

    result = await db.execute(
        select(PromptRef).where(
            PromptRef.source_prompt_id.in_(prompt_ids)
            | PromptRef.target_prompt_id.in_(prompt_ids)
        )
    )
    refs = result.scalars().all()

    for ref in refs:
        if ref.source_prompt_id not in graph:
            graph[ref.source_prompt_id] = set()
        if ref.target_prompt_id not in graph:
            graph[ref.target_prompt_id] = set()
        # source depends on target
        graph[ref.source_prompt_id].add(ref.target_prompt_id)

    return graph


async def build_scene_dependency_graph(
    db: AsyncSession,
    scene: Scene,
) -> tuple[dict[uuid.UUID, set[uuid.UUID]], dict[uuid.UUID, Prompt]]:
    """
    Build complete dependency graph for a scene.
    Returns (graph, prompt_lookup).
    """
    pipeline = PipelineConfig.model_validate(scene.pipeline)
    prompt_ids = {step.prompt_ref.prompt_id for step in pipeline.steps}

    # Load all prompts
    result = await db.execute(
        select(Prompt).where(Prompt.id.in_(prompt_ids), Prompt.deleted_at.is_(None))
    )
    prompts = {p.id: p for p in result.scalars().all()}

    # Build ref graph including transitive deps
    graph = await build_prompt_ref_graph(db, prompt_ids)

    return graph, prompts


async def build_full_ref_graph(
    db: AsyncSession,
    seed_ids: set[uuid.UUID],
) -> dict[uuid.UUID, set[uuid.UUID]]:
    """Iteratively expand to discover the full reachable subgraph."""
    visited: set[uuid.UUID] = set()
    to_visit = set(seed_ids)
    graph: dict[uuid.UUID, set[uuid.UUID]] = {pid: set() for pid in seed_ids}

    while to_visit - visited:
        batch = to_visit - visited
        visited.update(batch)
        result = await db.execute(
            select(PromptRef).where(
                PromptRef.source_prompt_id.in_(batch)
                | PromptRef.target_prompt_id.in_(batch)
            )
        )
        for ref in result.scalars().all():
            if ref.source_prompt_id not in graph:
                graph[ref.source_prompt_id] = set()
            if ref.target_prompt_id not in graph:
                graph[ref.target_prompt_id] = set()
            graph[ref.source_prompt_id].add(ref.target_prompt_id)
            to_visit.add(ref.source_prompt_id)
            to_visit.add(ref.target_prompt_id)

    return graph


async def check_no_cycles(
    db: AsyncSession,
    source_prompt_id: uuid.UUID,
    target_prompt_id: uuid.UUID,
) -> None:
    """Check that adding source -> target ref won't create a cycle."""
    # Build full reachable graph (not just direct neighbours)
    graph = await build_full_ref_graph(db, {source_prompt_id, target_prompt_id})

    # Add proposed edge
    if source_prompt_id not in graph:
        graph[source_prompt_id] = set()
    graph[source_prompt_id].add(target_prompt_id)

    topological_sort_with_cycle_detection(graph)


async def get_scene_dependency_graph(
    db: AsyncSession,
    scene_id: uuid.UUID,
) -> DependencyGraph:
    """Build dependency graph for frontend React Flow visualization."""
    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    scene = result.scalar_one_or_none()
    if scene is None:
        raise NotFoundError(message="Scene not found", detail=f"No scene with id '{scene_id}'")

    pipeline = PipelineConfig.model_validate(scene.pipeline)
    prompt_ids = {step.prompt_ref.prompt_id for step in pipeline.steps}

    # Load prompts
    prompt_result = await db.execute(
        select(Prompt).where(Prompt.id.in_(prompt_ids), Prompt.deleted_at.is_(None))
    )
    prompts = {p.id: p for p in prompt_result.scalars().all()}

    # Build nodes
    nodes = [
        DependencyNode(
            id=p.id,
            name=p.name,
            project_id=p.project_id,
            version=p.current_version,
            is_shared=p.is_shared,
        )
        for p in prompts.values()
    ]

    # Build edges from pipeline steps
    edges: list[DependencyEdge] = []
    for step in pipeline.steps:
        if step.prompt_ref.prompt_id in prompts:
            edges.append(
                DependencyEdge(
                    source=scene_id,
                    target=step.prompt_ref.prompt_id,
                    step_id=step.id,
                    ref_type="composes",
                )
            )

    # Add edges from prompt_refs
    ref_result = await db.execute(
        select(PromptRef).where(
            PromptRef.source_prompt_id.in_(prompt_ids)
            | PromptRef.target_prompt_id.in_(prompt_ids)
        )
    )
    for ref in ref_result.scalars().all():
        edges.append(
            DependencyEdge(
                source=ref.source_prompt_id,
                target=ref.target_prompt_id,
                ref_type=ref.ref_type,
            )
        )

    return DependencyGraph(nodes=nodes, edges=edges)

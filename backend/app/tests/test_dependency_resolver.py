import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CircularDependencyError
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.prompt_ref import PromptRef
from app.services.dependency_resolver import check_no_cycles, topological_sort_with_cycle_detection


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class TestTopologicalSort:
    def test_linear_chain(self) -> None:
        a, b, c = _uuid(), _uuid(), _uuid()
        # a depends on b, b depends on c
        graph = {a: {b}, b: {c}, c: set()}
        result = topological_sort_with_cycle_detection(graph)
        assert result.index(c) < result.index(b) < result.index(a)

    def test_diamond_dependency(self) -> None:
        a, b, c, d = _uuid(), _uuid(), _uuid(), _uuid()
        # a -> b, a -> c, b -> d, c -> d
        graph = {a: {b, c}, b: {d}, c: {d}, d: set()}
        result = topological_sort_with_cycle_detection(graph)
        assert result.index(d) < result.index(b)
        assert result.index(d) < result.index(c)
        assert result.index(b) < result.index(a)
        assert result.index(c) < result.index(a)

    def test_cycle_raises(self) -> None:
        a, b, c = _uuid(), _uuid(), _uuid()
        # a -> b -> c -> a
        graph = {a: {b}, b: {c}, c: {a}}
        with pytest.raises(CircularDependencyError, match="Circular dependency detected"):
            topological_sort_with_cycle_detection(graph)

    def test_self_reference_raises(self) -> None:
        a = _uuid()
        graph = {a: {a}}
        with pytest.raises(CircularDependencyError, match="Circular dependency detected"):
            topological_sort_with_cycle_detection(graph)

    def test_independent_nodes(self) -> None:
        a, b, c = _uuid(), _uuid(), _uuid()
        graph = {a: set(), b: set(), c: set()}
        result = topological_sort_with_cycle_detection(graph)
        assert set(result) == {a, b, c}

    def test_empty_graph(self) -> None:
        result = topological_sort_with_cycle_detection({})
        assert result == []


async def test_check_no_cycles_detects_indirect_cycle(db_session: AsyncSession) -> None:
    """build_full_ref_graph must discover the full A→B→C→D chain so adding D→A raises."""
    # Create a project
    project = Project(
        name="Cycle Project",
        slug=f"cycle-proj-{uuid.uuid4().hex[:8]}",
    )
    db_session.add(project)
    await db_session.flush()

    # Create 4 prompts: A, B, C, D
    prompts = []
    for label in ("A", "B", "C", "D"):
        p = Prompt(
            name=f"Prompt {label}",
            slug=f"p-{label.lower()}-{uuid.uuid4().hex[:6]}",
            content=f"content {label}",
            project_id=project.id,
        )
        db_session.add(p)
        prompts.append(p)
    await db_session.flush()

    a, b, c, d = prompts

    # Create refs: A→B, B→C, C→D
    for src, tgt in [(a, b), (b, c), (c, d)]:
        ref = PromptRef(
            source_prompt_id=src.id,
            target_prompt_id=tgt.id,
            ref_type="includes",
        )
        db_session.add(ref)
    await db_session.flush()

    # Adding D→A must detect cycle
    with pytest.raises(CircularDependencyError, match="Circular dependency detected"):
        await check_no_cycles(db_session, d.id, a.id)

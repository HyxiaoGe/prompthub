"""Generic paginated list wrapper."""

from __future__ import annotations

import math
from collections.abc import Iterator
from typing import Generic, TypeVar

T = TypeVar("T")


class PaginatedList(Generic[T]):
    """Wraps a page of results with pagination metadata."""

    __slots__ = ("items", "page", "page_size", "total", "total_pages")

    def __init__(
        self,
        items: list[T],
        page: int,
        page_size: int,
        total: int,
    ) -> None:
        self.items = items
        self.page = page
        self.page_size = page_size
        self.total = total
        self.total_pages = max(1, math.ceil(total / page_size)) if page_size > 0 else 1

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __repr__(self) -> str:
        return (
            f"PaginatedList(page={self.page}, page_size={self.page_size}, "
            f"total={self.total}, items_count={len(self.items)})"
        )

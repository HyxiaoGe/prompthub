from dataclasses import dataclass
from typing import Literal

from fastapi import Query


@dataclass
class PaginationParams:
    page: int
    page_size: int
    sort_by: str
    order: Literal["asc", "desc"]

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def get_pagination(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    order: Literal["asc", "desc"] = Query("desc", description="Sort order"),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size, sort_by=sort_by, order=order)

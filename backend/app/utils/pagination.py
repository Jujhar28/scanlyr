from dataclasses import dataclass

from fastapi import Query


@dataclass(frozen=True, slots=True)
class PageParams:
    """Reusable limit/offset for list endpoints."""

    skip: int
    limit: int


def pagination_params(
    skip: int = Query(default=0, ge=0, description="Number of rows to skip"),
    limit: int = Query(default=50, ge=1, le=200, description="Max rows to return"),
) -> PageParams:
    return PageParams(skip=skip, limit=limit)

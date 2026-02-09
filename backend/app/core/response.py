from typing import Any


def success_response(data: Any = None, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    response: dict[str, Any] = {
        "code": 0,
        "message": "success",
        "data": data,
    }
    if meta is not None:
        response["meta"] = meta
    return response


def error_response(code: int, message: str, detail: str | None = None) -> dict[str, Any]:
    response: dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if detail is not None:
        response["detail"] = detail
    return response


def pagination_meta(page: int, page_size: int, total: int) -> dict[str, Any]:
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
    }

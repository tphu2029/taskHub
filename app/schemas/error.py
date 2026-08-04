from typing import Any

from pydantic import BaseModel


class HTTPErrorResponse(BaseModel):
    detail: str | list[dict[str, Any]]


COMMON_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": HTTPErrorResponse, "description": "Bad Request"},
    401: {"model": HTTPErrorResponse, "description": "Unauthorized"},
    403: {"model": HTTPErrorResponse, "description": "Forbidden"},
    404: {"model": HTTPErrorResponse, "description": "Not Found"},
    422: {"model": HTTPErrorResponse, "description": "Validation Error"},
}

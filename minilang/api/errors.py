"""One error format for every failure: {"error": {"code", "message", "details"}}.

Unexpected exceptions are not handled here: an ``Exception`` handler runs in Starlette's
outermost ServerErrorMiddleware, outside CORS and our request middleware, so its 500
would have no CORS headers, request ID or log line. ``RequestContextMiddleware`` turns
them into the 500 instead.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

HTTP_CODES = {404: "not_found", 405: "method_not_allowed"}


class ApiError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        details: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers


def error_response(
    status: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {"code": code, "message": message}
    if details:
        body["details"] = details
    return JSONResponse({"error": body}, status_code=status, headers=headers)


def field_path(location: tuple[Any, ...]) -> str | None:
    # ("body", "source") -> "source"; a missing or malformed body has no field.
    parts = [str(part) for part in location if part != "body"]
    return ".".join(parts) or None


async def on_api_error(_: Request, exc: ApiError) -> JSONResponse:
    return error_response(exc.status, exc.code, exc.message, exc.details, exc.headers)


async def on_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = [{"field": field_path(e["loc"]), "message": e["msg"]} for e in exc.errors()]
    return error_response(422, "invalid_request", "The request body is invalid.", details)


async def on_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = HTTP_CODES.get(exc.status_code, "http_error")
    return error_response(exc.status_code, code, str(exc.detail), headers=exc.headers)


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, on_api_error)
    app.add_exception_handler(RequestValidationError, on_validation_error)
    app.add_exception_handler(StarletteHTTPException, on_http_error)

"""The endpoints. Each one validates, takes a program slot and calls the service layer.

Rate limiting and the body-size limit happen earlier, in ASGI middleware (``guards.py``),
so a refused request never gets this far.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from minilang import __version__, service
from minilang.api.config import Settings
from minilang.api.errors import ApiError
from minilang.api.schemas import (
    CheckResponse,
    CompileResponse,
    ErrorResponse,
    HealthResponse,
    ProgramRequest,
    RunResponse,
)

router = APIRouter()

ERRORS: dict[int | str, dict[str, Any]] = {
    413: {"model": ErrorResponse, "description": "Request body too large"},
    422: {"model": ErrorResponse, "description": "Invalid request body"},
    429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    500: {"model": ErrorResponse, "description": "Unexpected server error"},
    503: {"model": ErrorResponse, "description": "Too many programs running; see Retry-After"},
}
BUSY_RETRY_SECONDS = 1


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_program_slots(request: Request) -> threading.BoundedSemaphore:
    return request.app.state.program_slots


def program_source(
    body: ProgramRequest, settings: Annotated[Settings, Depends(get_settings)]
) -> str:
    """The validated source. The schema allows the default maximum; a setting may be lower."""
    if len(body.source) > settings.max_source_chars:
        raise ApiError(
            422,
            "invalid_request",
            "The request body is invalid.",
            details=[
                {
                    "field": "source",
                    "message": f"must be at most {settings.max_source_chars} characters "
                    f"(got {len(body.source)})",
                }
            ],
        )
    return body.source


@contextmanager
def program_slot(slots: threading.BoundedSemaphore) -> Iterator[None]:
    """Hold one of the few compile/run slots, or refuse with 503 right away.

    Compiling is CPU-bound and Python threads share one core (the GIL), so the 40-thread
    pool would only make every program slower. A small cap keeps latency predictable;
    a client told "busy, retry in 1 s" is better off than one stuck in a queue.
    """
    if not slots.acquire(blocking=False):
        raise ApiError(
            503,
            "server_busy",
            "The server is busy running other programs. Retry shortly.",
            headers={"Retry-After": str(BUSY_RETRY_SECONDS)},
        )
    try:
        yield
    finally:
        slots.release()


Source = Annotated[str, Depends(program_source)]
Slots = Annotated[threading.BoundedSemaphore, Depends(get_program_slots)]


# Plain `def` (not `async def`): FastAPI runs these in a thread pool, so a program
# that takes a while to compile can't block the event loop for other requests.
@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    operation_id="getHealth",
    tags=["service"],
)
def health(response: Response) -> HealthResponse:
    """Liveness check for the hosting platform and monitors."""
    response.headers["Cache-Control"] = "no-store"  # a cached "ok" would hide an outage
    return HealthResponse(status="ok", version=__version__)


@router.post(
    "/v1/run",
    response_model=RunResponse,
    responses=ERRORS,
    summary="Compile and run a program",
    operation_id="runProgram",
    tags=["compiler"],
)
def run(source: Source, slots: Slots) -> dict:
    """Compile and run a program. A program error is a `200` with `ok: false`."""
    with program_slot(slots):
        return service.run_program(source)


@router.post(
    "/v1/check",
    response_model=CheckResponse,
    responses=ERRORS,
    summary="Type-check a program without running it",
    operation_id="checkProgram",
    tags=["compiler"],
)
def check(source: Source, slots: Slots) -> dict:
    """Lex, parse and type-check without running: the fastest feedback."""
    with program_slot(slots):
        return service.check_program(source)


@router.post(
    "/v1/compile",
    response_model=None,
    responses={200: {"model": CompileResponse, "description": "Every stage"}, **ERRORS},
    summary="Show every compiler stage",
    operation_id="compileProgram",
    tags=["compiler"],
)
def compile_stages(source: Source, slots: Slots) -> JSONResponse:
    """Every compiler stage: tokens, AST, three-address code, pseudo-assembly and output.

    Returned as a plain JSONResponse: validating a large AST through the recursive
    response model on every request costs time and checks nothing new (the service
    builds it). `responses` keeps CompileResponse in the docs.
    """
    with program_slot(slots):
        return JSONResponse(service.compile_program(source))


@router.get(
    "/v1/spec",
    response_class=Response,
    responses={200: {"content": {"text/markdown": {}}}},
    summary="The language specification",
    operation_id="getLanguageSpec",
    tags=["language"],
)
def spec(request: Request) -> Response:
    """The MiniLang language specification, for people and for AI agents learning it."""
    return Response(request.app.state.spec, media_type="text/markdown; charset=utf-8")

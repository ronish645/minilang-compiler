"""Request and response models (Pydantic v2). They also generate the OpenAPI docs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from minilang.api.config import SOURCE_CHARS_CEILING

EXAMPLE = 'fn square(x) { return x * x; }\nprint("9 squared is " + str(square(9)));'


class ProgramRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")  # a typo like "sorce" is an error, not ignored

    # maxLength documents the default (and largest) limit; a server may set a lower one
    # with MINILANG_MAX_SOURCE_CHARS, which the route checks and reports as a 422.
    source: str = Field(
        min_length=1,
        max_length=SOURCE_CHARS_CEILING,
        description=f"MiniLang source code, at most {SOURCE_CHARS_CEILING:,} characters "
        "(a server may configure a lower limit)",
        examples=[EXAMPLE],
    )


class ProgramError(BaseModel):
    stage: str = Field(description="lexer, syntax, semantic or runtime")
    message: str
    line: int | None = None
    col: int | None = None
    hint: str | None = Field(default=None, description="A suggested fix, when there is one")


class RunResponse(BaseModel):
    ok: bool
    output: list[str] = Field(description="Printed lines (partial output on a runtime error)")
    errors: list[ProgramError]
    diagnostic: str | None = Field(description="Every error with source snippets, as text")


class CheckResponse(BaseModel):
    ok: bool
    errors: list[ProgramError]
    diagnostic: str | None


class Token(BaseModel):
    type: str
    value: str
    line: int
    col: int


class AstNode(BaseModel):
    kind: str
    value: Any = None
    type: str | None = Field(default=None, description="Literal type, on Literal nodes")
    line: int
    col: int
    children: list[AstNode]


class CompileResponse(BaseModel):
    ok: bool
    failed_stage: str | None
    tokens: list[Token] | None
    ast: AstNode | None
    tac: list[str] | None = Field(description="Three-address code")
    asm: list[str] | None = Field(description="Pseudo-assembly")
    output: list[str]
    errors: list[ProgramError]
    diagnostic: str | None
    timings_ms: dict[str, float]


class HealthResponse(BaseModel):
    status: str
    version: str


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorBody(BaseModel):
    code: str = Field(description="Stable, machine-readable: invalid_request, rate_limited, ...")
    message: str
    details: list[ErrorDetail] | None = None


class ErrorResponse(BaseModel):
    """Every non-2xx response has this shape."""

    error: ErrorBody

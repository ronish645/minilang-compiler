"""Cheap refusals that run before FastAPI reads or parses a request body.

FastAPI parses the JSON body *before* it runs route dependencies, so a check written as
a dependency still pays for the parse. As ASGI middleware these checks run first:
a throttled or oversized request is refused before the app touches its body.
"""

from __future__ import annotations

import math

from starlette.datastructures import MutableHeaders
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from minilang.api.errors import error_response
from minilang.api.middleware import client_ip
from minilang.api.ratelimit import RateLimiter

RATE_LIMITED_PATHS = frozenset({"/v1/run", "/v1/check", "/v1/compile"})


class RateLimitMiddleware:
    """Charge one token per compiler request; refuse with 429 before the body is read."""

    def __init__(self, app: ASGIApp, limiter: RateLimiter, trusted_proxy_hops: int = 0) -> None:
        self.app = app
        self.limiter = limiter
        self.trusted_proxy_hops = trusted_proxy_hops

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not (
            scope["type"] == "http"
            and scope["method"] == "POST"
            and scope["path"] in RATE_LIMITED_PATHS
        ):
            await self.app(scope, receive, send)
            return
        decision = self.limiter.check(client_ip(HTTPConnection(scope), self.trusted_proxy_hops))
        limit = {"X-RateLimit-Limit": str(self.limiter.per_minute)}
        if not decision.allowed:
            response = error_response(
                429,
                "rate_limited",
                f"Too many requests: the limit is {self.limiter.per_minute} per minute.",
                headers={
                    **limit,
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(max(1, math.ceil(decision.retry_after))),
                },
            )
            await response(scope, receive, send)
            return

        async def send_with_budget(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.update({**limit, "X-RateLimit-Remaining": str(decision.remaining)})
            await send(message)

        await self.app(scope, receive, send_with_budget)


class BodyLimitMiddleware:
    """Refuse request bodies over ``max_bytes``, whether or not they declare their size.

    A declared ``Content-Length`` over the limit is refused without reading anything.
    A chunked body (no Content-Length) is read message by message and refused the moment
    the running total passes the limit; a body within the limit is handed to the app.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        declared = HTTPConnection(scope).headers.get("content-length", "")
        if declared.isdigit() and int(declared) > self.max_bytes:
            await self.refuse(scope, receive, send)
            return

        chunks: list[bytes] = []
        total = 0
        while True:
            message = await receive()
            if message["type"] != "http.request":  # the client went away
                await self.app(scope, replay([message], receive), send)
                return
            body = message.get("body", b"")
            total += len(body)
            if total > self.max_bytes:
                await self.refuse(scope, receive, send)
                return
            chunks.append(body)
            if not message.get("more_body", False):
                break
        whole = {"type": "http.request", "body": b"".join(chunks), "more_body": False}
        await self.app(scope, replay([whole], receive), send)

    async def refuse(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = error_response(
            413, "payload_too_large", f"Request bodies are limited to {self.max_bytes} bytes."
        )
        await response(scope, receive, send)


def replay(messages: list[Message], receive: Receive) -> Receive:
    """A receive callable that returns ``messages`` first, then defers to ``receive``."""
    pending = list(messages)

    async def replayed() -> Message:
        if pending:
            return pending.pop(0)
        return await receive()

    return replayed

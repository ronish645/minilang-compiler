"""Per-request plumbing: the client's IP, a request ID, a log line, and a safety net for 500s.

These are *pure ASGI* middlewares (a class called with ``scope, receive, send``) rather
than ``@app.middleware("http")``: they see every message, so they can stamp headers on
any response (including errors produced by other middleware) and catch crashes.
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from minilang.api.errors import error_response

logger = logging.getLogger("minilang.api")

REQUEST_ID_HEADER = "X-Request-ID"
# Accept a caller's ID only if it's short and plain, so it can't inject into logs.
SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def request_id_for(connection: HTTPConnection) -> str:
    given = connection.headers.get(REQUEST_ID_HEADER, "")
    return given if SAFE_REQUEST_ID.match(given) else uuid.uuid4().hex


def client_ip(connection: HTTPConnection, hops: int) -> str:
    """The caller's IP, trusting X-Forwarded-For only as far as our own proxies.

    Each proxy *appends* the address it received the request from, so the rightmost
    entries are written by our infrastructure and everything to their left is whatever
    the client sent. With ``hops`` trusted proxies, the client is the ``hops``-th entry
    from the right. With ``hops=0`` the header is ignored: the socket peer is the client.
    """
    peer = connection.client.host if connection.client else "unknown"
    if hops == 0:
        return peer
    values = connection.headers.getlist("x-forwarded-for")
    entries = [entry.strip() for entry in ",".join(values).split(",") if entry.strip()]
    if len(entries) < hops:
        return peer  # not what our proxy chain produces: don't guess
    return entries[-hops]


class RequestContextMiddleware:
    """Request ID on every response, one JSON log line per request, and a clean 500."""

    def __init__(self, app: ASGIApp, trusted_proxy_hops: int = 0) -> None:
        self.app = app
        self.trusted_proxy_hops = trusted_proxy_hops

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        connection = HTTPConnection(scope)
        request_id = request_id_for(connection)
        scope.setdefault("state", {})["request_id"] = request_id
        start = time.perf_counter()
        status = 500
        started = False

        async def send_with_id(message: Message) -> None:
            nonlocal status, started
            if message["type"] == "http.response.start":
                started = True
                status = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        except Exception:
            # Inside CORS, so the browser can read the 500; outside, it would be opaque.
            logger.exception(
                "unhandled error (request_id=%s) on %s %s",
                request_id,
                scope["method"],
                scope["path"],
            )
            if started:  # headers already went out; nothing clean left to send
                raise
            response = error_response(500, "internal_error", "Something went wrong on our side.")
            await response(scope, receive, send_with_id)
        finally:
            self.log(connection, request_id, status, start)

    def log(self, connection: HTTPConnection, request_id: str, status: int, start: float) -> None:
        logger.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "method": connection.scope["method"],
                    "path": connection.url.path,
                    "status": status,
                    "ms": round((time.perf_counter() - start) * 1000, 1),
                    "client": client_ip(connection, self.trusted_proxy_hops),
                }
            )
        )

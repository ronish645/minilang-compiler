"""App factory: settings, rate limiter, middleware, CORS, error handlers, routes."""

from __future__ import annotations

import logging
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from minilang import __version__, service
from minilang.api.config import Settings
from minilang.api.errors import install_error_handlers
from minilang.api.guards import BodyLimitMiddleware, RateLimitMiddleware
from minilang.api.middleware import REQUEST_ID_HEADER, RequestContextMiddleware
from minilang.api.ratelimit import RateLimiter
from minilang.api.routes import router

DESCRIPTION = """
Compile, check and run [MiniLang](https://github.com/ronish645/minilang-compiler) programs.

* A problem **in the program** (syntax, type or runtime error) is a normal `200` response with
  `ok: false`, the errors with fix-it hints, and a diagnostic.
* A problem **with the request** is a `4xx` with `{"error": {"code", "message", "details"}}`;
  so are `500` (our bug) and `503 server_busy` (too many programs running; retry after
  `Retry-After` seconds).
* Compiler endpoints are rate limited per client; see the `X-RateLimit-*` headers.
"""


def configure_logging() -> None:
    """Send the API's one-line JSON request logs to stdout (where hosts collect logs)."""
    logger = logging.getLogger("minilang.api")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="MiniLang API", version=__version__, description=DESCRIPTION)
    app.state.settings = settings
    app.state.limiter = RateLimiter(settings.rate_limit_per_minute)
    app.state.program_slots = threading.BoundedSemaphore(settings.max_concurrent_programs)
    app.state.spec = service.language_spec()  # a missing spec file fails here, at startup

    # Each add_middleware wraps the app built so far, so the LAST one added runs FIRST:
    #   CORS -> request ID / log / 500 -> rate limit -> body limit -> FastAPI
    # Rate limit before body limit: a throttled client is refused before any reading.
    # Both sit inside the request-ID layer and CORS, so 413/429/500 carry X-Request-ID
    # and Access-Control-Allow-Origin like any other response.
    app.add_middleware(BodyLimitMiddleware, max_bytes=settings.max_body_bytes)
    app.add_middleware(
        RateLimitMiddleware,
        limiter=app.state.limiter,
        trusted_proxy_hops=settings.trusted_proxy_hops,
        client_ip_header=settings.client_ip_header,
    )
    app.add_middleware(
        RequestContextMiddleware,
        trusted_proxy_hops=settings.trusted_proxy_hops,
        client_ip_header=settings.client_ip_header,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", REQUEST_ID_HEADER],
        expose_headers=[
            REQUEST_ID_HEADER,
            "Retry-After",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
        ],
    )
    install_error_handlers(app)
    app.include_router(router)
    return app


configure_logging()
app = create_app()  # what uvicorn serves: `uvicorn minilang.api.app:app`

"""Settings read from environment variables (all optional)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

DEFAULT_ORIGINS = (
    "https://ronish645.github.io",  # the showcase site
    "http://localhost:5173",  # Vite dev server
    "http://localhost:4173",  # Vite preview
)

# The OpenAPI schema documents this as `source`'s maxLength. The setting may lower the
# limit, never raise it: a larger value would be silently capped by the schema.
SOURCE_CHARS_CEILING = 20_000


def env_int(name: str, default: int, minimum: int = 1, maximum: int | None = None) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from None
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}, got {value}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must be at most {maximum}, got {value}")
    return value


def env_list(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.environ.get(name)
    if not raw:
        return default
    return tuple(item.strip() for item in raw.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    rate_limit_per_minute: int = 30  # per client IP, on the compiler endpoints
    max_source_chars: int = SOURCE_CHARS_CEILING  # programs are rarely over a few hundred lines
    allowed_origins: tuple[str, ...] = field(default=DEFAULT_ORIGINS)
    # How many proxies in front of us append to X-Forwarded-For. 0: trust no header and
    # use the socket peer. 1: the platform's load balancer (e.g. Render) appends one entry.
    trusted_proxy_hops: int = 0
    # A header our edge proxy overwrites with the client IP; it wins when it holds a
    # valid IP. On Render that's CF-Connecting-IP (Cloudflare sits in front of Render).
    client_ip_header: str | None = None
    # Programs compiled/run at the same time; more get a 503 instead of queueing CPU work.
    max_concurrent_programs: int = 4

    def __post_init__(self) -> None:
        if not 1 <= self.max_source_chars <= SOURCE_CHARS_CEILING:
            raise ValueError(
                f"max_source_chars must be between 1 and {SOURCE_CHARS_CEILING}, "
                f"got {self.max_source_chars}"
            )
        if self.trusted_proxy_hops < 0:
            raise ValueError("trusted_proxy_hops must be at least 0")
        if self.max_concurrent_programs < 1:
            raise ValueError("max_concurrent_programs must be at least 1")

    @property
    def max_body_bytes(self) -> int:
        # JSON escaping can grow text (e.g. "\n" -> "\\n", non-ASCII -> "\\uXXXX"), so
        # allow headroom before the precise per-field check in the schema.
        return self.max_source_chars * 6 + 1024

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            rate_limit_per_minute=env_int("MINILANG_RATE_LIMIT_PER_MINUTE", 30),
            max_source_chars=env_int(
                "MINILANG_MAX_SOURCE_CHARS", SOURCE_CHARS_CEILING, maximum=SOURCE_CHARS_CEILING
            ),
            allowed_origins=env_list("MINILANG_ALLOWED_ORIGINS", DEFAULT_ORIGINS),
            trusted_proxy_hops=env_int("MINILANG_TRUSTED_PROXY_HOPS", 0, minimum=0),
            client_ip_header=os.environ.get("MINILANG_CLIENT_IP_HEADER", "").strip() or None,
            max_concurrent_programs=env_int("MINILANG_MAX_CONCURRENT_PROGRAMS", 4),
        )

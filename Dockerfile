# MiniLang REST API: a small image that runs as a non-root user.
#   docker build -t minilang-api .
#   docker run -p 8000:8000 minilang-api        # then open http://localhost:8000/docs
# A pinned patch version: rebuilds are reproducible; bump it deliberately for security fixes.
FROM python:3.12.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

WORKDIR /app

# Only what the API needs: the package, its metadata and the language spec it serves.
COPY pyproject.toml README.md ./
COPY minilang ./minilang
COPY docs/LANGUAGE_SPEC.md ./docs/LANGUAGE_SPEC.md
# Editable install: the package stays in /app, next to docs/ (where /v1/spec reads the spec).
RUN pip install -e ".[api]"

RUN useradd --create-home --uid 10001 app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/health', timeout=3)"

# Hosts like Render set $PORT.
# --no-proxy-headers: uvicorn must not rewrite the client address from X-Forwarded-For
#   (its leftmost entry is whatever the client typed). The app trusts only the entries
#   our own proxies append: see MINILANG_TRUSTED_PROXY_HOPS in render.yaml.
# --workers 1: the rate limiter and concurrency gate live in memory, per process.
# --limit-concurrency 64: beyond 64 open connections uvicorn answers 503 straight away.
# --timeout-keep-alive 5: idle connections don't hold a slot for long.
# --no-server-header: don't advertise the server software and version.
CMD ["sh", "-c", "exec uvicorn minilang.api.app:app --host 0.0.0.0 --port ${PORT} --no-proxy-headers --workers 1 --limit-concurrency 64 --timeout-keep-alive 5 --no-server-header"]

"""Abuse resistance: client IPs behind proxies, streamed bodies, throttling order, busy server."""

import json
import logging

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from minilang.api.app import create_app
from minilang.api.config import Settings
from minilang.api.guards import BodyLimitMiddleware
from minilang.api.middleware import RequestContextMiddleware, client_ip

HELLO = 'print("hi");'
ORIGIN = "https://ronish645.github.io"  # an allowed origin by default


def client_for(**overrides) -> TestClient:
    settings = Settings(**{"rate_limit_per_minute": 1000, **overrides})
    return TestClient(create_app(settings), raise_server_exceptions=False)


def request_with(peer: str, forwarded: list[str]) -> Request:
    headers = [(b"x-forwarded-for", value.encode()) for value in forwarded]
    return Request({"type": "http", "headers": headers, "client": (peer, 1234)})


@pytest.fixture
def access_log():
    """Collect the API's log records (its logger doesn't propagate to the root)."""
    records: list[logging.LogRecord] = []

    class Collector(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    logger = logging.getLogger("minilang.api")
    handler = Collector()
    previous_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    yield records
    logger.removeHandler(handler)
    logger.setLevel(previous_level)


def json_lines(records: list[logging.LogRecord]) -> list[dict]:
    lines = []
    for record in records:
        try:
            lines.append(json.loads(record.getMessage()))
        except ValueError:
            continue
    return lines


class TestClientIp:
    def test_without_trusted_proxies_the_socket_peer_is_used(self):
        assert client_ip(request_with("9.9.9.9", ["1.2.3.4"]), hops=0) == "9.9.9.9"

    def test_one_hop_takes_the_entry_our_proxy_appended(self):
        # The client wrote "6.6.6.6"; the proxy appended the address it really saw.
        request = request_with("10.0.0.1", ["6.6.6.6, 7.7.7.7"])
        assert client_ip(request, hops=1) == "7.7.7.7"

    def test_two_hops_count_from_the_right(self):
        request = request_with("10.0.0.1", ["6.6.6.6, 7.7.7.7, 8.8.8.8"])
        assert client_ip(request, hops=2) == "7.7.7.7"

    def test_repeated_headers_are_read_as_one_list(self):
        request = request_with("10.0.0.1", ["6.6.6.6", "7.7.7.7"])
        assert client_ip(request, hops=1) == "7.7.7.7"

    def test_falls_back_to_the_peer_when_the_header_is_too_short(self):
        assert client_ip(request_with("10.0.0.1", ["7.7.7.7"]), hops=2) == "10.0.0.1"
        assert client_ip(request_with("10.0.0.1", []), hops=1) == "10.0.0.1"

    def test_unknown_peer(self):
        assert client_ip(Request({"type": "http", "headers": []}), hops=0) == "unknown"


class TestSpoofedForwardedFor:
    def test_a_spoofed_header_does_not_get_a_fresh_bucket(self):
        client = client_for(rate_limit_per_minute=1)
        first = client.post(
            "/v1/check", json={"source": HELLO}, headers={"X-Forwarded-For": "1.1.1.1"}
        )
        second = client.post(
            "/v1/check", json={"source": HELLO}, headers={"X-Forwarded-For": "2.2.2.2"}
        )
        assert (first.status_code, second.status_code) == (200, 429)

    def test_behind_one_proxy_the_rightmost_entry_is_the_client(self):
        client = client_for(rate_limit_per_minute=1, trusted_proxy_hops=1)
        codes = [
            client.post(
                "/v1/check", json={"source": HELLO}, headers={"X-Forwarded-For": forwarded}
            ).status_code
            for forwarded in ("spoof-a, 1.1.1.1", "spoof-b, 1.1.1.1", "spoof-a, 2.2.2.2")
        ]
        assert codes == [200, 429, 200]

    def test_the_access_log_records_the_resolved_client(self, access_log):
        client = client_for(trusted_proxy_hops=1)
        client.get("/health", headers={"X-Forwarded-For": "6.6.6.6, 7.7.7.7"})
        assert json_lines(access_log)[-1]["client"] == "7.7.7.7"


class TestStreamedBodyLimit:
    def test_a_chunked_body_over_the_limit_is_a_413(self):
        client = client_for(max_source_chars=10)

        def chunks():
            for _ in range(10):
                yield b"x" * 1000

        response = client.post(
            "/v1/run", content=chunks(), headers={"content-type": "application/json"}
        )
        assert "content-length" not in response.request.headers  # really chunked
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "payload_too_large"
        assert response.headers["x-request-id"]

    def test_a_chunked_body_within_the_limit_reaches_the_app(self):
        client = client_for()
        body = json.dumps({"source": "print(1 + 2);"}).encode()

        def chunks():
            yield body

        response = client.post(
            "/v1/run", content=chunks(), headers={"content-type": "application/json"}
        )
        assert response.status_code == 200
        assert response.json()["output"] == ["3"]

    def test_413_carries_cors_headers(self):
        client = client_for(max_source_chars=10)
        response = client.post(
            "/v1/run",
            content="x" * 5000,
            headers={"content-type": "application/json", "Origin": ORIGIN},
        )
        assert response.status_code == 413
        assert response.headers["access-control-allow-origin"] == ORIGIN


class TestBodyLimitMiddleware:
    """Drive the ASGI middleware directly to see exactly how much it reads."""

    @staticmethod
    async def run_middleware(chunks: list[bytes], max_bytes: int, headers=()):
        messages = [{"type": "http.request", "body": c, "more_body": True} for c in chunks]
        messages.append({"type": "http.request", "body": b"", "more_body": False})
        reads = 0
        received_by_app: list[bytes] = []
        sent: list[dict] = []

        async def receive():
            nonlocal reads
            reads += 1
            return messages.pop(0)

        async def send(message):
            sent.append(message)

        async def app(scope, receive, send):
            while True:
                message = await receive()
                received_by_app.append(message.get("body", b""))
                if not message.get("more_body"):
                    break
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})

        scope = {"type": "http", "method": "POST", "path": "/v1/run", "headers": list(headers)}
        await BodyLimitMiddleware(app, max_bytes=max_bytes)(scope, receive, send)
        return reads, b"".join(received_by_app), sent

    @pytest.mark.anyio
    async def test_stops_reading_as_soon_as_the_limit_is_passed(self):
        reads, received, sent = await self.run_middleware([b"a" * 60] * 10, max_bytes=100)
        assert reads == 2  # 60 bytes, then 120 > 100: refused without reading the rest
        assert received == b""  # the app never saw the request
        assert sent[0]["status"] == 413

    @pytest.mark.anyio
    async def test_replays_a_body_within_the_limit(self):
        reads, received, sent = await self.run_middleware([b"ab", b"cd"], max_bytes=100)
        assert received == b"abcd"
        assert sent[0]["status"] == 200

    @pytest.mark.anyio
    async def test_a_declared_length_over_the_limit_is_refused_unread(self):
        reads, _, sent = await self.run_middleware(
            [b"a"], max_bytes=100, headers=[(b"content-length", b"5000")]
        )
        assert reads == 0
        assert sent[0]["status"] == 413


class TestThrottledBeforeParsing:
    def test_a_throttled_request_is_refused_before_its_body_is_read(self):
        client = client_for(rate_limit_per_minute=1)
        client.post("/v1/check", json={"source": HELLO})
        # Invalid JSON would be a 422 if the body were parsed; a 429 proves it wasn't.
        refused = client.post(
            "/v1/check",
            content="{not json",
            headers={"content-type": "application/json", "Origin": ORIGIN},
        )
        assert refused.status_code == 429
        assert refused.json()["error"]["code"] == "rate_limited"
        assert refused.headers["x-ratelimit-limit"] == "1"
        assert refused.headers["x-ratelimit-remaining"] == "0"
        assert int(refused.headers["retry-after"]) >= 1
        assert refused.headers["x-request-id"]
        assert refused.headers["access-control-allow-origin"] == ORIGIN

    @pytest.mark.parametrize("path", ["/v1/run", "/v1/check", "/v1/compile"])
    def test_every_compiler_endpoint_is_limited(self, path):
        client = client_for(rate_limit_per_minute=1)
        codes = [client.post(path, json={"source": HELLO}).status_code for _ in range(2)]
        assert codes == [200, 429]

    def test_docs_and_openapi_are_not_limited(self):
        client = client_for(rate_limit_per_minute=1)
        assert all(client.get("/openapi.json").status_code == 200 for _ in range(3))
        assert all(client.get("/docs").status_code == 200 for _ in range(3))


class TestConcurrencyGate:
    def test_a_saturated_server_answers_503_with_retry_after(self):
        app = create_app(Settings(max_concurrent_programs=1))
        client = TestClient(app)
        slots = app.state.program_slots
        assert slots.acquire(blocking=False)  # another program is "running"
        try:
            busy = client.post("/v1/run", json={"source": HELLO}, headers={"Origin": ORIGIN})
        finally:
            slots.release()
        assert busy.status_code == 503
        assert busy.json()["error"]["code"] == "server_busy"
        assert busy.headers["retry-after"] == "1"
        assert busy.headers["access-control-allow-origin"] == ORIGIN
        assert client.post("/v1/run", json={"source": HELLO}).status_code == 200

    def test_the_slot_is_released_after_each_program(self):
        app = create_app(Settings(max_concurrent_programs=1))
        client = TestClient(app)
        for path in ("/v1/run", "/v1/check", "/v1/compile", "/v1/run"):
            assert client.post(path, json={"source": HELLO}).status_code == 200

    def test_the_slot_is_released_when_a_program_crashes(self, monkeypatch):
        def explode(_source):
            raise RuntimeError("boom")

        monkeypatch.setattr("minilang.service.check_program", explode)
        app = create_app(Settings(max_concurrent_programs=1))
        client = TestClient(app, raise_server_exceptions=False)
        assert client.post("/v1/check", json={"source": HELLO}).status_code == 500
        assert app.state.program_slots.acquire(blocking=False)


class TestOpenApi:
    @pytest.fixture
    def schema(self):
        return client_for().get("/openapi.json").json()

    def test_source_length_is_documented(self, schema):
        source = schema["components"]["schemas"]["ProgramRequest"]["properties"]["source"]
        assert source["maxLength"] == 20_000
        assert "20000" in source["description"].replace(",", "")

    def test_routes_have_summaries_and_operation_ids(self, schema):
        operations = [op for path in schema["paths"].values() for op in path.values()]
        assert all(op.get("summary") and op.get("operationId") for op in operations)
        assert schema["paths"]["/v1/run"]["post"]["operationId"] == "runProgram"

    @pytest.mark.parametrize("path", ["/v1/run", "/v1/check", "/v1/compile"])
    def test_server_errors_are_documented(self, schema, path):
        assert {"500", "503"} <= set(schema["paths"][path]["post"]["responses"])

    def test_compile_still_documents_its_response_model(self, schema):
        ok = schema["paths"]["/v1/compile"]["post"]["responses"]["200"]
        ref = ok["content"]["application/json"]["schema"]["$ref"]
        assert ref.endswith("/CompileResponse")


def test_health_is_never_cached():
    assert client_for().get("/health").headers["cache-control"] == "no-store"


def test_a_source_at_the_schema_limit_is_accepted_and_over_it_rejected():
    client = client_for()
    ok = client.post("/v1/check", json={"source": "x" * 20_000})
    too_long = client.post("/v1/check", json={"source": "x" * 20_001})
    assert ok.status_code == 200
    assert too_long.status_code == 422


class TestEdgeCases:
    @pytest.mark.anyio
    async def test_a_client_disconnect_is_passed_on_to_the_app(self):
        seen: list[str] = []

        async def receive():
            return {"type": "http.disconnect"}

        async def send(message):
            pass

        async def app(scope, receive, send):
            seen.append((await receive())["type"])

        scope = {"type": "http", "method": "POST", "path": "/v1/run", "headers": []}
        await BodyLimitMiddleware(app, max_bytes=10)(scope, receive, send)
        assert seen == ["http.disconnect"]

    @pytest.mark.anyio
    async def test_non_http_scopes_pass_straight_through(self):
        calls: list[str] = []

        async def app(scope, receive, send):
            calls.append(scope["type"])

        for middleware in (BodyLimitMiddleware(app, max_bytes=1), RequestContextMiddleware(app)):
            await middleware({"type": "lifespan"}, None, None)
        assert calls == ["lifespan", "lifespan"]

    @pytest.mark.anyio
    async def test_a_crash_after_the_response_started_is_re_raised(self):
        async def app(scope, receive, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})
            raise RuntimeError("mid-stream")

        async def send(message):
            pass

        scope = {"type": "http", "method": "GET", "path": "/x", "headers": []}
        with pytest.raises(RuntimeError, match="mid-stream"):
            await RequestContextMiddleware(app)(scope, None, send)

    @pytest.mark.parametrize(
        "overrides", [{"trusted_proxy_hops": -1}, {"max_concurrent_programs": 0}]
    )
    def test_settings_reject_out_of_range_values(self, overrides):
        with pytest.raises(ValueError):
            Settings(**overrides)

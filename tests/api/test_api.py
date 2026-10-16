"""REST API endpoints, validation, error format and rate limiting."""

import pytest
from fastapi.testclient import TestClient

from minilang import __version__
from minilang.api.app import create_app
from minilang.api.config import Settings

HELLO = 'print("hi");'


def client_for(**overrides) -> TestClient:
    settings = Settings(**{"rate_limit_per_minute": 1000, **overrides})
    return TestClient(create_app(settings))


@pytest.fixture
def client() -> TestClient:
    return client_for()


class TestHealth:
    def test_reports_status_and_version(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "version": __version__}

    def test_every_response_has_a_request_id(self, client):
        assert client.get("/health").headers["x-request-id"]

    def test_a_given_request_id_is_echoed(self, client):
        response = client.get("/health", headers={"X-Request-ID": "abc-123"})
        assert response.headers["x-request-id"] == "abc-123"


class TestRun:
    def test_runs_a_program(self, client):
        response = client.post("/v1/run", json={"source": "print(1 + 2);"})
        assert response.status_code == 200
        assert response.json() == {"ok": True, "output": ["3"], "errors": [], "diagnostic": None}

    def test_a_program_error_is_a_200_with_ok_false(self, client):
        # The request succeeded; the *program* failed. That's data, not an HTTP error.
        data = client.post("/v1/run", json={"source": "let total = 1; print(totl);"}).json()
        assert data["ok"] is False
        assert data["errors"][0]["stage"] == "semantic"
        assert data["errors"][0]["hint"] == "did you mean 'total'?"
        assert "error[semantic]" in data["diagnostic"]

    def test_runtime_error_keeps_partial_output(self, client):
        data = client.post("/v1/run", json={"source": "print(1);\nprint(1 / 0);"}).json()
        assert data["output"] == ["1"]
        assert data["errors"][0]["stage"] == "runtime"

    def test_every_error_is_reported(self, client):
        data = client.post("/v1/run", json={"source": "let x = ;\nlet y = ;"}).json()
        assert len(data["errors"]) == 2

    def test_runaway_program_is_stopped(self, client):
        data = client.post("/v1/run", json={"source": "while (true) { }"}).json()
        assert data["ok"] is False
        assert "step limit exceeded" in data["errors"][0]["message"]


class TestCheck:
    def test_valid_program_is_not_executed(self, client):
        data = client.post("/v1/check", json={"source": "while (true) { }"}).json()
        assert data == {"ok": True, "errors": [], "diagnostic": None}

    def test_invalid_program_lists_errors(self, client):
        data = client.post("/v1/check", json={"source": "let x = True;"}).json()
        assert data["ok"] is False
        assert data["errors"][0]["hint"] == "booleans are lowercase: true / false"


class TestCompile:
    def test_returns_every_stage(self, client):
        data = client.post("/v1/compile", json={"source": "let x = 1 + 2;"}).json()
        assert data["ok"] is True
        assert data["tokens"][0] == {"type": "KW", "value": "let", "line": 1, "col": 1}
        assert data["ast"]["kind"] == "Program"
        assert data["tac"] == ["t1 = 1 + 2", "x = t1"]
        assert set(data["timings_ms"]) == {"lex", "parse", "check", "codegen", "run"}

    def test_failed_stage_keeps_earlier_stages(self, client):
        data = client.post("/v1/compile", json={"source": "let x = ;"}).json()
        assert data["failed_stage"] == "syntax"
        assert data["tokens"] and data["ast"] is None


class TestSpec:
    def test_serves_the_language_spec_as_markdown(self, client):
        response = client.get("/v1/spec")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/markdown")
        assert response.text.startswith("# MiniLang Language Specification")


class TestValidation:
    @pytest.mark.parametrize(
        "body",
        [{}, {"source": ""}, {"source": 42}, {"source": "print(1);", "extra": True}],
    )
    def test_bad_bodies_get_a_422_in_the_error_format(self, client, body):
        response = client.post("/v1/run", json=body)
        assert response.status_code == 422
        error = response.json()["error"]
        assert error["code"] == "invalid_request"
        assert error["details"]

    def test_too_long_source_is_rejected(self):
        client = client_for(max_source_chars=10)
        response = client.post("/v1/run", json={"source": "print(1234567890);"})
        assert response.status_code == 422
        assert "at most 10 characters" in response.json()["error"]["details"][0]["message"]

    def test_oversized_body_is_a_413_before_parsing(self):
        client = client_for(max_source_chars=10)
        response = client.post(
            "/v1/run", content="x" * 5000, headers={"content-type": "application/json"}
        )
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "payload_too_large"

    def test_unknown_route_uses_the_error_format(self, client):
        response = client.get("/v1/nope")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"


class TestRateLimit:
    def test_limits_each_client_and_says_when_to_retry(self):
        client = client_for(rate_limit_per_minute=2)
        codes = [client.post("/v1/check", json={"source": HELLO}).status_code for _ in range(3)]
        assert codes == [200, 200, 429]
        refused = client.post("/v1/check", json={"source": HELLO})
        assert refused.json()["error"]["code"] == "rate_limited"
        assert int(refused.headers["retry-after"]) >= 1

    def test_successful_responses_report_the_remaining_budget(self):
        client = client_for(rate_limit_per_minute=5)
        response = client.post("/v1/check", json={"source": HELLO})
        assert response.headers["x-ratelimit-limit"] == "5"
        assert response.headers["x-ratelimit-remaining"] == "4"

    def test_health_and_spec_are_not_rate_limited(self):
        client = client_for(rate_limit_per_minute=1)
        assert all(client.get("/health").status_code == 200 for _ in range(5))
        assert all(client.get("/v1/spec").status_code == 200 for _ in range(5))


class TestCors:
    def test_allows_the_showcase_site(self, client):
        origin = "https://ronish645.github.io"
        response = client.options(
            "/v1/run",
            headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
        )
        assert response.headers["access-control-allow-origin"] == origin

    def test_ignores_other_origins(self, client):
        response = client.options(
            "/v1/run",
            headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
        )
        assert "access-control-allow-origin" not in response.headers


def test_openapi_docs_are_published(client):
    schema = client.get("/openapi.json").json()
    assert {"/v1/run", "/v1/check", "/v1/compile", "/v1/spec", "/health"} <= set(schema["paths"])
    assert client.get("/docs").status_code == 200

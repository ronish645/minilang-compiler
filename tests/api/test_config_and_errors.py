"""Settings from the environment, startup checks, and the 500 that hides internals."""

import json
import logging

import pytest
from fastapi.testclient import TestClient

from minilang import service
from minilang.api.app import create_app
from minilang.api.config import DEFAULT_ORIGINS, Settings


class TestSettingsFromEnv:
    def test_defaults_without_variables(self, monkeypatch):
        names = (
            "RATE_LIMIT_PER_MINUTE",
            "MAX_SOURCE_CHARS",
            "ALLOWED_ORIGINS",
            "TRUSTED_PROXY_HOPS",
            "MAX_CONCURRENT_PROGRAMS",
        )
        for name in names:
            monkeypatch.delenv(f"MINILANG_{name}", raising=False)
        assert Settings.from_env() == Settings()

    def test_reads_variables(self, monkeypatch):
        monkeypatch.setenv("MINILANG_RATE_LIMIT_PER_MINUTE", "5")
        monkeypatch.setenv("MINILANG_MAX_SOURCE_CHARS", "100")
        monkeypatch.setenv("MINILANG_ALLOWED_ORIGINS", "https://a.example, https://b.example")
        settings = Settings.from_env()
        assert settings.rate_limit_per_minute == 5
        assert settings.max_source_chars == 100
        assert settings.allowed_origins == ("https://a.example", "https://b.example")

    def test_reads_proxy_hops_and_concurrency(self, monkeypatch):
        monkeypatch.setenv("MINILANG_TRUSTED_PROXY_HOPS", "1")
        monkeypatch.setenv("MINILANG_MAX_CONCURRENT_PROGRAMS", "2")
        settings = Settings.from_env()
        assert settings.trusted_proxy_hops == 1
        assert settings.max_concurrent_programs == 2

    def test_zero_proxy_hops_is_allowed(self, monkeypatch):
        monkeypatch.setenv("MINILANG_TRUSTED_PROXY_HOPS", "0")
        assert Settings.from_env().trusted_proxy_hops == 0

    @pytest.mark.parametrize(
        ("name", "value"),
        [
            ("MINILANG_TRUSTED_PROXY_HOPS", "-1"),
            ("MINILANG_MAX_CONCURRENT_PROGRAMS", "0"),
            ("MINILANG_MAX_SOURCE_CHARS", "20001"),  # above the documented schema maximum
        ],
    )
    def test_rejects_out_of_range_values(self, monkeypatch, name, value):
        monkeypatch.setenv(name, value)
        with pytest.raises(ValueError, match=name):
            Settings.from_env()

    def test_a_source_limit_above_the_schema_maximum_is_refused(self):
        # The schema caps `source` at 20,000; a bigger setting would be silently capped.
        with pytest.raises(ValueError, match="max_source_chars"):
            Settings(max_source_chars=20_001)

    def test_empty_origin_list_falls_back_to_defaults(self, monkeypatch):
        monkeypatch.setenv("MINILANG_ALLOWED_ORIGINS", "")
        assert Settings.from_env().allowed_origins == DEFAULT_ORIGINS

    @pytest.mark.parametrize("value", ["abc", "0", "-3"])
    def test_rejects_invalid_numbers_at_startup(self, monkeypatch, value):
        monkeypatch.setenv("MINILANG_RATE_LIMIT_PER_MINUTE", value)
        with pytest.raises(ValueError, match="MINILANG_RATE_LIMIT_PER_MINUTE"):
            Settings.from_env()


class TestStartup:
    def test_a_missing_spec_fails_at_startup(self, monkeypatch, tmp_path):
        service.language_spec.cache_clear()
        monkeypatch.setattr(service, "SPEC_PATH", tmp_path / "missing.md")
        try:
            with pytest.raises(FileNotFoundError):
                create_app(Settings())
        finally:
            monkeypatch.undo()
            service.language_spec.cache_clear()


def test_unexpected_errors_are_a_generic_500(monkeypatch):
    def explode(_source):
        raise RuntimeError("secret internal detail")

    records: list[logging.LogRecord] = []

    class Collector(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    logger = logging.getLogger("minilang.api")
    handler = Collector()
    logger.addHandler(handler)
    previous_level = logger.level
    logger.setLevel(logging.INFO)
    monkeypatch.setattr("minilang.service.check_program", explode)
    client = TestClient(create_app(Settings()), raise_server_exceptions=False)
    origin = "https://ronish645.github.io"
    try:
        response = client.post(
            "/v1/check",
            json={"source": "print(1);"},
            headers={"Origin": origin, "X-Request-ID": "trace-500"},
        )
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)

    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Something went wrong on our side."}
    }
    assert "secret" not in response.text
    assert response.headers["x-request-id"] == "trace-500"
    assert response.headers["access-control-allow-origin"] == origin
    # The traceback is logged with the request id, and the access line still says 500.
    crash = next(r for r in records if r.exc_info)
    assert "trace-500" in crash.getMessage()
    access = [json.loads(r.getMessage()) for r in records if r.getMessage().startswith("{")]
    assert access[-1]["status"] == 500
    assert access[-1]["request_id"] == "trace-500"

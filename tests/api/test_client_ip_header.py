"""A trusted client-IP header set by the edge proxy (e.g. Cloudflare's CF-Connecting-IP).

On Render, X-Forwarded-For can't identify the client: Render keeps whatever the
client sent (so the leftmost entry can be forged) and the rightmost entries are
proxy addresses that change between requests. Cloudflare, in front of Render,
overwrites CF-Connecting-IP with the real client address, so that header is the
one to trust there.
"""

import pytest
from fastapi.testclient import TestClient
from starlette.requests import HTTPConnection

from minilang.api.app import create_app
from minilang.api.config import Settings
from minilang.api.middleware import client_ip


def connection(headers: dict[str, str], peer: str = "10.0.0.1") -> HTTPConnection:
    raw = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    return HTTPConnection({"type": "http", "headers": raw, "client": (peer, 1234)})


class TestClientIpHeader:
    def test_trusted_header_wins_over_forwarded_for(self):
        conn = connection({"CF-Connecting-IP": "203.0.113.7", "X-Forwarded-For": "6.6.6.6"})
        assert client_ip(conn, hops=1, header="CF-Connecting-IP") == "203.0.113.7"

    def test_ipv6_is_accepted(self):
        conn = connection({"CF-Connecting-IP": "2001:db8::1"})
        assert client_ip(conn, hops=0, header="CF-Connecting-IP") == "2001:db8::1"

    @pytest.mark.parametrize("value", ["", "not-an-ip", "1.2.3.4, 5.6.7.8", "999.1.1.1"])
    def test_missing_or_invalid_header_falls_back(self, value):
        conn = connection({"CF-Connecting-IP": value}, peer="10.0.0.9")
        assert client_ip(conn, hops=0, header="CF-Connecting-IP") == "10.0.0.9"

    def test_header_is_ignored_unless_configured(self):
        conn = connection({"CF-Connecting-IP": "203.0.113.7"}, peer="10.0.0.9")
        assert client_ip(conn, hops=0) == "10.0.0.9"

    def test_invalid_forwarded_for_entry_falls_back_to_the_peer(self):
        conn = connection({"X-Forwarded-For": "1.1.1.1, garbage"}, peer="10.0.0.9")
        assert client_ip(conn, hops=1) == "10.0.0.9"


class TestEndToEnd:
    def test_one_client_shares_a_bucket_whatever_else_it_forges(self):
        app = create_app(Settings(rate_limit_per_minute=2, client_ip_header="CF-Connecting-IP"))
        client = TestClient(app)
        codes = [
            client.post(
                "/v1/check",
                json={"source": "print(1);"},
                headers={"CF-Connecting-IP": "203.0.113.7", "X-Forwarded-For": f"9.9.9.{i}"},
            ).status_code
            for i in range(3)
        ]
        assert codes == [200, 200, 429]

    def test_different_clients_get_different_buckets(self):
        app = create_app(Settings(rate_limit_per_minute=1, client_ip_header="CF-Connecting-IP"))
        client = TestClient(app)
        for ip in ("203.0.113.1", "203.0.113.2"):
            response = client.post(
                "/v1/check", json={"source": "print(1);"}, headers={"CF-Connecting-IP": ip}
            )
            assert response.status_code == 200


class TestSetting:
    def test_read_from_the_environment(self, monkeypatch):
        monkeypatch.setenv("MINILANG_CLIENT_IP_HEADER", "CF-Connecting-IP")
        assert Settings.from_env().client_ip_header == "CF-Connecting-IP"

    def test_empty_means_unset(self, monkeypatch):
        monkeypatch.setenv("MINILANG_CLIENT_IP_HEADER", "  ")
        assert Settings.from_env().client_ip_header is None

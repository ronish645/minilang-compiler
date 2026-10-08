"""MCP server: tool functions directly, plus one real stdio round trip."""

import json
import sys

import anyio
import pytest

pytest.importorskip("mcp")

from mcp.client.session import ClientSession  # noqa: E402
from mcp.client.stdio import StdioServerParameters, stdio_client  # noqa: E402

from minilang import mcp_server  # noqa: E402


class TestTools:
    def test_run_program_success(self):
        result = mcp_server.run_program("print(6 * 7);")
        assert result["ok"] and result["output"] == ["42"]

    def test_run_program_reports_structured_error(self):
        result = mcp_server.run_program("print(y);")
        assert result["error"]["stage"] == "semantic"
        assert "program.ml:1:7" in result["diagnostic"]

    def test_check_program(self):
        assert mcp_server.check_program("let a = 1;")["ok"]
        failed = mcp_server.check_program("let = 1;")
        assert failed["error"]["stage"] == "syntax"

    def test_check_does_not_execute(self):
        assert mcp_server.check_program("let z = 0; print(1 / z);")["ok"]

    def test_compile_program(self):
        result = mcp_server.compile_program("let a = 1 + 2;")
        assert result["three_address_code"] == ["t1 = 1 + 2", "a = t1"]
        assert mcp_server.compile_program("print(q);")["ok"] is False

    @pytest.mark.parametrize("tool", ["run_program", "check_program", "compile_program"])
    def test_oversized_input_is_rejected(self, tool):
        huge = "print(1);" * (mcp_server.MAX_SOURCE_CHARS // 9 + 1)
        result = getattr(mcp_server, tool)(huge)
        assert result["error"]["stage"] == "input"

    def test_spec_resource(self):
        assert mcp_server.language_spec().startswith("# MiniLang Language Specification")


async def exercise_server_over_stdio():
    params = StdioServerParameters(command=sys.executable, args=["-m", "minilang.mcp_server"])
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        call = await session.call_tool("run_program", {"code": "print(1 + 1);"})
        resources = await session.list_resources()
        spec = await session.read_resource("minilang://spec")
        return tools, call, resources, spec


def test_stdio_round_trip():
    # Arrange / Act: launch the server as a subprocess, talk MCP to it.
    tools, call, resources, spec = anyio.run(exercise_server_over_stdio)

    # Assert
    names = {t.name for t in tools.tools}
    assert names == {"run_program", "check_program", "compile_program"}
    assert all(t.annotations.read_only_hint for t in tools.tools)
    payload = call.structured_content or json.loads(call.content[0].text)
    assert payload["output"] == ["2"]
    assert [str(r.uri) for r in resources.resources] == ["minilang://spec"]
    assert "MiniLang" in spec.contents[0].text

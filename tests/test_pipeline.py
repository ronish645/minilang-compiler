"""The public pipeline API used by the CLI, the LLM agent and the MCP server."""

from minilang.pipeline import compile_source, run_source
from minilang.runtime import RuntimeLimits


class TestRunSource:
    def test_success(self):
        result = run_source("print(6 * 7);")
        assert result.ok
        assert result.output == ["42"]
        assert result.error is None and result.diagnostic is None

    def test_compile_error_is_returned_not_raised(self):
        result = run_source("print(y);", filename="t.ml")
        assert not result.ok
        assert result.is_compile_error
        assert result.error["stage"] == "semantic"
        assert result.diagnostic.startswith("error[semantic]")
        assert "t.ml:1:7" in result.diagnostic

    def test_runtime_error_keeps_partial_output(self):
        result = run_source("print(1); let z = 0; print(1 / z);")
        assert not result.ok
        assert not result.is_compile_error
        assert result.output == ["1"]

    def test_limits_are_applied(self):
        result = run_source("while (true) { }", limits=RuntimeLimits(max_steps=10))
        assert "step limit" in result.error["message"]

    def test_to_dict_round_trips_fields(self):
        assert run_source("print(1);").to_dict() == {
            "ok": True,
            "output": ["1"],
            "error": None,
            "diagnostic": None,
        }


class TestCompileSource:
    def test_execute_false_skips_running(self):
        result = compile_source("let z = 0; print(1 / z);", execute=False)
        assert "execution_output" not in result
        assert result["three_address_code"]

    def test_lexical_table_lists_identifiers_and_constants(self):
        table = compile_source("let total = 5;")["lexical_table"]
        assert table["identifiers"] == ["total"]
        assert table["constants"] == ["5"]

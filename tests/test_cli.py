"""CLI behavior: output streams, --json, and exit codes."""

import io
import json

import pytest

from minilang.cli import (
    EXIT_COMPILE_ERROR,
    EXIT_OK,
    EXIT_RUNTIME_ERROR,
    EXIT_USAGE_ERROR,
    main,
)


@pytest.fixture
def program(tmp_path):
    def write(source: str) -> str:
        path = tmp_path / "prog.ml"
        path.write_text(source)
        return str(path)

    return write


class TestRun:
    def test_prints_program_output(self, program, capsys):
        assert main(["run", program("print(1 + 2);")]) == EXIT_OK
        assert capsys.readouterr().out == "3\n"

    def test_compile_error_goes_to_stderr_with_exit_1(self, program, capsys):
        assert main(["run", program("print(y);")]) == EXIT_COMPILE_ERROR
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "error[semantic]" in captured.err
        assert "prog.ml:1:7" in captured.err

    def test_runtime_error_exits_3_and_keeps_partial_output(self, program, capsys):
        code = main(["run", program("print(1);\nlet z = 0;\nprint(1 / z);")])
        captured = capsys.readouterr()
        assert code == EXIT_RUNTIME_ERROR
        assert captured.out == "1\n"
        assert "division by zero" in captured.err

    def test_json_output(self, program, capsys):
        main(["run", program("print(y);"), "--json"])
        data = json.loads(capsys.readouterr().out)
        assert data["ok"] is False
        assert data["error"]["stage"] == "semantic"
        assert "^" in data["diagnostic"]

    def test_reads_stdin_when_file_is_dash(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", io.StringIO('print("piped");'))
        assert main(["run", "-"]) == EXIT_OK
        assert capsys.readouterr().out == "piped\n"

    def test_missing_file_is_a_usage_error(self, tmp_path, capsys):
        assert main(["run", str(tmp_path / "nope.ml")]) == EXIT_USAGE_ERROR
        assert "cannot read" in capsys.readouterr().err


class TestCheck:
    def test_valid_program(self, program, capsys):
        assert main(["check", program("let a = 1;")]) == EXIT_OK
        assert capsys.readouterr().out.endswith(": ok\n")

    def test_does_not_execute_the_program(self, program, capsys):
        # A runtime error must not be reported by a static check.
        assert main(["check", program("let z = 0; print(1 / z);")]) == EXIT_OK

    def test_invalid_program(self, program, capsys):
        assert main(["check", program("let = 1;")]) == EXIT_COMPILE_ERROR
        assert "error[syntax]" in capsys.readouterr().err

    @pytest.mark.parametrize(("source", "ok"), [("let a = 1;", True), ("print(q);", False)])
    def test_json(self, program, capsys, source, ok):
        main(["check", program(source), "--json"])
        assert json.loads(capsys.readouterr().out)["ok"] is ok


class TestCompile:
    def test_emits_selected_stages_only(self, program, capsys):
        assert main(["compile", program("let a = 1 + 2;"), "--emit", "tac"]) == EXIT_OK
        out = capsys.readouterr().out
        assert "== THREE-ADDRESS CODE ==" in out
        assert "t1 = 1 + 2" in out
        assert "== TOKENS ==" not in out

    def test_emits_all_stages_by_default(self, program, capsys):
        main(["compile", program("let a = 1;")])
        out = capsys.readouterr().out
        for title in ("TOKENS", "AST", "THREE-ADDRESS CODE", "PSEUDO-ASSEMBLY"):
            assert f"== {title} ==" in out

    def test_json(self, program, capsys):
        main(["compile", program("let a = 1;"), "--json", "--emit", "tac", "asm"])
        data = json.loads(capsys.readouterr().out)
        assert data == {"ok": True, "tac": ["a = 1"], "asm": ["STORE a, 1"]}

    def test_compile_error(self, program, capsys):
        assert main(["compile", program("print(q);")]) == EXIT_COMPILE_ERROR
        assert "error[semantic]" in capsys.readouterr().err

    def test_compile_error_json(self, program, capsys):
        assert main(["compile", program("print(q);"), "--json"]) == EXIT_COMPILE_ERROR
        assert json.loads(capsys.readouterr().out)["error"]["stage"] == "semantic"


def test_demo_runs_the_sample_program(capsys):
    assert main(["demo"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "== OUTPUT ==\n30\ngreater than twenty\n0\n1\n2\n" in out


def test_no_command_is_a_usage_error():
    with pytest.raises(SystemExit) as info:
        main([])
    assert info.value.code == EXIT_USAGE_ERROR

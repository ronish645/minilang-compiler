"""Shared pytest helpers."""

import pytest

from minilang.pipeline import compile_source


def run_program(source: str) -> list[str]:
    """Compile and execute a MiniLang program, returning its printed lines."""
    return compile_source(source)["execution_output"]


@pytest.fixture
def run():
    return run_program

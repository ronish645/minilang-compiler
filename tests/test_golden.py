"""Golden (snapshot) tests: every program in tests/programs must reproduce the
tokens, AST, TAC, pseudo-assembly and output recorded in tests/golden.

To intentionally change compiler output, regenerate snapshots with:
    python -m tests.update_golden
and review the diff in git before committing.
"""

import json
from pathlib import Path

import pytest

from minilang.pipeline import compile_source

PROGRAMS_DIR = Path(__file__).parent / "programs"
GOLDEN_DIR = Path(__file__).parent / "golden"
PROGRAMS = sorted(PROGRAMS_DIR.glob("*.ml"))


@pytest.mark.parametrize("program", PROGRAMS, ids=[p.stem for p in PROGRAMS])
def test_program_matches_golden_snapshot(program: Path) -> None:
    # Arrange
    expected = json.loads((GOLDEN_DIR / f"{program.stem}.json").read_text())

    # Act
    result = compile_source(program.read_text())

    # Assert (each stage separately, so a failure names the stage that changed)
    for stage, expected_value in expected.items():
        assert result[stage] == expected_value, f"{program.name}: '{stage}' changed"


def test_every_program_has_a_snapshot() -> None:
    missing = [p.name for p in PROGRAMS if not (GOLDEN_DIR / f"{p.stem}.json").exists()]
    assert not missing, f"run `python -m tests.update_golden` for: {missing}"

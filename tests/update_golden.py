"""Regenerate golden snapshots: python -m tests.update_golden"""

import json
from pathlib import Path

from minilang.pipeline import compile_source

SNAPSHOT_KEYS = ("tokens", "ast", "three_address_code", "pseudo_code", "execution_output")
TESTS_DIR = Path(__file__).parent


def main() -> None:
    for program in sorted((TESTS_DIR / "programs").glob("*.ml")):
        result = compile_source(program.read_text())
        snapshot = {key: result[key] for key in SNAPSHOT_KEYS}
        out = TESTS_DIR / "golden" / f"{program.stem}.json"
        out.write_text(json.dumps(snapshot, indent=2) + "\n")
        print(f"wrote {out.relative_to(TESTS_DIR.parent)}")


if __name__ == "__main__":
    main()

"""Every ```js example in the docs must compile and run, so docs can't drift."""

import re
from pathlib import Path

import pytest

from minilang.pipeline import run_source

ROOT = Path(__file__).parent.parent
DOCS = [ROOT / "README.md", ROOT / "docs" / "LANGUAGE_SPEC.md"]
EXAMPLES = [
    pytest.param(block, id=f"{doc.name}#{i}")
    for doc in DOCS
    for i, block in enumerate(re.findall(r"```js\n(.*?)```", doc.read_text(), re.S))
]


@pytest.mark.parametrize("source", EXAMPLES)
def test_documented_example_runs(source):
    result = run_source(source)
    assert result.ok, result.diagnostic

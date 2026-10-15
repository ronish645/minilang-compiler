"""Exporting benchmark results as JSON for the showcase site."""

import json

import pytest

from bench.agent import Episode, RunRecord
from bench.export import (
    RUNS,
    build_episodes,
    build_summary,
    error_pattern,
    export,
    rate_json,
)
from bench.feedback import DIAGNOSTIC, HINT, ONESHOT
from bench.llm.base import Usage
from bench.report import Rate


def make_episode(
    model="claude-haiku",
    outcome="passed",
    runs=(),
    condition=DIAGNOSTIC,
    task="gcd",
    tier=2,
    error=None,
):
    return Episode(
        model,
        task,
        tier,
        condition,
        0,
        outcome=outcome,
        code="print(1);",
        runs=[RunRecord(ok, None if ok else "syntax") for ok in runs],
        usage=Usage(1_000_000, 100_000),
        seconds=2.0,
        error=error,
    )


class TestRateJson:
    def test_includes_counts_value_and_interval(self):
        data = rate_json(Rate(5, 10))
        assert data["hits"] == 5 and data["total"] == 10
        assert data["value"] == 0.5
        assert 0 < data["low"] < 0.5 < data["high"] < 1

    def test_empty_rate_has_no_value(self):
        assert rate_json(Rate(0, 0)) == {
            "hits": 0,
            "total": 0,
            "value": None,
            "low": None,
            "high": None,
        }


class TestErrorPattern:
    @pytest.mark.parametrize(
        ("error", "pattern"),
        [
            ("Syntax error at line 3, col 9: expected ';' but found '.'",
             "expected ';' but found '.'"),
            ("Semantic error at line 1, col 1: variable 'totl' used before declaration",
             "variable '…' used before declaration"),
            (None, None),
            ("", None),
        ],
    )  # fmt: skip
    def test_strips_positions_and_names(self, error, pattern):
        assert error_pattern(error) == pattern


class TestSummary:
    def test_cells_per_model_and_condition(self):
        episodes = {
            "v2": [
                make_episode(outcome="passed", condition=ONESHOT),
                make_episode(outcome="compile_error", condition=ONESHOT),
                make_episode(
                    model="gpt-luna", outcome="passed", condition=HINT, runs=[False, True]
                ),
            ]
        }
        summary = build_summary(episodes)
        cell = next(
            c
            for c in summary["cells"]
            if c["model"] == "claude-haiku" and c["condition"] == ONESHOT
        )
        assert cell["run"] == "v2"
        assert cell["pass"]["hits"] == 1 and cell["pass"]["total"] == 2

    def test_model_stats_include_cost_and_outcomes(self):
        episodes = {"v2": [make_episode(), make_episode(outcome="no_code")]}
        stats = build_summary(episodes)["model_stats"][0]
        # Haiku: 1M input at $0.10 + 100K output at $0.50 per episode = $0.15
        assert stats["cost_usd"] == pytest.approx(0.30)
        assert stats["cost_per_solve"] == pytest.approx(0.30)
        assert stats["outcomes"] == {"passed": 1, "no_code": 1}

    def test_repair_is_pooled_per_condition(self):
        episodes = {
            "v2": [
                make_episode(runs=[False, True], outcome="passed"),
                make_episode(model="gpt-luna", runs=[False], outcome="compile_error"),
            ]
        }
        repair = build_summary(episodes)["repair"]
        row = next(r for r in repair if r["condition"] == DIAGNOSTIC)
        assert row["rate"]["hits"] == 1 and row["rate"]["total"] == 2

    def test_totals_and_metadata(self):
        episodes = {"v2": [make_episode()], "v21-tier5": [make_episode(tier=5)]}
        summary = build_summary(episodes)
        assert summary["totals"]["episodes"] == 2
        assert [r["id"] for r in summary["runs"]] == ["v2", "v21-tier5"]
        assert {m["id"] for m in summary["models"]} >= {"claude-haiku", "qwen-3b-local"}
        assert {c["id"] for c in summary["conditions"]} == {
            "oneshot",
            "opaque",
            "message",
            "diagnostic",
            "hint",
        }

    def test_error_patterns_are_counted_per_model(self):
        error = "Syntax error at line 1, col 2: expected ';' but found '.'"
        episodes = {
            "v2": [
                make_episode(outcome="compile_error", error=error),
                make_episode(outcome="compile_error", error=error.replace("1, col 2", "4, col 8")),
            ]
        }
        patterns = build_summary(episodes)["error_patterns"]
        assert patterns == [
            {
                "run": "v2",
                "model": "claude-haiku",
                "pattern": "expected ';' but found '.'",
                "count": 2,
            }
        ]


def test_episodes_are_slim_and_identified():
    rows = build_episodes({"v2": [make_episode(runs=[False, True])]})
    assert rows[0]["id"] == "v2/claude-haiku/gcd/diagnostic/0"
    assert rows[0]["runs"] == [{"ok": False, "stage": "syntax"}, {"ok": True, "stage": None}]
    assert rows[0]["cost_usd"] == pytest.approx(0.15)
    assert "usage" not in rows[0]


def test_export_writes_all_files_from_real_results(tmp_path):
    export(tmp_path)
    summary = json.loads((tmp_path / "summary.json").read_text())
    episodes = json.loads((tmp_path / "episodes.json").read_text())
    tasks = json.loads((tmp_path / "tasks.json").read_text())
    assert summary["totals"]["episodes"] == len(episodes)
    assert [r["episodes"] for r in summary["runs"]] == [640, 250]
    assert [r["id"] for r in summary["runs"]] == [r.id for r in RUNS]
    assert all("reference" not in t for t in tasks)  # reference solutions stay hidden
    assert {t["tier"] for t in tasks} == {1, 2, 3, 4, 5}

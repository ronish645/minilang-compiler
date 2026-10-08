"""Runner orchestration, caching and report statistics (no API calls)."""

import pytest

from bench import runner as runner_module
from bench.agent import AgentLimits, Episode, RunRecord
from bench.config import load_models
from bench.feedback import DIAGNOSTIC, ONESHOT
from bench.llm.base import Usage
from bench.report import Rate, build_report, pass_rate, repair_rate
from bench.runner import EpisodeCache, Job, Runner, build_jobs, main
from bench.tasks import load_tasks
from tests.bench.fakes import FakeSession, factory_for, submit

MODELS = load_models()
TASKS = load_tasks()


def make_episode(model="claude-haiku", outcome="passed", runs=(), condition=DIAGNOSTIC, task="gcd"):
    return Episode(
        model, task, 2, condition, 0, outcome=outcome, runs=[RunRecord(ok, None) for ok in runs],
        usage=Usage(1000, 100), seconds=1.0,
    )  # fmt: skip


class TestJobs:
    def test_matrix_size(self):
        jobs = build_jobs(MODELS[:2], TASKS[:3], [ONESHOT, DIAGNOSTIC], samples=2)
        assert len(jobs) == 2 * 3 * 2 * 2

    def test_cache_key_changes_with_inputs(self):
        job = Job(MODELS[0], TASKS[0], DIAGNOSTIC, 0)
        key = job.cache_key("spec", AgentLimits())
        assert key == job.cache_key("spec", AgentLimits())
        assert key != job.cache_key("spec v2", AgentLimits())
        assert key != Job(MODELS[0], TASKS[0], DIAGNOSTIC, 1).cache_key("spec", AgentLimits())
        assert key != job.cache_key("spec", AgentLimits(max_runs=3))


class TestCache:
    def test_round_trip(self, tmp_path):
        cache = EpisodeCache(tmp_path)
        episode = make_episode(runs=(False, True))
        cache.put("k", episode)
        assert cache.get("k") == episode

    def test_api_errors_are_not_cached(self, tmp_path):
        cache = EpisodeCache(tmp_path)
        cache.put("k", make_episode(outcome="api_error"))
        assert cache.get("k") is None

    def test_disabled_cache_never_hits(self, tmp_path):
        EpisodeCache(tmp_path).put("k", make_episode())
        assert EpisodeCache(tmp_path, enabled=False).get("k") is None


def test_runner_runs_jobs_and_uses_cache(tmp_path, monkeypatch):
    calls = []

    def fake_factory(model):
        calls.append(model.id)
        task_code = "print(6); print(1); print(25);"
        return factory_for(FakeSession([submit(task_code)]))

    monkeypatch.setattr(runner_module, "session_factory", fake_factory)
    gcd = [t for t in TASKS if t.id == "gcd"]
    jobs = build_jobs(MODELS[:1], gcd, [DIAGNOSTIC], samples=1)
    runner = Runner("spec", AgentLimits(), EpisodeCache(tmp_path / "cache"), workers=2)

    first = runner.run(jobs, tmp_path / "out" / "episodes.jsonl")
    second = runner.run(jobs, tmp_path / "out" / "episodes.jsonl")

    assert [e.outcome for e in first] == ["passed"]
    assert second == first
    assert len(calls) == 1  # the second run was served from cache
    assert (tmp_path / "out" / "episodes.jsonl").read_text().count("\n") == 1


def test_dry_run_makes_no_calls(monkeypatch, capsys):
    monkeypatch.setattr(runner_module, "session_factory", lambda m: pytest.fail("API used"))
    assert main(["--dry-run", "--models", "qwen-3b-local", "--tiers", "1"]) == 0
    out = capsys.readouterr().out
    assert "32 episodes" in out  # 8 tier-1 tasks x 4 conditions


def test_unknown_model_is_an_error():
    with pytest.raises(SystemExit, match="unknown models"):
        main(["--dry-run", "--models", "nope"])


class TestStatistics:
    def test_rate_and_wilson_interval(self):
        r = Rate(8, 10)
        assert r.value == 0.8
        low, high = r.wilson_interval()
        assert 0.44 < low < 0.5 and 0.94 < high < 0.97
        assert Rate(0, 0).format() == "–"

    def test_repair_rate_counts_only_failed_first_runs(self):
        episodes = [
            make_episode(runs=(False, True)),  # repaired
            make_episode(outcome="compile_error", runs=(False, False)),  # not repaired
            make_episode(runs=(True,)),  # first run fine: excluded
            make_episode(runs=()),  # never ran: excluded
        ]
        assert repair_rate(episodes) == Rate(1, 2)
        assert pass_rate(episodes) == Rate(3, 4)


def test_report_excludes_api_errors_and_has_all_sections():
    episodes = [
        make_episode(runs=(False, True)),
        make_episode(condition=ONESHOT),
        make_episode(model="gpt-luna", outcome="wrong_output", runs=(True,)),
        make_episode(model="gpt-luna", outcome="api_error"),
    ]
    report = build_report(episodes, "test")
    assert "3 graded episodes" in report
    assert "1 API-error episodes excluded" in report
    for heading in ("Pass rate by condition", "Repair rate", "tier", "cost", "Outcomes", "Hardest"):
        assert heading in report

"""Run the benchmark matrix: models x tasks x conditions x samples.

    python -m bench.runner --dry-run                    # plan + cost estimate, no API calls
    python -m bench.runner --models claude-haiku --conditions oneshot diagnostic
    python -m bench.runner --tiers 3 --samples 3

Every finished episode is cached under bench/.cache/, keyed by everything
that affects it (model, task, condition, sample, prompt, limits), so an
interrupted or repeated run only pays for episodes it hasn't done yet.
Episodes are written to bench/results/<run-name>/episodes.jsonl.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from bench.agent import AgentLimits, Episode, run_episode
from bench.config import BENCH_DIR, ModelConfig, load_models
from bench.feedback import CONDITIONS, ONESHOT
from bench.llm.base import Usage
from bench.llm.registry import session_factory
from bench.prompts import fingerprint, load_spec, system_prompt
from bench.tasks import Task, load_tasks

CACHE_DIR = BENCH_DIR / ".cache"
RESULTS_DIR = BENCH_DIR / "results"

# Rough per-episode token guesses for --dry-run (no caching assumed: an upper bound).
CHARS_PER_TOKEN = 4
ESTIMATED_TOOL_TURNS = 3
ESTIMATED_OUTPUT_TOKENS_PER_TURN = 800  # includes thinking
ESTIMATED_HISTORY_TOKENS_PER_TURN = 500


@dataclass(frozen=True)
class Job:
    model: ModelConfig
    task: Task
    condition: str
    sample: int

    def cache_key(self, spec: str, limits: AgentLimits) -> str:
        uses_tools = self.condition != ONESHOT
        return fingerprint(
            self.model.provider,
            self.model.model,
            str(self.model.effort),
            json.dumps(self.model.extra, sort_keys=True),
            self.task.id,
            self.task.user_message(),
            self.condition,
            str(self.sample),
            system_prompt(spec, uses_tools, limits.max_runs),
            f"{limits.max_runs}/{limits.max_model_turns}",
        )


def build_jobs(
    models: list[ModelConfig], tasks: list[Task], conditions: list[str], samples: int
) -> list[Job]:
    return [
        Job(model, task, condition, sample)
        for model in models
        for condition in conditions
        for task in tasks
        for sample in range(samples)
    ]


def estimate_usage(job: Job, spec: str) -> Usage:
    system_tokens = len(spec) // CHARS_PER_TOKEN
    turns = 1 if job.condition == ONESHOT else ESTIMATED_TOOL_TURNS
    input_tokens = sum(system_tokens + i * ESTIMATED_HISTORY_TOKENS_PER_TURN for i in range(turns))
    return Usage(input_tokens, turns * ESTIMATED_OUTPUT_TOKENS_PER_TURN)


class EpisodeCache:
    def __init__(self, directory: Path, enabled: bool = True):
        self.directory = directory
        self.enabled = enabled

    def get(self, key: str) -> Episode | None:
        path = self.directory / f"{key}.json"
        if not self.enabled or not path.exists():
            return None
        return Episode.from_dict(json.loads(path.read_text()))

    def put(self, key: str, episode: Episode) -> None:
        # Infrastructure failures are not cached, so a rerun retries them.
        if episode.outcome == "api_error":
            return
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / f"{key}.json").write_text(json.dumps(episode.to_dict()))


class Runner:
    def __init__(self, spec: str, limits: AgentLimits, cache: EpisodeCache, workers: int):
        self.spec = spec
        self.limits = limits
        self.cache = cache
        self.workers = workers
        self.lock = threading.Lock()
        self.semaphores: dict[str, threading.Semaphore] = {}

    def run_job(self, job: Job) -> tuple[Episode, bool]:
        key = job.cache_key(self.spec, self.limits)
        cached = self.cache.get(key)
        if cached is not None:
            return cached, True
        with self.semaphores[job.model.id]:  # per-model concurrency cap
            episode = run_episode(
                session_factory(job.model),
                job.model.id,
                job.task,
                job.condition,
                self.spec,
                job.sample,
                self.limits,
            )
        self.cache.put(key, episode)
        return episode, False

    def run(self, jobs: list[Job], out_path: Path) -> list[Episode]:
        for job in jobs:
            self.semaphores.setdefault(job.model.id, threading.Semaphore(job.model.max_concurrency))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        episodes: list[Episode] = []
        with open(out_path, "w") as out, ThreadPoolExecutor(self.workers) as pool:
            futures = [pool.submit(self.run_job, job) for job in jobs]
            for done, future in enumerate(as_completed(futures), start=1):
                episode, from_cache = future.result()
                with self.lock:
                    episodes.append(episode)
                    out.write(json.dumps(episode.to_dict()) + "\n")
                    out.flush()
                    print_progress(done, len(jobs), episode, from_cache)
        return episodes


def print_progress(done: int, total: int, episode: Episode, from_cache: bool) -> None:
    mark = "PASS" if episode.passed else episode.outcome.upper()
    source = " (cached)" if from_cache else f" {episode.seconds:.1f}s"
    print(
        f"[{done:>4}/{total}] {episode.model_id:<15} {episode.condition:<10} "
        f"{episode.task_id:<18} {mark}{source}",
        flush=True,
    )


def select(items: list, wanted: list[str] | None, key, label: str) -> list:
    if not wanted:
        return items
    unknown = set(wanted) - {key(i) for i in items}
    if unknown:
        raise SystemExit(f"unknown {label}: {sorted(unknown)}")
    return [i for i in items if key(i) in wanted]


def print_plan(jobs: list[Job], spec: str, skipped: list[ModelConfig]) -> None:
    for model in skipped:
        print(f"skipping {model.id}: {model.key_env} is not set")
    per_model = Counter(job.model.id for job in jobs)
    costs: Counter[str] = Counter()
    for job in jobs:
        costs[job.model.id] += job.model.price.cost(estimate_usage(job, spec))
    print(f"{len(jobs)} episodes")
    for model_id, count in per_model.items():
        print(f"  {model_id:<15} {count:>4} episodes   ~${costs[model_id]:.2f} (upper bound)")
    print(f"  {'total':<15} {len(jobs):>4} episodes   ~${sum(costs.values()):.2f}")


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m bench.runner", description=__doc__.split("\n")[0]
    )
    parser.add_argument("--models", nargs="+", help="model ids from models.yaml (default: all)")
    parser.add_argument("--tasks", nargs="+", help="task ids (default: all)")
    parser.add_argument("--tiers", nargs="+", type=int, help="only tasks in these tiers")
    parser.add_argument("--conditions", nargs="+", choices=CONDITIONS, default=list(CONDITIONS))
    parser.add_argument("--samples", type=int, default=1, help="repeats per task (default 1)")
    parser.add_argument("--workers", type=int, default=8, help="parallel episodes")
    parser.add_argument("--max-runs", type=int, default=AgentLimits.max_runs)
    parser.add_argument("--run-name", default="latest", help="results/<run-name>/")
    parser.add_argument("--no-cache", action="store_true", help="ignore cached episodes")
    parser.add_argument("--dry-run", action="store_true", help="show the plan and estimated cost")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_dotenv(BENCH_DIR.parent / ".env")
    args = parse_args(argv)

    models = select(load_models(), args.models, lambda m: m.id, "models")
    available = [m for m in models if m.is_available()]
    skipped = [m for m in models if not m.is_available()]
    tasks = select(load_tasks(), args.tasks, lambda t: t.id, "tasks")
    if args.tiers:
        tasks = [t for t in tasks if t.tier in args.tiers]

    spec = load_spec()
    jobs = build_jobs(available, tasks, args.conditions, args.samples)
    print_plan(jobs, spec, skipped)
    if args.dry_run or not jobs:
        return 0

    limits = AgentLimits(max_runs=args.max_runs)
    runner = Runner(spec, limits, EpisodeCache(CACHE_DIR, not args.no_cache), args.workers)
    out_path = RESULTS_DIR / args.run_name / "episodes.jsonl"
    episodes = runner.run(jobs, out_path)

    api_errors = sum(e.outcome == "api_error" for e in episodes)
    print(f"\nwrote {out_path.relative_to(BENCH_DIR.parent)}")
    if api_errors:
        print(f"{api_errors} episode(s) hit API errors; rerun to retry them (others are cached)")
    print(f"summarize with: python -m bench.report {args.run_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

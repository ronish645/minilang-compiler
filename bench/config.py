"""Benchmark configuration: which models to run and what they cost."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from bench.llm.base import Usage

BENCH_DIR = Path(__file__).parent
DEFAULT_MODELS_FILE = BENCH_DIR / "models.yaml"

PROVIDER_KEY_ENV = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "ollama": None,  # local, no key
}
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"
TOKENS_PER_MILLION = 1_000_000
# Prompt-cache pricing relative to the base input price (same for both
# providers' current models; OpenAI doesn't report cache writes, so OpenAI
# runs slightly under-count cost).
CACHE_READ_MULTIPLIER = 0.1
CACHE_WRITE_MULTIPLIER = 1.25


@dataclass(frozen=True)
class Price:
    input: float  # USD per 1M input tokens
    output: float  # USD per 1M output tokens

    def cost(self, usage: Usage) -> float:
        input_cost = self.input * (
            usage.input_tokens
            + usage.cache_read_tokens * CACHE_READ_MULTIPLIER
            + usage.cache_write_tokens * CACHE_WRITE_MULTIPLIER
        )
        return (input_cost + usage.output_tokens * self.output) / TOKENS_PER_MILLION


@dataclass(frozen=True)
class ModelConfig:
    id: str  # short name used in results, e.g. "claude-haiku"
    provider: str  # "anthropic" | "openai" | "ollama"
    model: str  # provider's model ID
    tier: str
    price: Price
    effort: str | None = None  # reasoning effort (Anthropic and OpenAI)
    max_concurrency: int = 4
    extra: dict[str, Any] = field(default_factory=dict)  # passed through to the API call

    @property
    def key_env(self) -> str | None:
        return PROVIDER_KEY_ENV[self.provider]

    def is_available(self) -> bool:
        return self.key_env is None or bool(os.environ.get(self.key_env))


def parse_model(raw: dict[str, Any]) -> ModelConfig:
    missing = {"id", "provider", "model", "tier", "price"} - raw.keys()
    if missing:
        raise ValueError(f"model entry {raw.get('id', raw)!r} is missing {sorted(missing)}")
    if raw["provider"] not in PROVIDER_KEY_ENV:
        raise ValueError(
            f"model {raw['id']!r}: unknown provider {raw['provider']!r} "
            f"(expected one of {sorted(PROVIDER_KEY_ENV)})"
        )
    return ModelConfig(
        id=raw["id"],
        provider=raw["provider"],
        model=raw["model"],
        tier=raw["tier"],
        price=Price(**raw["price"]),
        effort=raw.get("effort"),
        max_concurrency=int(raw.get("max_concurrency", 4)),
        extra=raw.get("extra", {}),
    )


def load_models(path: Path = DEFAULT_MODELS_FILE) -> list[ModelConfig]:
    data = yaml.safe_load(path.read_text())
    models = [parse_model(entry) for entry in data["models"]]
    ids = [m.id for m in models]
    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates:
        raise ValueError(f"duplicate model ids in {path.name}: {sorted(duplicates)}")
    return models

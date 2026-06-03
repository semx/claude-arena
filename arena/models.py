"""Core data models for routing decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ModelProfile:
    """Commercial and capability metadata for one model tier."""

    name: str
    tier: str
    input_cost_per_mtok: float
    output_cost_per_mtok: float
    max_context_tokens: int
    strengths: tuple[str, ...] = ()

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        input_cost = (input_tokens / 1_000_000) * self.input_cost_per_mtok
        output_cost = (output_tokens / 1_000_000) * self.output_cost_per_mtok
        return round(input_cost + output_cost, 6)


@dataclass(frozen=True, slots=True)
class PromptFeatures:
    """Feature vector extracted from a prompt before routing."""

    prompt: str
    token_estimate: int
    expected_output_tokens: int
    complexity: int
    domains: tuple[str, ...] = ()
    risk_flags: tuple[str, ...] = ()
    requires_tools: bool = False

    @property
    def band(self) -> str:
        if self.complexity >= 72:
            return "high"
        if self.complexity >= 38:
            return "medium"
        return "low"


@dataclass(frozen=True, slots=True)
class RouteDecision:
    """Final model selection and the information needed to audit it."""

    model: ModelProfile
    features: PromptFeatures
    estimated_cost_usd: float
    rationale: tuple[str, ...] = field(default_factory=tuple)
    fallback_model: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "model": self.model.name,
            "tier": self.model.tier,
            "estimated_cost_usd": self.estimated_cost_usd,
            "complexity": self.features.complexity,
            "band": self.features.band,
            "domains": list(self.features.domains),
            "risk_flags": list(self.features.risk_flags),
            "requires_tools": self.features.requires_tools,
            "fallback_model": self.fallback_model,
            "rationale": list(self.rationale),
        }


DEFAULT_MODEL_PROFILES: tuple[ModelProfile, ...] = (
    ModelProfile(
        name="claude-3-haiku",
        tier="haiku",
        input_cost_per_mtok=0.25,
        output_cost_per_mtok=1.25,
        max_context_tokens=200_000,
        strengths=("classification", "simple edits", "summaries"),
    ),
    ModelProfile(
        name="claude-3-sonnet",
        tier="sonnet",
        input_cost_per_mtok=3.0,
        output_cost_per_mtok=15.0,
        max_context_tokens=200_000,
        strengths=("code review", "debugging", "analysis"),
    ),
    ModelProfile(
        name="claude-3-opus",
        tier="opus",
        input_cost_per_mtok=15.0,
        output_cost_per_mtok=75.0,
        max_context_tokens=200_000,
        strengths=("architecture", "incident analysis", "complex reasoning"),
    ),
)

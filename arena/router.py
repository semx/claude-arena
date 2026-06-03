"""Cost-aware routing policy."""

from __future__ import annotations

from dataclasses import dataclass

from arena.classifier import PromptClassifier
from arena.models import DEFAULT_MODEL_PROFILES, ModelProfile, RouteDecision


TIER_ORDER: tuple[str, ...] = ("haiku", "sonnet", "opus")


@dataclass(frozen=True, slots=True)
class RouterConfig:
    """Runtime policy for model selection."""

    max_cost_usd: float = 0.06
    prefer_capability: bool = True
    allow_downgrade: bool = True


class CostAwareRouter:
    """Select a model tier from prompt complexity and budget constraints."""

    def __init__(
        self,
        profiles: tuple[ModelProfile, ...] = DEFAULT_MODEL_PROFILES,
        classifier: PromptClassifier | None = None,
        config: RouterConfig | None = None,
    ) -> None:
        self.profiles = tuple(profiles)
        self.classifier = classifier or PromptClassifier()
        self.config = config or RouterConfig()
        self._by_tier = {profile.tier: profile for profile in self.profiles}

        missing = set(TIER_ORDER) - set(self._by_tier)
        if missing:
            raise ValueError(f"missing model tiers: {', '.join(sorted(missing))}")

    def route(self, prompt: str) -> RouteDecision:
        features = self.classifier.classify(prompt)
        target_tier = self._tier_for_complexity(features.complexity)
        selected = self._by_tier[target_tier]
        rationale = [f"{features.band} complexity prompt"]

        if features.requires_tools:
            rationale.append("tool context requested")
        if features.risk_flags:
            rationale.append("risk terms detected")

        estimated_cost = selected.estimate_cost(
            features.token_estimate,
            features.expected_output_tokens,
        )
        fallback_model: str | None = None

        if estimated_cost > self.config.max_cost_usd and self.config.allow_downgrade:
            downgraded = self._downgrade_until_within_budget(
                selected.tier,
                features.token_estimate,
                features.expected_output_tokens,
            )
            if downgraded.name != selected.name:
                fallback_model = selected.name
                selected = downgraded
                estimated_cost = selected.estimate_cost(
                    features.token_estimate,
                    features.expected_output_tokens,
                )
                rationale.append("downgraded to stay within budget")

        return RouteDecision(
            model=selected,
            features=features,
            estimated_cost_usd=estimated_cost,
            rationale=tuple(rationale),
            fallback_model=fallback_model,
        )

    def _tier_for_complexity(self, complexity: int) -> str:
        if complexity >= 72:
            return "opus"
        if complexity >= 38:
            return "sonnet"
        return "haiku"

    def _downgrade_until_within_budget(
        self,
        tier: str,
        input_tokens: int,
        output_tokens: int,
    ) -> ModelProfile:
        start_index = TIER_ORDER.index(tier)
        for candidate_tier in reversed(TIER_ORDER[: start_index + 1]):
            candidate = self._by_tier[candidate_tier]
            if candidate.estimate_cost(input_tokens, output_tokens) <= self.config.max_cost_usd:
                return candidate
        return self._by_tier["haiku"]

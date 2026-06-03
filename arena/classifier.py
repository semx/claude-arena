"""Prompt feature extraction used by the router."""

from __future__ import annotations

import math
import re

from arena.models import PromptFeatures


DOMAIN_TERMS: dict[str, tuple[str, ...]] = {
    "code": ("python", "typescript", "diff", "merge request", "repository", "refactor"),
    "infrastructure": ("terraform", "helm", "kubernetes", "ansible", "docker", "deploy"),
    "incident": ("incident", "outage", "logs", "trace", "root cause", "postmortem"),
    "security": ("oauth", "token", "secret", "credential", "rbac", "policy"),
    "data": ("sql", "sqlite", "schema", "migration", "analytics", "dataset"),
}

RISK_TERMS: tuple[str, ...] = (
    "production",
    "delete",
    "drop table",
    "credential",
    "secret",
    "customer",
    "payment",
    "rollback",
    "migration",
    "incident",
)

COMPLEXITY_TERMS: tuple[str, ...] = (
    "architecture",
    "debug",
    "root cause",
    "race condition",
    "concurrency",
    "security",
    "migration",
    "multi-step",
    "performance",
    "terraform",
    "kubernetes",
    "helm",
    "ansible",
    "policy",
)

TOOL_TERMS: tuple[str, ...] = (
    "repository",
    "logs",
    "traces",
    "deploys",
    "metrics",
    "terraform plan",
    "cluster",
)


class PromptClassifier:
    """Deterministic prompt classifier for repeatable routing tests."""

    def classify(self, prompt: str) -> PromptFeatures:
        normalized = self._normalize(prompt)
        words = self._words(normalized)
        token_estimate = max(1, math.ceil(len(words) * 1.35))

        domains = tuple(
            domain
            for domain, terms in DOMAIN_TERMS.items()
            if any(term in normalized for term in terms)
        )
        risk_flags = tuple(term for term in RISK_TERMS if term in normalized)
        requires_tools = any(term in normalized for term in TOOL_TERMS)

        complexity = self._score_complexity(normalized, words, domains, risk_flags, requires_tools)
        expected_output_tokens = self._expected_output_tokens(complexity, requires_tools)

        return PromptFeatures(
            prompt=prompt,
            token_estimate=token_estimate,
            expected_output_tokens=expected_output_tokens,
            complexity=complexity,
            domains=domains,
            risk_flags=risk_flags,
            requires_tools=requires_tools,
        )

    def _score_complexity(
        self,
        normalized: str,
        words: list[str],
        domains: tuple[str, ...],
        risk_flags: tuple[str, ...],
        requires_tools: bool,
    ) -> int:
        score = 8
        score += min(24, len(words) // 18)
        score += 12 * len(domains)
        score += 7 * len(risk_flags)
        score += 12 if requires_tools else 0
        score += sum(6 for term in COMPLEXITY_TERMS if term in normalized)

        if "incident" in domains and requires_tools:
            score += 10
        if "production" in risk_flags and "infrastructure" in domains:
            score += 6

        if "explain" in normalized or "summarize" in normalized:
            score -= 8
        if "simple" in normalized or "quick" in normalized:
            score -= 6

        return max(0, min(100, score))

    def _expected_output_tokens(self, complexity: int, requires_tools: bool) -> int:
        base = 350
        if complexity >= 72:
            base = 1400
        elif complexity >= 38:
            base = 800
        if requires_tools:
            base += 250
        return base

    def _normalize(self, prompt: str) -> str:
        return re.sub(r"\s+", " ", prompt.strip().lower())

    def _words(self, normalized: str) -> list[str]:
        return re.findall(r"[a-z0-9_./:-]+", normalized)

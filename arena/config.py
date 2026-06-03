"""Configuration helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from arena.models import DEFAULT_MODEL_PROFILES, ModelProfile
from arena.router import RouterConfig


def load_profiles(path: str | Path | None = None) -> tuple[ModelProfile, ...]:
    if path is None:
        return DEFAULT_MODEL_PROFILES

    data = _read_json(path)
    items = data.get("models")
    if not items:
        return DEFAULT_MODEL_PROFILES

    profiles = []
    for item in items:
        profiles.append(
            ModelProfile(
                name=item["name"],
                tier=item["tier"],
                input_cost_per_mtok=float(item["input_cost_per_mtok"]),
                output_cost_per_mtok=float(item["output_cost_per_mtok"]),
                max_context_tokens=int(item["max_context_tokens"]),
                strengths=tuple(item.get("strengths", [])),
            )
        )
    return tuple(profiles)


def load_router_config(path: str | Path | None = None) -> RouterConfig:
    defaults = RouterConfig()
    if path is None:
        return defaults

    data = _read_json(path).get("router", {})
    return RouterConfig(
        max_cost_usd=float(data.get("max_cost_usd", defaults.max_cost_usd)),
        prefer_capability=bool(data.get("prefer_capability", defaults.prefer_capability)),
        allow_downgrade=bool(data.get("allow_downgrade", defaults.allow_downgrade)),
    )


def _read_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data: dict[str, Any] = json.load(handle)
    return data

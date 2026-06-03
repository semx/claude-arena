"""Local tool registry inspired by MCP-style tool envelopes."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any


ToolHandler = Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    required_fields: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ToolResult:
    name: str
    ok: bool
    payload: Mapping[str, Any]
    error: str | None = None


class ToolRegistry:
    """Register and execute internal tools through a stable interface."""

    def __init__(self) -> None:
        self._specs: dict[str, ToolSpec] = {}
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, spec: ToolSpec, handler: ToolHandler) -> None:
        if not spec.name:
            raise ValueError("tool name cannot be empty")
        if spec.name in self._specs:
            raise ValueError(f"tool already registered: {spec.name}")
        self._specs[spec.name] = spec
        self._handlers[spec.name] = handler

    def list_tools(self) -> tuple[ToolSpec, ...]:
        return tuple(sorted(self._specs.values(), key=lambda spec: spec.name))

    def execute(self, name: str, arguments: Mapping[str, Any]) -> ToolResult:
        spec = self._specs.get(name)
        if spec is None:
            return ToolResult(name=name, ok=False, payload={}, error="unknown tool")

        missing = [field for field in spec.required_fields if field not in arguments]
        if missing:
            return ToolResult(
                name=name,
                ok=False,
                payload={},
                error=f"missing required fields: {', '.join(missing)}",
            )

        try:
            payload = self._handlers[name](arguments)
        except Exception as exc:  # pragma: no cover - defensive envelope
            return ToolResult(name=name, ok=False, payload={}, error=str(exc))

        return ToolResult(name=name, ok=True, payload=payload)


def default_registry() -> ToolRegistry:
    """Create a registry with safe read-only demo tools."""

    registry = ToolRegistry()

    registry.register(
        ToolSpec(
            name="repo.diff_summary",
            description="Summarize changed files in a repository diff",
            required_fields=("files",),
        ),
        lambda args: {
            "changed_files": len(args["files"]),
            "files": list(args["files"]),
        },
    )
    registry.register(
        ToolSpec(
            name="observability.deploy_window",
            description="Return deploy window metadata for incident correlation",
            required_fields=("service",),
        ),
        lambda args: {
            "service": args["service"],
            "window_minutes": int(args.get("window_minutes", 30)),
            "status": "ready",
        },
    )

    return registry

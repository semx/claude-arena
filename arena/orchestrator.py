"""Routing plus tool planning facade."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from arena.mcp import ToolRegistry, ToolResult, default_registry
from arena.models import RouteDecision
from arena.router import CostAwareRouter


@dataclass(frozen=True, slots=True)
class WorkflowPlan:
    decision: RouteDecision
    suggested_tools: tuple[str, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.as_dict(),
            "suggested_tools": list(self.suggested_tools),
            "notes": list(self.notes),
        }


class ArenaOrchestrator:
    """Coordinate prompt routing with optional internal tool execution."""

    def __init__(
        self,
        router: CostAwareRouter | None = None,
        registry: ToolRegistry | None = None,
    ) -> None:
        self.router = router or CostAwareRouter()
        self.registry = registry or default_registry()

    def plan(self, prompt: str) -> WorkflowPlan:
        decision = self.router.route(prompt)
        tools = self._suggest_tools(decision)
        notes = []
        if decision.features.risk_flags:
            notes.append("route requires audit logging")
        if not tools:
            notes.append("no tool calls required")

        return WorkflowPlan(
            decision=decision,
            suggested_tools=tools,
            notes=tuple(notes),
        )

    def execute_tool_plan(
        self,
        plan: WorkflowPlan,
        tool_arguments: dict[str, dict[str, Any]],
    ) -> tuple[ToolResult, ...]:
        results = []
        for tool_name in plan.suggested_tools:
            results.append(self.registry.execute(tool_name, tool_arguments.get(tool_name, {})))
        return tuple(results)

    def _suggest_tools(self, decision: RouteDecision) -> tuple[str, ...]:
        domains = set(decision.features.domains)
        tools = []
        if "code" in domains:
            tools.append("repo.diff_summary")
        if "incident" in domains or "infrastructure" in domains:
            tools.append("observability.deploy_window")
        return tuple(tools)

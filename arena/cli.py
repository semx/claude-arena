"""Command line interface."""

from __future__ import annotations

import argparse
import json

from arena.config import load_profiles, load_router_config
from arena.mcp import default_registry
from arena.orchestrator import ArenaOrchestrator
from arena.router import CostAwareRouter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="arena", description="Cost-aware model router")
    parser.add_argument("--config", help="Optional JSON config path")

    subparsers = parser.add_subparsers(dest="command", required=True)

    route = subparsers.add_parser("route", help="Route a prompt")
    route.add_argument("prompt", help="Prompt text to classify and route")
    route.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    subparsers.add_parser("tools", help="List registered tools")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    registry = default_registry()
    router = CostAwareRouter(
        profiles=load_profiles(args.config),
        config=load_router_config(args.config),
    )
    orchestrator = ArenaOrchestrator(router=router, registry=registry)

    if args.command == "route":
        plan = orchestrator.plan(args.prompt)
        print(_json(plan.as_dict(), pretty=args.pretty))
        return 0

    if args.command == "tools":
        tools = [
            {
                "name": spec.name,
                "description": spec.description,
                "required_fields": list(spec.required_fields),
            }
            for spec in registry.list_tools()
        ]
        print(_json({"tools": tools}, pretty=True))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


def _json(payload: object, pretty: bool = False) -> str:
    if pretty:
        return json.dumps(payload, indent=2, sort_keys=True)
    return json.dumps(payload, sort_keys=True)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

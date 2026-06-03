# Claude Arena

[![tests](https://github.com/semx/claude-arena/actions/workflows/tests.yml/badge.svg)](https://github.com/semx/claude-arena/actions/workflows/tests.yml)

Cost-aware model routing and orchestration for developer workflows.

Claude Arena classifies incoming work, estimates token spend, and selects an
appropriate model tier for the job. It is designed for engineering teams that
need predictable costs while still giving complex tasks enough capability.

## What it does

- Classifies prompts by complexity, risk, domain, and expected token volume.
- Routes requests across configurable model tiers with cost ceilings.
- Exposes a small orchestration layer for repository, infrastructure, and
  observability tools.
- Uses OAuth-style session state for user-scoped access instead of long-lived
  shared credentials.
- Ships with a CLI and a deterministic test suite.

## Quick start

```bash
python3 -m unittest discover -s tests
python3 -m arena.cli route "review this Terraform module for risky changes"
```

## Repository layout

```text
arena/
  classifier.py      prompt feature extraction
  router.py          cost and capability based routing
  mcp.py             local tool registry and execution envelope
  oauth.py           user session store
  orchestrator.py    routing + tool planning facade
tests/               unit tests
```

## Status

The project is intentionally self-contained: no network calls are required to
exercise routing, tool selection, or session management. Provider adapters can
be wired in behind the orchestration interface when deployed.

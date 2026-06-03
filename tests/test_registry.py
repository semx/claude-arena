from unittest import TestCase

from arena.mcp import ToolRegistry, ToolSpec, default_registry


class ToolRegistryTest(TestCase):
    def test_executes_registered_tool(self) -> None:
        registry = ToolRegistry()
        registry.register(
            ToolSpec(name="echo", description="Echo payload", required_fields=("value",)),
            lambda args: {"value": args["value"]},
        )

        result = registry.execute("echo", {"value": "ok"})

        self.assertTrue(result.ok)
        self.assertEqual(result.payload["value"], "ok")

    def test_validates_required_fields(self) -> None:
        result = default_registry().execute("repo.diff_summary", {})

        self.assertFalse(result.ok)
        self.assertIn("missing required fields", result.error)

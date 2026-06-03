from unittest import TestCase

from arena.orchestrator import ArenaOrchestrator


class ArenaOrchestratorTest(TestCase):
    def test_suggests_repository_and_observability_tools(self) -> None:
        plan = ArenaOrchestrator().plan(
            "Review repository diff and correlate production incident logs after deploy"
        )

        self.assertIn("repo.diff_summary", plan.suggested_tools)
        self.assertIn("observability.deploy_window", plan.suggested_tools)

    def test_executes_suggested_tool_plan(self) -> None:
        orchestrator = ArenaOrchestrator()
        plan = orchestrator.plan("Review repository diff")
        results = orchestrator.execute_tool_plan(
            plan,
            {"repo.diff_summary": {"files": ["main.tf", "values.yaml"]}},
        )

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].ok)
        self.assertEqual(results[0].payload["changed_files"], 2)

from unittest import TestCase

from arena.router import CostAwareRouter, RouterConfig


class CostAwareRouterTest(TestCase):
    def test_routes_simple_work_to_small_tier(self) -> None:
        decision = CostAwareRouter().route("summarize this changelog in three bullets")

        self.assertEqual(decision.model.tier, "haiku")
        self.assertLess(decision.estimated_cost_usd, 0.01)

    def test_routes_complex_work_to_capable_tier_when_budget_allows(self) -> None:
        router = CostAwareRouter(config=RouterConfig(max_cost_usd=1.0))
        decision = router.route(
            "Perform architecture review for a production Kubernetes migration, "
            "debug security policy drift, and inspect repository context"
        )

        self.assertEqual(decision.model.tier, "opus")
        self.assertIsNone(decision.fallback_model)

    def test_downgrades_when_cost_ceiling_is_tight(self) -> None:
        router = CostAwareRouter(config=RouterConfig(max_cost_usd=0.03))
        decision = router.route(
            "Perform architecture review for a production Kubernetes migration, "
            "debug security policy drift, and inspect repository context"
        )

        self.assertEqual(decision.model.tier, "sonnet")
        self.assertEqual(decision.fallback_model, "claude-3-opus")

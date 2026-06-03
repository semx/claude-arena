from unittest import TestCase

from arena.classifier import PromptClassifier


class PromptClassifierTest(TestCase):
    def test_detects_infrastructure_incident_work(self) -> None:
        features = PromptClassifier().classify(
            "Investigate production Kubernetes incident using logs, traces, and recent deploys"
        )

        self.assertIn("infrastructure", features.domains)
        self.assertIn("incident", features.domains)
        self.assertTrue(features.requires_tools)
        self.assertGreaterEqual(features.complexity, 72)

    def test_simple_summary_stays_low_complexity(self) -> None:
        features = PromptClassifier().classify("quickly summarize this short README")

        self.assertEqual(features.band, "low")
        self.assertFalse(features.requires_tools)

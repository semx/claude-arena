import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from arena.config import load_profiles, load_router_config
from arena.models import DEFAULT_MODEL_PROFILES
from arena.router import RouterConfig


class LoadRouterConfigTest(TestCase):
    def test_returns_defaults_without_path(self) -> None:
        self.assertEqual(load_router_config(), RouterConfig())

    def test_partial_router_section_falls_back_to_defaults(self) -> None:
        defaults = RouterConfig()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"router": {"prefer_capability": False}}), encoding="utf-8")

            config = load_router_config(path)

        self.assertFalse(config.prefer_capability)
        self.assertEqual(config.max_cost_usd, defaults.max_cost_usd)
        self.assertEqual(config.allow_downgrade, defaults.allow_downgrade)


class LoadProfilesTest(TestCase):
    def test_config_without_models_keeps_default_profiles(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"router": {"max_cost_usd": 0.1}}), encoding="utf-8")

            self.assertEqual(load_profiles(path), DEFAULT_MODEL_PROFILES)

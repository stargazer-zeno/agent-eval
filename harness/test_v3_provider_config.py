from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import run_codex_eval


class V3ProviderConfigTests(unittest.TestCase):
    def test_seed_long_session_compaction_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "codex_home"
            model, authentication, environment, extra = run_codex_eval.provider_config(
                "seed_evolving",
                {"Seed_Agent_Plan_key": "synthetic-canary-value"},
                home,
                "http://127.0.0.1:9/v1",
            )
            config = (home / "config.toml").read_text(encoding="utf-8")
            self.assertEqual(model, "doubao-seed-evolving")
            self.assertEqual(authentication, "seed_evolving")
            self.assertEqual(extra, ["--model", "doubao-seed-evolving"])
            self.assertIn("model_context_window = 256000", config)
            self.assertIn("model_auto_compact_token_limit = 180000", config)
            self.assertIn("model_supports_reasoning_summaries = true", config)
            self.assertNotIn("synthetic-canary-value", config)
            self.assertEqual(environment["Seed_Agent_Plan_key"], "synthetic-canary-value")

    def test_non_seed_provider_does_not_inherit_seed_limits(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "codex_home"
            run_codex_eval.provider_config(
                "qwen38",
                {"QWEN_API_KEY": "synthetic", "QWEN_BASE_URL": "https://example.invalid/v1"},
                home,
            )
            config = (home / "config.toml").read_text(encoding="utf-8")
            self.assertNotIn("model_auto_compact_token_limit", config)


if __name__ == "__main__":
    unittest.main()

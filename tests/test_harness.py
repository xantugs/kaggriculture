"""Harness integrity checks; no Kaggle installation or full games required."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("tested_harness", ROOT / "tools" / "harness.py")
harness = importlib.util.module_from_spec(spec)
with mock.patch.dict(sys.modules, {"kaggle_environments": SimpleNamespace(make=mock.Mock())}):
    spec.loader.exec_module(harness)


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "tools").mkdir()
        (self.root / "versions").mkdir()
        self.agent_path = self.root / "main.py"
        self.agent_path.write_text(
            "PARAMS = {'weight': 1}\nDEBUG = False\ncount = 0\n"
            "def agent(*args):\n    global count\n    count += 1\n    return count, PARAMS['weight'], DEBUG\n",
            encoding="utf-8")

    def test_module_instances_are_independent_and_overrides_do_not_leak(self):
        a = harness.load_agent(self.agent_path, {"weight": 9})
        b = harness.load_agent(self.agent_path)
        self.assertEqual(a(), (1, 9, True))
        self.assertEqual(a(), (2, 9, True))
        self.assertEqual(b(), (1, 1, True))

    def test_unknown_parameters_fail_before_evaluation(self):
        with self.assertRaisesRegex(ValueError, "Unknown agent parameters.*wieght"):
            harness.load_agent(self.agent_path, {"wieght": 9})
        with self.assertRaisesRegex(ValueError, "does not accept"):
            harness.load_agent("starter", {"weight": 9})

    def test_resolves_root_tools_and_versions_from_unrelated_directory(self):
        (self.root / "tools" / "tool_agent.py").write_text("", encoding="utf-8")
        (self.root / "versions" / "main_v7.py").write_text("", encoding="utf-8")
        with mock.patch.object(harness, "PROJECT_ROOT", self.root), mock.patch.object(Path, "cwd", return_value=self.root / "unrelated"):
            self.assertEqual(harness.resolve_agent_path("main.py"), str(self.agent_path.resolve()))
            self.assertEqual(harness.resolve_agent_path("tool_agent.py"), str((self.root / "tools" / "tool_agent.py").resolve()))
            self.assertEqual(harness.resolve_agent_path("main_v7.py"), str((self.root / "versions" / "main_v7.py").resolve()))

    def test_metadata_contains_full_parameters_and_content_hash(self):
        meta = harness.describe_agent(self.agent_path, {"weight": 2})
        self.assertEqual(meta["params"], {"weight": 2})
        self.assertEqual(len(meta["sha256"]), 64)
        self.assertEqual(json.loads(json.dumps(meta)), meta)

    def fake_env(self, rewards=(20, 10), statuses=("DONE", "DONE")):
        return SimpleNamespace(run=mock.Mock(), steps=[[
            SimpleNamespace(reward=r, status=s) for r, s in zip(rewards, statuses)]])

    def test_success_uses_environment_episode_default_and_honors_debug(self):
        env = self.fake_env()
        with mock.patch.object(harness, "make", return_value=env) as make:
            self.assertEqual(harness.run_match("pass", "pass", 42, debug=False), (env, [20, 10], ["DONE", "DONE"]))
            make.assert_called_once_with("kaggriculture", debug=False, configuration={"seed": 42})

    def test_explicit_episode_limit_is_preserved(self):
        with mock.patch.object(harness, "make", return_value=self.fake_env()) as make:
            harness.run_match("pass", "pass", 42, steps=5)
            self.assertEqual(make.call_args.kwargs["configuration"]["episodeSteps"], 5)

    def test_failed_status_never_becomes_a_win(self):
        with mock.patch.object(harness, "make", return_value=self.fake_env((100, 0), ("DONE", "ERROR"))):
            with self.assertRaises(harness.MatchError) as caught:
                harness.run_match("pass", "pass", 42)
        self.assertEqual(caught.exception.statuses, ["DONE", "ERROR"])

    def test_nonfinite_and_nonnumeric_rewards_are_rejected(self):
        for reward in (None, float("nan"), float("inf"), "100", True):
            with self.subTest(reward=reward), mock.patch.object(harness, "make", return_value=self.fake_env((reward, 10))):
                with self.assertRaises(harness.MatchError):
                    harness.run_match("pass", "pass", 42)


if __name__ == "__main__":
    unittest.main()

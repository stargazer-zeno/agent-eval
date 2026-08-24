#!/usr/bin/env python3
"""Model-free unit tests for the v3 state receipt and workspace hashing."""
from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path

import stateful_controller


class StatefulControllerTests(unittest.TestCase):
    def test_tree_hash_ignores_generated_directories(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "source.gd").write_text("alpha\n", encoding="utf-8")
            first = stateful_controller.tree_sha256(root)
            generated = root / ".godot"
            generated.mkdir()
            (generated / "cache").write_text("ignored", encoding="utf-8")
            self.assertEqual(first, stateful_controller.tree_sha256(root))
            (root / "source.gd").write_text("beta\n", encoding="utf-8")
            self.assertNotEqual(first, stateful_controller.tree_sha256(root))

    def test_sha256_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "value.txt"
            path.write_text("state", encoding="utf-8")
            self.assertEqual(stateful_controller.sha256(path), stateful_controller.sha256(path))

    def test_stateful_adapter_advances_and_chains_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            workspace = root / "workspace"
            workspace.mkdir()
            (workspace / "source.gd").write_text("value\n", encoding="utf-8")
            adapter = root / "adapter.py"
            adapter.write_text(
                "import argparse,json\n"
                "p=argparse.ArgumentParser()\n"
                "for n in ('workspace','godot','state','scenario','output','result'): p.add_argument('--'+n,required=True)\n"
                "a=p.parse_args(); s=json.load(open(a.state,encoding='utf-8')); before=s['phase']; s={'phase':'NEXT','step':s['step']+1,'data':{}}\n"
                "open(a.output,'wb').write(b'PNG'); json.dump({'phase_before':before,'phase_after':'NEXT','advanced':True,'next_state':s},open(a.result,'w',encoding='utf-8'))\n",
                encoding="utf-8",
            )
            task = {"harness": {"initial_state": "START", "allowed_scenarios": ["ADVANCE"], "default_scenario": "ADVANCE", "controller_adapter": "adapter.py"}}
            session = stateful_controller.StatefulObservation(root, task, workspace, root / "control")
            first = session.observe("ADVANCE", root / "one.png", Path("unused.exe"))
            second = session.observe("ADVANCE", root / "two.png", Path("unused.exe"))
            self.assertTrue(first["advanced"])
            self.assertEqual(first["phase_before"], "START")
            self.assertEqual(second["phase_before"], "NEXT")
            lines = (root / "control" / "state_ledger.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            one, two = map(json.loads, lines)
            self.assertEqual(two["previous_sha256"], one["event_sha256"])


if __name__ == "__main__":
    unittest.main()

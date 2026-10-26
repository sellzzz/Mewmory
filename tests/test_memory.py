import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from mewmory import Memory


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.memory = Memory(":memory:")
        self.addCleanup(self.memory.close)

    def add(self, outcome="food", **overrides):
        event = dict(actor="Mira", place="kitchen", cue="can opening", outcome=outcome,
                     text="Pip hears a can", occurred_at="2026-01-01T08:00:00+00:00")
        event.update(overrides)
        return self.memory.add(**event)

    def test_frequency_includes_conflicting_outcomes_and_trace(self):
        ids = [self.add(), self.add()]
        self.add("no food")
        rule = self.memory.rules()[0]
        self.assertEqual(rule["source_ids"], ids)
        self.assertAlmostEqual(rule["frequency"], 2 / 3)
        self.assertEqual(len(self.memory.trace(ids)), 2)
        self.assertEqual(self.memory.trace(ids)[0]["text"], "Pip hears a can")

    def test_context_is_bounded_and_unknown_query_is_empty(self):
        for _ in range(10):
            self.add()
        result = self.memory.recall("can", limit=2, max_chars=400)
        self.assertTrue(result)
        self.assertLessEqual(len(result), 2)
        self.assertLessEqual(len(json.dumps(result, ensure_ascii=False)), 400)
        self.assertTrue(result[0]["sources_truncated"])
        self.assertEqual(len(self.memory.rules()[0]["source_ids"]), 10)
        self.assertEqual(self.memory.recall("spaceship"), [])
        self.assertEqual(self.memory.recall("can", max_chars=2), [])

    def test_validation(self):
        for overrides in ({"actor": " "}, {"occurred_at": "bad"},
                          {"occurred_at": "2026-01-01T08:00:00"}):
            with self.assertRaises(ValueError):
                self.add(**overrides)
        with self.assertRaises(KeyError):
            self.memory.trace([999])
        with self.assertRaises(ValueError):
            self.memory.recall("can", limit=0)

    def test_contexts_are_separate(self):
        self.add()
        self.add(place="garden")
        self.assertEqual(self.memory.rules(), [])

    def test_unicode_and_sql_text(self):
        event_id = self.add(text="猫听见罐头声 '; DROP TABLE events; --", cue="罐头声")
        self.assertEqual(self.memory.recall("罐头")[0]["source_ids"], [event_id])
        self.assertEqual(len(self.memory.events()), 1)

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "memory.db"
            with Memory(path) as memory:
                memory.add(actor="a", place="p", cue="c", outcome="o", text="t")
            with Memory(path) as memory:
                self.assertEqual(memory.trace([1])[0]["text"], "t")

    def test_cli_end_to_end(self):
        with tempfile.TemporaryDirectory() as folder:
            base = [sys.executable, "-m", "mewmory", "--db", str(Path(folder) / "test.db")]
            def run(*args):
                return json.loads(subprocess.check_output(base + list(args), encoding="utf-8"))
            self.assertEqual(len(run("demo")["ids"]), 6)
            self.assertEqual(run("rules")[0]["support"], 2)
            self.assertTrue(run("recall", "can opening"))
            self.assertEqual(run("trace", "1")[0]["actor"], "Mira")


if __name__ == "__main__":
    unittest.main()

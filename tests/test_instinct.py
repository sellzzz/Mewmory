import json
import subprocess
import sys
import unittest

from mewmory import Memory
from mewmory.instinct import Feedback, Kitten, Needs, Senses, choose, simulate


class InstinctTests(unittest.TestCase):
    def setUp(self):
        self.memory = Memory(":memory:")
        self.addCleanup(self.memory.close)

    def test_unlearned_response_and_competing_needs(self):
        hungry = Needs(hunger=0.9, cold=0, fatigue=0)
        self.assertEqual(choose(hungry, Senses(food_cue=True)), ("orient_to_food", "hunger"))
        self.assertEqual(choose(hungry, Senses()), ("call", "hunger"))
        self.assertEqual(choose(Needs(), Senses(warm_contact=True)), ("nuzzle", "cold"))

    def test_disturbance_interrupts_and_low_demand_rests(self):
        self.assertEqual(choose(Needs(), Senses(disturbance=0.9)), ("recoil", "disturbance"))
        self.assertEqual(choose(Needs(0, 0, 0), Senses()), ("rest", "low_demand"))

    def test_food_cue_and_intent_alone_do_not_satisfy_hunger(self):
        kitten = Kitten(self.memory, needs=Needs(0.9, 0, 0))
        result = kitten.step(cue="scent", senses=Senses(food_cue=True))
        self.assertEqual(result["action"], "orient_to_food")
        self.assertEqual(result["after"]["hunger"], 0.9)
        self.assertEqual(result["reinforcement"], 0)
        self.assertEqual(result["outcome"], "unchanged")

    def test_feedback_is_bounded_and_preserves_provenance(self):
        kitten = Kitten(self.memory)
        result = kitten.step(cue="contact", senses=Senses(), feedback=Feedback(hunger=-1, cold=1))
        self.assertEqual(result["after"]["hunger"], 0)
        self.assertEqual(result["after"]["cold"], 1)
        original = self.memory.trace([result["event_id"]])[0]
        evidence = json.loads(original["text"])
        self.assertEqual(evidence["source"], "synthetic_simulation")
        self.assertEqual(evidence["feedback"]["cold"], 1)
        self.assertEqual(evidence["after"], result["after"])

    def test_worsening_has_negative_reinforcement(self):
        kitten = Kitten(self.memory, needs=Needs(0, 0, 0))
        result = kitten.step(cue="waiting", senses=Senses(), feedback=Feedback(hunger=0.2))
        self.assertLess(result["reinforcement"], 0)

    def test_synthetic_demo_forms_traceable_association(self):
        steps = simulate(self.memory)
        self.assertEqual([step["action"] for step in steps],
                         ["call", "nuzzle", "orient_to_food", "orient_to_food", "rest"])
        rule = self.memory.rules()[0]
        self.assertEqual(rule["cue"], "caregiver_scent")
        self.assertEqual(rule["outcome"], "hunger_down")
        self.assertEqual(rule["source_ids"], [3, 4])
        self.assertEqual(rule["frequency"], 2 / 3)
        recall = self.memory.recall("caregiver_scent", limit=1)
        self.assertEqual(recall[0]["kind"], "rule")
        self.assertEqual(len(self.memory.trace(recall[0]["source_ids"])), 2)

    def test_invalid_state_is_rejected(self):
        for value in (-0.1, 1.1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                Needs(hunger=value)
        with self.assertRaises(ValueError):
            Feedback(cold=-2)
        with self.assertRaises(ValueError):
            Senses(food_cue="yes")

    def test_cli_simulation(self):
        output = subprocess.check_output(
            [sys.executable, "-m", "mewmory", "--db", ":memory:", "simulate"], encoding="utf-8")
        steps = json.loads(output)
        self.assertEqual(len(steps), 5)
        self.assertEqual(steps[0]["source"], "synthetic_simulation")
        self.assertEqual(steps[-1]["action"], "rest")

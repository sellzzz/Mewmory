"""Toy homeostatic controller. All values are simulation assumptions, not biology."""
import json
import math
from dataclasses import asdict, dataclass


# Arbitrary priorities for experiments; these have not been fitted to animal data.
WEIGHTS = {"hunger": 1.0, "cold": 1.2, "fatigue": 0.5}


def validate_numbers(values, lower, upper):
    for value in values:
        if not isinstance(value, (int, float)) or not math.isfinite(value) or not lower <= value <= upper:
            raise ValueError(f"Simulation values must be finite numbers in [{lower}, {upper}]")


@dataclass(frozen=True)
class Needs:
    hunger: float = 0.9
    cold: float = 0.8
    fatigue: float = 0.6

    def __post_init__(self):
        validate_numbers(asdict(self).values(), 0, 1)

    def discomfort(self):
        return sum(WEIGHTS[key] * value for key, value in asdict(self).items())


@dataclass(frozen=True)
class Senses:
    food_cue: bool = False
    warm_contact: bool = False
    disturbance: float = 0.0

    def __post_init__(self):
        if not isinstance(self.food_cue, bool) or not isinstance(self.warm_contact, bool):
            raise ValueError("Sensory cues must be booleans")
        validate_numbers([self.disturbance], 0, 1)


@dataclass(frozen=True)
class Feedback:
    """Changes supplied by the environment, independently of the chosen action."""
    hunger: float = 0.0
    cold: float = 0.0
    fatigue: float = 0.0

    def __post_init__(self):
        validate_numbers(asdict(self).values(), -1, 1)


def choose(needs, senses):
    """Return an action and an inspectable reason, with deterministic tie-breaking."""
    if senses.disturbance >= 0.6:
        return "recoil", "disturbance"
    urgency = {key: WEIGHTS[key] * value for key, value in asdict(needs).items()}
    drive = max(urgency, key=urgency.get)
    if urgency[drive] < 0.25:
        return "rest", "low_demand"
    if drive == "cold":
        return ("nuzzle" if senses.warm_contact else "call"), drive
    if drive == "hunger":
        return ("orient_to_food" if senses.food_cue else "call"), drive
    return "rest", drive


class Kitten:
    def __init__(self, memory, name="Kitten-01", needs=None):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be nonempty")
        self.memory = memory
        self.name = name.strip()
        self.needs = needs if needs is not None else Needs()

    def step(self, *, cue, senses, feedback=None, actor="fictional_caregiver", place="fictional_nest"):
        feedback = feedback if feedback is not None else Feedback()
        before = asdict(self.needs)
        action, drive = choose(self.needs, senses)
        after = Needs(**{key: max(0.0, min(1.0, value + getattr(feedback, key)))
                         for key, value in before.items()})
        changes = [key + ("_down" if value < before[key] else "_up")
                   for key, value in asdict(after).items() if value != before[key]]
        outcome = "+".join(changes) or "unchanged"
        record = dict(source="synthetic_simulation", name=self.name, before=before,
                      senses=asdict(senses), action=action, drive=drive,
                      feedback=asdict(feedback), after=asdict(after),
                      reinforcement=round(self.needs.discomfort() - after.discomfort(), 6))
        event_id = self.memory.add(actor=actor, place=place, cue=cue, outcome=outcome,
                                   text=json.dumps(record, ensure_ascii=False))
        self.needs = after
        return dict(event_id=event_id, cue=cue, outcome=outcome, **record)


def simulate(memory, name="Kitten-01"):
    """Five invented steps; not a reenactment, real timeline or care instructions."""
    kitten = Kitten(memory, name=name)
    scenario = [
        ("unfamiliar_place", Senses(), Feedback()),
        ("caregiver_scent", Senses(warm_contact=True), Feedback(cold=-0.65)),
        ("caregiver_scent", Senses(food_cue=True), Feedback(hunger=-0.45)),
        ("caregiver_scent", Senses(food_cue=True), Feedback(hunger=-0.4)),
        ("quiet_contact", Senses(warm_contact=True), Feedback(fatigue=-0.5)),
    ]
    return [kitten.step(cue=cue, senses=senses, feedback=feedback)
            for cue, senses, feedback in scenario]

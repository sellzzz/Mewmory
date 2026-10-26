# Instinct before narrative

## Research boundary

A kitten need not be assigned a human-style account of abandonment or trust in
order to simulate needs and learned associations. This modeling choice does not
establish whether an animal has consciousness or particular subjective feelings.

Research reports both inborn and learned contributions to newborn kitten nipple
search and attachment. Raihani et al. (2009), [Olfactory guidance of nipple
attachment and suckling in kittens of the domestic cat: Inborn and learned
responses](https://pubmed.ncbi.nlm.nih.gov/19757456/), describes responses to
lactating females and learning of mother-specific olfactory cues. This motivates
separating initial response tendencies from acquired associations. It does not
validate this controller, its weights, its actions, or its fictional scenario.

## Controller

State is three unitless numbers in [0, 1]: hunger, cold and fatigue. For each need:

```
urgency = need * weight
weights = {hunger: 1.0, cold: 1.2, fatigue: 0.5}
```

The highest urgency selects a drive. Ties follow hunger, cold, fatigue order.
An external disturbance >= 0.6 interrupts with `recoil`. Otherwise:

| Selected drive | Available cue | Action |
| --- | --- | --- |
| cold | warm contact | nuzzle |
| cold | no warm contact | call |
| hunger | food cue | orient_to_food |
| hunger | no food cue | call |
| fatigue | any | rest |
| all weighted urgencies below 0.25 | any | rest |

All numbers and action mappings are explicit engineering assumptions. They do
not describe measured development at a particular age. The model has no walking,
human language, concept of parenthood, or narrative interpretation module.

## Environment and memory

An action does not guarantee a successful outcome. The environment supplies
signed changes in [-1, 1] for each need; state is clamped to [0, 1]. There is no
implicit feeding, automatic time progression, aging or survival model. The
caller can explicitly supply worsening needs as well as relief.

```
discomfort = sum(weight * need)
reinforcement = discomfort_before - discomfort_after
```

This scalar measures an observed change in the toy state. It does not establish
that the action caused the change, and is not evidence of conscious pleasure or
suffering. It is logged but does not yet train the controller.

Every step records before/after state, sensory input, selected drive/action,
environment feedback and reinforcement in event text, labeled
`synthetic_simulation`. Outcome labels report which needs actually moved.
The existing aggregation groups actor/place/cue and counts outcomes, so two
`caregiver_scent` events with `hunger_down` can produce an association. The third
event for the same cue (cold relief) remains in the denominator: frequency 2/3.
Evidence IDs permit inspection of the original simulated transitions.

Memory is currently an auditable observer of this controller. It does not yet
change action selection. A next experiment can compare the fixed controller to
a learned cue-guided policy on held-out scenarios, including misleading cues.

The shipped five-step scenario is entirely invented. It contains no user's
personal history or real rescue record. Repeating it adds duplicate observations;
it must not be treated as independent biological evidence.

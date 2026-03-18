"""Backward chaining engine for testing whether a goal can be justified."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from student_success_copilot.reasoning.rules import Rule, get_rules


@dataclass
class ProofStep:
    """Record one proof step for a goal."""

    goal: str
    success: bool
    strength: float
    rule_name: str | None = None
    detail: str = ""


@dataclass
class BackwardChainingResult:
    """Store the final proof result and the path used to reach it."""

    goal: str
    proved: bool
    strength: float
    proof_path: list[ProofStep] = field(default_factory=list)


def backward_chain(
    goal: str,
    known_facts: Mapping[str, float],
    rules: Sequence[Rule] | None = None,
) -> BackwardChainingResult:
    """Try to prove a goal from known facts and rules."""
    active_rules = rules if rules is not None else get_rules()
    proved, strength, proof_path = _prove_goal(
        goal=goal,
        known_facts=known_facts,
        rules=active_rules,
        visited=set(),
    )

    return BackwardChainingResult(
        goal=goal,
        proved=proved,
        strength=strength,
        proof_path=proof_path,
    )


def _prove_goal(
    goal: str,
    known_facts: Mapping[str, float],
    rules: Sequence[Rule],
    visited: set[str],
) -> tuple[bool, float, list[ProofStep]]:
    """Recursively prove a goal and return a proof path."""
    if goal in known_facts:
        return True, known_facts[goal], [
            ProofStep(
                goal=goal,
                success=True,
                strength=known_facts[goal],
                detail=f"Goal '{goal}' was already known as an initial or inferred fact.",
            )
        ]

    if goal in visited:
        return False, 0.0, [
            ProofStep(
                goal=goal,
                success=False,
                strength=0.0,
                detail=f"Stopped to avoid a reasoning loop while proving '{goal}'.",
            )
        ]

    visited.add(goal)
    best_strength = 0.0
    best_path: list[ProofStep] = []
    matching_rules = [rule for rule in rules if rule.conclusion == goal]

    if not matching_rules:
        visited.remove(goal)
        return False, 0.0, [
            ProofStep(
                goal=goal,
                success=False,
                strength=0.0,
                detail=f"No rule concludes '{goal}'.",
            )
        ]

    for rule in matching_rules:
        combined_path: list[ProofStep] = []
        premise_strengths: list[float] = []
        rule_success = True

        for premise in rule.premises:
            proved, premise_strength, premise_path = _prove_goal(
                goal=premise,
                known_facts=known_facts,
                rules=rules,
                visited=visited,
            )
            combined_path.extend(premise_path)

            if not proved:
                rule_success = False
                combined_path.append(
                    ProofStep(
                        goal=goal,
                        success=False,
                        strength=0.0,
                        rule_name=rule.name,
                        detail=(
                            f"Rule '{rule.name}' could not prove '{goal}' "
                            f"because premise '{premise}' failed."
                        ),
                    )
                )
                break

            premise_strengths.append(premise_strength)

        if not rule_success:
            if not best_path:
                best_path = combined_path
            continue

        goal_strength = min(premise_strengths) * rule.strength
        combined_path.append(
            ProofStep(
                goal=goal,
                success=True,
                strength=goal_strength,
                rule_name=rule.name,
                detail=(
                    f"Rule '{rule.name}' proved '{goal}' from premises "
                    f"{', '.join(rule.premises)}."
                ),
            )
        )

        if goal_strength > best_strength:
            best_strength = goal_strength
            best_path = combined_path

    visited.remove(goal)
    return best_strength > 0.0, best_strength, best_path

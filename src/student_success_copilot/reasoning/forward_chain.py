"""Forward chaining engine for the Student Success Copilot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from student_success_copilot.reasoning.facts import FactStrengths
from student_success_copilot.reasoning.rules import Rule, get_rules


@dataclass
class TraceStep:
    """Record one successful rule application."""

    rule_name: str
    premises: tuple[str, ...]
    conclusion: str
    premise_strength: float
    rule_strength: float
    conclusion_strength: float
    description: str


@dataclass
class ForwardChainingResult:
    """Store inferred facts together with a reasoning trace."""

    facts: FactStrengths = field(default_factory=dict)
    trace: list[TraceStep] = field(default_factory=list)

    def has_fact(self, fact_name: str, minimum_strength: float = 0.0) -> bool:
        """Return True when the requested fact is present strongly enough."""
        return self.facts.get(fact_name, 0.0) >= minimum_strength

    def get_recommendations(self, rules: Sequence[Rule] | None = None) -> list[str]:
        """Collect unique recommendation texts whose conclusion facts were inferred."""
        active_rules = rules if rules is not None else get_rules()
        recommendations: list[str] = []
        seen: set[str] = set()

        for rule in active_rules:
            if rule.recommendation and rule.conclusion in self.facts:
                if rule.recommendation not in seen:
                    recommendations.append(rule.recommendation)
                    seen.add(rule.recommendation)

        return recommendations


def forward_chain(
    initial_facts: Mapping[str, float],
    rules: Sequence[Rule] | None = None,
    max_iterations: int = 20,
) -> ForwardChainingResult:
    """Infer new facts by repeatedly applying rules whose premises are true."""
    active_rules = rules if rules is not None else get_rules()
    known_facts: FactStrengths = dict(initial_facts)
    trace: list[TraceStep] = []

    for _ in range(max_iterations):
        changed = False

        for rule in active_rules:
            premise_strength = _match_rule(rule, known_facts)
            if premise_strength is None:
                continue

            conclusion_strength = premise_strength * rule.strength
            current_strength = known_facts.get(rule.conclusion, 0.0)

            if conclusion_strength > current_strength + 1e-9:
                known_facts[rule.conclusion] = conclusion_strength
                trace.append(
                    TraceStep(
                        rule_name=rule.name,
                        premises=rule.premises,
                        conclusion=rule.conclusion,
                        premise_strength=premise_strength,
                        rule_strength=rule.strength,
                        conclusion_strength=conclusion_strength,
                        description=rule.description,
                    )
                )
                changed = True

        if not changed:
            break

    return ForwardChainingResult(facts=known_facts, trace=trace)


def _match_rule(rule: Rule, known_facts: Mapping[str, float]) -> float | None:
    """Return the combined premise strength when all premises are present."""
    premise_strengths: list[float] = []

    for premise in rule.premises:
        strength = known_facts.get(premise)
        if strength is None:
            return None
        premise_strengths.append(strength)

    if not premise_strengths:
        return None

    return min(premise_strengths)

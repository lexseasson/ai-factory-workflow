from __future__ import annotations

from collections.abc import Sequence

from workflow.models import Decision, NormalizedRequest, RuleFailure, ValidationResult
from workflow.rules import Rule


def validate(r: NormalizedRequest, rules: Sequence[Rule]) -> ValidationResult:
    """
    Ejecuta las reglas de elegibilidad sobre un registro normalizado.

    Propiedades:
    - Determinístico (mismo input + mismas reglas => mismo output)
    - Sin efectos secundarios
    - Fácil de testear y auditar
    """
    failures: list[RuleFailure] = []

    for rule in rules:
        reason = rule.check(r)
        if reason is not None:
            failures.append(
                RuleFailure(
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    reason=reason,
                )
            )

    if failures:
        return ValidationResult(
            decision=Decision.REJECT,
            failures=tuple(failures),
        )

    return ValidationResult(
        decision=Decision.ACCEPT,
        failures=tuple(),
    )

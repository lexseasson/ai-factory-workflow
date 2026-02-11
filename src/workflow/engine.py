from __future__ import annotations

from workflow.models import Decision, NormalizedRequest, ValidationResult
from workflow.rules import Rule, to_failure


def validate(r: NormalizedRequest, rules: list[Rule]) -> ValidationResult:
    failures = []
    for rule in rules:
        reason = rule.check(r)
        if reason is not None:
            failures.append(to_failure(rule, reason))

    if failures:
        return ValidationResult(decision=Decision.REJECT, failures=tuple(failures))
    return ValidationResult(decision=Decision.ACCEPT, failures=tuple())

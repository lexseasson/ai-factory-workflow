from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from workflow.models import NormalizedRequest, RuleFailure, Severity


class Rule(Protocol):
    @property
    def rule_id(self) -> str: ...

    @property
    def severity(self) -> Severity: ...

    def check(self, r: NormalizedRequest) -> str | None:
        """Return reason string if fails, otherwise None."""


@dataclass(frozen=True)
class RequiredFieldsRule:
    rule_id: str = "REQUIRED_FIELDS"
    severity: Severity = Severity.HIGH

    def check(self, r: NormalizedRequest) -> str | None:
        # Ya normalizado, pero aseguramos “no vacío” donde aplica
        if not r.id_solicitud:
            return "id_solicitud is empty"
        if not r.id_cliente:
            return "id_cliente is empty"
        if not r.tipo_producto:
            return "tipo_producto is empty"
        if not r.moneda:
            return "moneda is empty"
        if not r.pais:
            return "pais is empty"
        return None


@dataclass(frozen=True)
class CurrencyAllowedRule:
    allowed: tuple[str, ...] = ("ARS", "USD", "EUR")
    rule_id: str = "CURRENCY_ALLOWED"
    severity: Severity = Severity.MEDIUM

    def check(self, r: NormalizedRequest) -> str | None:
        if r.moneda not in self.allowed:
            return f"moneda '{r.moneda}' not in allowed list {list(self.allowed)}"
        return None


@dataclass(frozen=True)
class AmountRangeRule:
    min_value: float = 1.0
    max_value: float = 1_000_000.0
    rule_id: str = "AMOUNT_RANGE"
    severity: Severity = Severity.MEDIUM

    def check(self, r: NormalizedRequest) -> str | None:
        if r.monto_o_limite < self.min_value or r.monto_o_limite > self.max_value:
            return f"monto_o_limite {r.monto_o_limite} out of range [{self.min_value}, {self.max_value}]"
        return None


def to_failure(rule: Rule, reason: str) -> RuleFailure:
    return RuleFailure(rule_id=rule.rule_id, severity=rule.severity, reason=reason)

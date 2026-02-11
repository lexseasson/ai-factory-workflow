from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Decision(StrEnum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"


@dataclass(frozen=True)
class RawRequest:
    id_solicitud: str
    fecha_solicitud: str
    tipo_producto: str
    id_cliente: str
    monto_o_limite: str
    moneda: str
    pais: str
    is_vip: str
    risk_score: str


@dataclass(frozen=True)
class NormalizedRequest:
    id_solicitud: str
    fecha_solicitud: date
    tipo_producto: str
    id_cliente: str
    monto_o_limite: float
    moneda: str
    pais: str
    is_vip: bool
    risk_score: int
    risk_bucket: str  # LOW/MED/HIGH (campo calculado)


@dataclass(frozen=True)
class RuleFailure:
    rule_id: str
    severity: Severity
    reason: str


@dataclass(frozen=True)
class ValidationResult:
    decision: Decision
    failures: tuple[RuleFailure, ...]


@dataclass(frozen=True)
class WorkflowStats:
    total: int
    valid: int
    invalid: int


@dataclass(frozen=True)
class QualityRuleDetail:
    rule_id: str
    failed_count: int
    pass_rate: float
    examples: list[str]


@dataclass(frozen=True)
class QualityReport:
    run_id: str
    generated_utc: str
    totals: WorkflowStats
    rule_details: list[QualityRuleDetail]
    notes: list[str]

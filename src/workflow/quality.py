from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from workflow.models import QualityReport, QualityRuleDetail, WorkflowStats


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _safe_rate(numer: int, denom: int) -> float:
    return 0.0 if denom <= 0 else numer / denom


def _round4(x: float) -> float:
    return round(x, 4)


@dataclass(frozen=True)
class QualityGatePolicy:
    """
    Política versionable del quality gate.

    Nota: en producción suele vivir fuera del código (config versionada).
    Para el challenge la dejamos explícita y trazable.
    """

    policy_id: str = "quality_gate.v1"
    # Guardrail: si el rechazo supera este umbral, el run queda en WARNING.
    max_rejection_rate: float = 0.40
    # Guardrail adicional (opcional): si hay muy pocos registros válidos.
    min_acceptance_rate: float = 0.10


@dataclass(frozen=True)
class QualityGateDecision:
    """
    Decisión automatizada del quality gate.
    """

    decision: str  # PASS | WARN
    rationale: str
    policy_id: str
    metrics_snapshot: dict[str, float]


def evaluate_quality_gate(
    *,
    acceptance_rate: float,
    rejection_rate: float,
    policy: QualityGatePolicy,
) -> QualityGateDecision:
    # Regla 1: exceso de rechazo => WARN
    if rejection_rate > policy.max_rejection_rate:
        return QualityGateDecision(
            decision="WARN",
            rationale=(
                "Rejection rate above threshold: "
                f"{rejection_rate:.4f} > {policy.max_rejection_rate:.4f}"
            ),
            policy_id=policy.policy_id,
            metrics_snapshot={
                "acceptance_rate": _round4(acceptance_rate),
                "rejection_rate": _round4(rejection_rate),
            },
        )

    # Regla 2: aceptación demasiado baja => WARN
    if acceptance_rate < policy.min_acceptance_rate:
        return QualityGateDecision(
            decision="WARN",
            rationale=(
                "Acceptance rate below minimum: "
                f"{acceptance_rate:.4f} < {policy.min_acceptance_rate:.4f}"
            ),
            policy_id=policy.policy_id,
            metrics_snapshot={
                "acceptance_rate": _round4(acceptance_rate),
                "rejection_rate": _round4(rejection_rate),
            },
        )

    return QualityGateDecision(
        decision="PASS",
        rationale="Quality gate passed",
        policy_id=policy.policy_id,
        metrics_snapshot={
            "acceptance_rate": _round4(acceptance_rate),
            "rejection_rate": _round4(rejection_rate),
        },
    )


def build_quality_report(
    run_id: str,
    total: int,
    valid: int,
    invalid: int,
    failures_by_rule: dict[str, list[str]],
) -> QualityReport:
    """
    Construye un reporte de calidad 'audit-friendly':
    - totales
    - detalle por regla con ejemplos
    - notas para interpretación

    Importante: el payload extendido (tasas + quality gate) se construye
    determinísticamente en write_quality_report para mantener inmutabilidad
    del modelo QualityReport (frozen dataclass).
    """
    rule_details: list[QualityRuleDetail] = []
    for rule_id, examples in sorted(failures_by_rule.items()):
        failed_count = len(examples)
        pass_rate = 0.0 if total == 0 else (total - failed_count) / total
        rule_details.append(
            QualityRuleDetail(
                rule_id=rule_id,
                failed_count=failed_count,
                pass_rate=_round4(pass_rate),
                examples=examples[:3],
            )
        )

    notes = [
        "pass_rate computed as (total - failed_count)/total per rule_id",
        "examples are record ids (id_solicitud) for quick audit sampling",
        "rates (acceptance/rejection) are computed from totals at write time",
        "quality_gate decision is deterministic given policy + computed rates",
    ]

    return QualityReport(
        run_id=run_id,
        generated_utc=utc_now_iso(),
        totals=WorkflowStats(total=total, valid=valid, invalid=invalid),
        rule_details=rule_details,
        notes=notes,
    )


def write_quality_report(
    path: Path,
    report: QualityReport,
    *,
    policy: QualityGatePolicy | None = None,
) -> None:
    """
    Escribe el JSON final incluyendo:
    - estructura base (compatible con el challenge)
    - métricas ejecutivas (tasas)
    - failure_rate_by_rule
    - decisión automatizada del quality gate (policy versionable)
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    total = report.totals.total
    valid = report.totals.valid
    invalid = report.totals.invalid

    acceptance_rate = _safe_rate(valid, total)
    rejection_rate = _safe_rate(invalid, total)

    # Reconstruimos failures_by_rule desde rule_details (determinístico)
    # Nota: report.rule_details.failed_count es suficiente para failure_rate_by_rule.
    failure_rate_by_rule: dict[str, float] = {
        d.rule_id: _round4(_safe_rate(d.failed_count, total)) for d in report.rule_details
    }

    effective_policy = policy or QualityGatePolicy()
    gate = evaluate_quality_gate(
        acceptance_rate=acceptance_rate,
        rejection_rate=rejection_rate,
        policy=effective_policy,
    )

    payload: dict[str, object] = {
        "schema": "ai_factory.workflow.data_quality_report.v1",
        "run_id": report.run_id,
        "generated_utc": report.generated_utc,
        "totals": {
            "total": total,
            "valid": valid,
            "invalid": invalid,
            "acceptance_rate": _round4(acceptance_rate),
            "rejection_rate": _round4(rejection_rate),
        },
        "rule_details": [
            {
                "rule_id": d.rule_id,
                "failed_count": d.failed_count,
                "pass_rate": d.pass_rate,
                "examples": d.examples,
            }
            for d in report.rule_details
        ],
        "failure_rate_by_rule": failure_rate_by_rule,
        "quality_gate": {
            "policy": {
                "policy_id": effective_policy.policy_id,
                "max_rejection_rate": _round4(effective_policy.max_rejection_rate),
                "min_acceptance_rate": _round4(effective_policy.min_acceptance_rate),
            },
            "decision": gate.decision,
            "rationale": gate.rationale,
            "metrics_snapshot": gate.metrics_snapshot,
        },
        "notes": report.notes,
    }

    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def failures_dict() -> dict[str, list[str]]:
    return defaultdict(list)

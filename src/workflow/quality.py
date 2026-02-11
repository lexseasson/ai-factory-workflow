from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from workflow.models import QualityReport, QualityRuleDetail, WorkflowStats


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def build_quality_report(
    run_id: str,
    total: int,
    valid: int,
    invalid: int,
    failures_by_rule: dict[str, list[str]],
) -> QualityReport:
    rule_details: list[QualityRuleDetail] = []
    for rule_id, examples in sorted(failures_by_rule.items()):
        failed_count = len(examples)
        pass_rate = 0.0 if total == 0 else (total - failed_count) / total
        rule_details.append(
            QualityRuleDetail(
                rule_id=rule_id,
                failed_count=failed_count,
                pass_rate=round(pass_rate, 4),
                examples=examples[:3],
            )
        )

    notes = [
        "pass_rate computed as (total - failed_count)/total per rule_id",
        "examples are record ids (id_solicitud) for quick audit sampling",
    ]

    return QualityReport(
        run_id=run_id,
        generated_utc=utc_now_iso(),
        totals=WorkflowStats(total=total, valid=valid, invalid=invalid),
        rule_details=rule_details,
        notes=notes,
    )


def write_quality_report(path: Path, report: QualityReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": report.run_id,
        "generated_utc": report.generated_utc,
        "totals": {
            "total": report.totals.total,
            "valid": report.totals.valid,
            "invalid": report.totals.invalid,
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
        "notes": report.notes,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def failures_dict() -> dict[str, list[str]]:
    return defaultdict(list)

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from workflow.audit import AuditEvent, AuditLogger, StageTimer, utc_now_iso
from workflow.engine import validate
from workflow.io import InputFormatError, read_requests, write_clean_csv
from workflow.normalize import NormalizationError, normalize
from workflow.quality import (
    QualityGatePolicy,
    build_quality_report,
    evaluate_quality_gate,
    failures_dict,
    write_quality_report,
)
from workflow.rules import AmountRangeRule, CurrencyAllowedRule, RequiredFieldsRule, Rule

PIPELINE_VERSION = "0.2.0"
MANIFEST_SCHEMA = "ai_factory.workflow.run_manifest.v2"


class WorkflowError(RuntimeError):
    """Fatal error for the workflow run."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI Factory - Backoffice Admission Workflow")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--format",
        type=str,
        default="auto",
        choices=["auto", "csv", "json", "txt", "cobol"],
        help="Input format: auto (extension), csv, json, txt-delimited, cobol-fixed-width",
    )
    parser.add_argument("--out", type=Path, default=Path("artifacts"))
    parser.add_argument("--run-label", type=str, default="")
    return parser.parse_args()


def _safe_label(value: str) -> str:
    value = value.strip()
    if not value:
        return "run"
    return "".join(c if c.isalnum() or c in {"-", "_"} else "_" for c in value)


def _run_key(run_id: str, label: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y-%m-%d_%H%M%SZ")
    return f"{stamp}__{_safe_label(label)}__{run_id[:8]}"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _relpath(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except Exception:
        return str(path)


def main() -> int:
    args = parse_args()
    run_id = str(uuid.uuid4())
    run_label = args.run_label.strip() or args.input.stem
    run_key = _run_key(run_id, run_label)

    run_dir = args.out / "runs" / run_key
    run_dir.mkdir(parents=True, exist_ok=True)

    decision_log_path = run_dir / "decision_log.jsonl"
    normalized_path = run_dir / "normalized_requests.csv"
    rejected_path = run_dir / "rejected_requests.csv"
    quality_path = run_dir / "data_quality_report.json"
    manifest_path = run_dir / "run_manifest.json"

    audit = AuditLogger(decision_log_path)
    total_timer = StageTimer()

    def log(level: str, stage: str, event: str, message: str, **extra: Any) -> None:
        audit.emit(
            AuditEvent(
                ts_utc=utc_now_iso(),
                level=level,
                run_id=run_id,
                stage=stage,
                event=event,
                message=message,
                extra=extra or None,
            )
        )

    manifest: dict[str, Any] = {
        "schema": MANIFEST_SCHEMA,
        "pipeline": {
            "version": PIPELINE_VERSION,
            "component": "backoffice_admission_workflow",
        },
        "run": {
            "run_id": run_id,
            "run_key": run_key,
            "run_label": run_label,
            "folder": str(run_dir),
            "generated_utc": utc_now_iso(),
            "status": "RUNNING",
        },
        "environment": {
            "python_version": platform.python_version(),
            "platform": f"{platform.system().lower()}-{platform.release()}",
            "argv": sys.argv,
        },
        "input": {
            "path": str(args.input),
            "format": args.format,
            "sha256": _sha256_file(args.input) if args.input.exists() else None,
        },
        "artifacts": {
            "decision_log": _relpath(decision_log_path, run_dir),
            "normalized_requests": _relpath(normalized_path, run_dir),
            "rejected_requests": _relpath(rejected_path, run_dir),
            "data_quality_report": _relpath(quality_path, run_dir),
            "run_manifest": _relpath(manifest_path, run_dir),
        },
    }
    _write_json(manifest_path, manifest)

    log(
        "INFO",
        "workflow",
        "run_started",
        "Workflow execution started",
        run_key=run_key,
        run_label=run_label,
        input_path=str(args.input),
        input_format=args.format,
        output_dir=str(run_dir),
    )

    ingest_timer = StageTimer()
    try:
        raw_rows = read_requests(args.input, input_format=args.format)
        log(
            "INFO",
            "ingest",
            "input_loaded",
            "Input file loaded",
            rows=len(raw_rows),
            input_format=args.format,
            elapsed_ms=ingest_timer.elapsed_ms(),
        )
    except InputFormatError as exc:
        manifest["run"]["status"] = "FAILED"
        manifest["run"]["failed_stage"] = "ingest"
        manifest["run"]["error"] = str(exc)
        manifest["run"]["generated_utc"] = utc_now_iso()
        _write_json(manifest_path, manifest)
        log("ERROR", "ingest", "input_invalid", str(exc), elapsed_ms=ingest_timer.elapsed_ms())
        return 2

    rules: list[Rule] = [
        RequiredFieldsRule(),
        CurrencyAllowedRule(),
        AmountRangeRule(),
    ]
    manifest["rules"] = [
        {"rule_id": r.rule_id, "severity": str(r.severity), "scope": "eligibility"} for r in rules
    ]
    _write_json(manifest_path, manifest)

    failures_by_rule = failures_dict()
    clean_out: list[dict[str, object]] = []
    rejected_out: list[dict[str, object]] = []

    valid = 0
    invalid = 0

    process_timer = StageTimer()

    for raw in raw_rows:
        record_id = raw.id_solicitud.strip()

        try:
            normalized = normalize(raw)
        except NormalizationError as exc:
            invalid += 1
            failures_by_rule["NORMALIZATION_ERROR"].append(record_id)
            rejected_out.append(
                {
                    "id_solicitud": record_id,
                    "reject_rule_ids": "NORMALIZATION_ERROR",
                    "reject_reasons": str(exc),
                }
            )
            log(
                "WARN",
                "normalize",
                "record_rejected",
                "Normalization failed",
                record_id=record_id,
                rule_id="NORMALIZATION_ERROR",
                reason=str(exc),
            )
            continue

        result = validate(normalized, rules)

        if result.decision.value == "ACCEPT":
            valid += 1
            clean_out.append(
                {
                    "id_solicitud": normalized.id_solicitud,
                    "fecha_solicitud": normalized.fecha_solicitud.isoformat(),
                    "tipo_producto": normalized.tipo_producto,
                    "id_cliente": normalized.id_cliente,
                    "monto_o_limite": normalized.monto_o_limite,
                    "moneda": normalized.moneda,
                    "pais": normalized.pais,
                    "is_vip": normalized.is_vip,
                    "risk_score": normalized.risk_score,
                    "risk_bucket": normalized.risk_bucket,
                }
            )
        else:
            invalid += 1
            rule_ids = [f.rule_id for f in result.failures]
            reasons = [f.reason for f in result.failures]

            for failure in result.failures:
                failures_by_rule[failure.rule_id].append(record_id)
                log(
                    "WARN",
                    "validate",
                    "record_rejected",
                    "Eligibility rule failed",
                    record_id=record_id,
                    rule_id=failure.rule_id,
                    reason=failure.reason,
                )

            rejected_out.append(
                {
                    "id_solicitud": normalized.id_solicitud,
                    "fecha_solicitud": normalized.fecha_solicitud.isoformat(),
                    "tipo_producto": normalized.tipo_producto,
                    "id_cliente": normalized.id_cliente,
                    "monto_o_limite": normalized.monto_o_limite,
                    "moneda": normalized.moneda,
                    "pais": normalized.pais,
                    "is_vip": normalized.is_vip,
                    "risk_score": normalized.risk_score,
                    "risk_bucket": normalized.risk_bucket,
                    "reject_rule_ids": "|".join(rule_ids),
                    "reject_reasons": " | ".join(reasons),
                }
            )

    log(
        "INFO",
        "process",
        "processing_completed",
        "Processing completed",
        total=len(raw_rows),
        valid=valid,
        invalid=invalid,
        elapsed_ms=process_timer.elapsed_ms(),
    )

    output_timer = StageTimer()

    write_clean_csv(normalized_path, clean_out)
    write_clean_csv(rejected_path, rejected_out)

    quality_report = build_quality_report(
        run_id=run_id,
        total=len(raw_rows),
        valid=valid,
        invalid=invalid,
        failures_by_rule=dict(failures_by_rule),
    )

    policy = QualityGatePolicy()
    write_quality_report(quality_path, quality_report, policy=policy)

    log(
        "INFO",
        "output",
        "artifacts_written",
        "Artifacts generated",
        elapsed_ms=output_timer.elapsed_ms(),
        normalized_requests=_relpath(normalized_path, run_dir),
        rejected_requests=_relpath(rejected_path, run_dir),
        data_quality_report=_relpath(quality_path, run_dir),
        decision_log=_relpath(decision_log_path, run_dir),
    )

    total_records = len(raw_rows)
    acceptance_rate = 0.0 if total_records <= 0 else valid / total_records
    rejection_rate = 0.0 if total_records <= 0 else invalid / total_records

    gate = evaluate_quality_gate(
        acceptance_rate=acceptance_rate,
        rejection_rate=rejection_rate,
        policy=policy,
    )

    manifest["quality_gate"] = {
        "policy": {
            "policy_id": policy.policy_id,
            "max_rejection_rate": round(policy.max_rejection_rate, 4),
            "min_acceptance_rate": round(policy.min_acceptance_rate, 4),
        },
        "decision": gate.decision,
        "rationale": gate.rationale,
        "metrics_snapshot": gate.metrics_snapshot,
        "evidence": _relpath(quality_path, run_dir),
    }

    log(
        "INFO",
        "governance",
        "quality_gate_evaluated",
        "Quality gate evaluated",
        decision=gate.decision,
        policy_id=policy.policy_id,
        acceptance_rate=round(acceptance_rate, 4),
        rejection_rate=round(rejection_rate, 4),
        evidence=_relpath(quality_path, run_dir),
    )

    manifest["counts"] = {
        "total": total_records,
        "valid": valid,
        "invalid": invalid,
    }
    manifest["run"]["elapsed_ms_total"] = total_timer.elapsed_ms()
    manifest["run"]["status"] = "SUCCESS" if gate.decision == "PASS" else "COMPLETED_WITH_WARNINGS"
    manifest["run"]["generated_utc"] = utc_now_iso()

    _write_json(manifest_path, manifest)

    log(
        "INFO",
        "workflow",
        "run_finished",
        "Workflow execution finished",
        status=manifest["run"]["status"],
        elapsed_ms=total_timer.elapsed_ms(),
    )

    print(f"run_id={run_id}")
    print(f"run_key={run_key}")
    print(f"run_dir={run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

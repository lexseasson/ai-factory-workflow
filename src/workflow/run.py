# src/workflow/run.py
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shlex
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
    p = argparse.ArgumentParser(description="AI Factory – Backoffice Admission Workflow")
    p.add_argument("--input", type=Path, required=True, help="Input file path")
    p.add_argument("--out", type=Path, default=Path("artifacts"), help="Output base dir")
    p.add_argument(
        "--run-label",
        type=str,
        default="",
        help="Optional human label for the run folder (default: input filename stem)",
    )
    p.add_argument(
        "--format",
        type=str,
        default="auto",
        help="Input format: auto|csv|json|txt|cobol (default: auto)",
    )
    return p.parse_args()


def _safe_label(s: str) -> str:
    s = s.strip()
    if not s:
        return "run"
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in s)


def _run_key(run_id: str, label: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y-%m-%d_%H%M%SZ")
    return f"{stamp}__{_safe_label(label)}__{run_id[:8]}"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_or_none(path: Path) -> str | None:
    if not path.exists():
        return None
    return _sha256_file(path)


def _relpath(p: Path, base: Path) -> str:
    try:
        return str(p.relative_to(base))
    except Exception:
        return str(p)


def _resolve_format(input_path: Path, requested: str) -> str:
    fmt = requested.lower().strip()
    if fmt != "auto":
        return fmt

    suffix = input_path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix == ".json":
        return "json"
    if suffix == ".txt":
        return "txt"
    if suffix in {".dat", ".cob"}:
        return "cobol"
    return "unknown"


def _command_string(argv: list[str]) -> str:
    # En Windows también sirve como “replay” humano.
    return " ".join(shlex.quote(a) for a in argv)


def main() -> int:
    args = parse_args()

    run_id = str(uuid.uuid4())
    run_label = args.run_label.strip() or args.input.stem
    run_key = _run_key(run_id, run_label)

    run_dir = args.out / "runs" / run_key
    run_dir.mkdir(parents=True, exist_ok=True)

    # Artefactos con naming “de negocio”
    decision_log_path = run_dir / "decision_log.jsonl"
    normalized_path = run_dir / "normalized_requests.csv"
    rejected_path = run_dir / "rejected_requests.csv"
    quality_path = run_dir / "data_quality_report.json"
    manifest_path = run_dir / "run_manifest.json"

    audit = AuditLogger(decision_log_path)
    t_all = StageTimer()

    run_start_utc = utc_now_iso()
    fmt_resolved = _resolve_format(args.input, args.format)

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

    # --------------------------
    # MANIFEST BASE (CONTRATO)
    # --------------------------
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
            "status": "RUNNING",
            "start_utc": run_start_utc,
            "end_utc": None,
            "elapsed_ms_total": None,
            "command": _command_string(sys.argv),
        },
        "environment": {
            "python_version": platform.python_version(),
            "platform": f"{platform.system().lower()}-{platform.release()}",
            "argv": sys.argv,
        },
        "input": {
            "path": str(args.input),
            # Alias “contract-friendly” (lo usa el test y es razonable para auditoría)
            "format": fmt_resolved,
            # Campos explícitos (mejor semántica)
            "format_requested": args.format,
            "format_resolved": fmt_resolved,
            "sha256": _sha256_or_none(args.input),
        },
        "quality_gate": {
            "policy_id": "quality_gate.v1",
            "inputs": {
                "acceptance_rate": "counts.valid / counts.total",
                "rejection_rate": "counts.invalid / counts.total",
            },
            "decision": None,
            "rationale": None,
            "metrics_snapshot": None,
            "evidence": _relpath(quality_path, run_dir),
        },
        "artifacts": {
            "decision_log": _relpath(decision_log_path, run_dir),
            "normalized_requests": _relpath(normalized_path, run_dir),
            "rejected_requests": _relpath(rejected_path, run_dir),
            "data_quality_report": _relpath(quality_path, run_dir),
            "run_manifest": _relpath(manifest_path, run_dir),
        },
        "artifacts_integrity": {},
        "rules": [],
        "counts": None,
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
        output_dir=str(run_dir),
        format_requested=args.format,
        format_resolved=fmt_resolved,
    )

    # --------------------------
    # INGEST
    # --------------------------
    t_ingest = StageTimer()
    try:
        raw_rows = read_requests(args.input, input_format=args.format)
        log(
            "INFO",
            "ingest",
            "input_loaded",
            "Input file loaded",
            rows=len(raw_rows),
            elapsed_ms=t_ingest.elapsed_ms(),
            input_format=fmt_resolved,
        )
    except InputFormatError as exc:
        manifest["run"]["status"] = "FAILED"
        manifest["run"]["end_utc"] = utc_now_iso()
        manifest["run"]["elapsed_ms_total"] = t_all.elapsed_ms()
        manifest["run"]["error"] = str(exc)
        _write_json(manifest_path, manifest)
        log("ERROR", "ingest", "input_invalid", str(exc), elapsed_ms=t_ingest.elapsed_ms())
        return 2

    # --------------------------
    # RULES (ELEGIBILIDAD)
    # --------------------------
    rules: list[Rule] = [RequiredFieldsRule(), CurrencyAllowedRule(), AmountRangeRule()]
    manifest["rules"] = [
        {"rule_id": r.rule_id, "severity": str(r.severity), "scope": "eligibility"} for r in rules
    ]
    _write_json(manifest_path, manifest)

    failures_by_rule = failures_dict()
    clean_out: list[dict[str, object]] = []
    rejected_out: list[dict[str, object]] = []

    valid = 0
    invalid = 0

    # --------------------------
    # PROCESS (NORMALIZE + VALIDATE)
    # --------------------------
    t_process = StageTimer()

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
            for f in result.failures:
                failures_by_rule[f.rule_id].append(record_id)

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
                "WARN",
                "validate",
                "record_rejected",
                "Eligibility rule failed",
                record_id=record_id,
                rule_ids=rule_ids,
            )

    log(
        "INFO",
        "process",
        "processing_completed",
        "Processing completed",
        total=len(raw_rows),
        valid=valid,
        invalid=invalid,
        elapsed_ms=t_process.elapsed_ms(),
    )

    # --------------------------
    # OUTPUTS + QUALITY REPORT
    # --------------------------
    t_out = StageTimer()

    write_clean_csv(normalized_path, clean_out)
    write_clean_csv(rejected_path, rejected_out)

    quality_report = build_quality_report(
        run_id=run_id,
        total=len(raw_rows),
        valid=valid,
        invalid=invalid,
        failures_by_rule=dict(failures_by_rule),
    )
    write_quality_report(quality_path, quality_report)

    log(
        "INFO",
        "output",
        "artifacts_written",
        "Artifacts generated",
        elapsed_ms=t_out.elapsed_ms(),
        normalized_requests=_relpath(normalized_path, run_dir),
        rejected_requests=_relpath(rejected_path, run_dir),
        data_quality_report=_relpath(quality_path, run_dir),
        decision_log=_relpath(decision_log_path, run_dir),
    )

    # --------------------------
    # GOVERNANCE: QUALITY GATE (POLÍTICA + DECISIÓN + EVIDENCIA)
    # --------------------------
    total_records = len(raw_rows)
    acceptance_rate = 0.0 if total_records <= 0 else valid / total_records
    rejection_rate = 0.0 if total_records <= 0 else invalid / total_records

    policy = QualityGatePolicy()
    gate = evaluate_quality_gate(
        acceptance_rate=acceptance_rate,
        rejection_rate=rejection_rate,
        policy=policy,
    )

    manifest["counts"] = {"total": total_records, "valid": valid, "invalid": invalid}
    manifest["quality_gate"] = {
        "policy": {
            "policy_id": policy.policy_id,
            "max_rejection_rate": round(policy.max_rejection_rate, 4),
            "min_acceptance_rate": round(policy.min_acceptance_rate, 4),
        },
        "inputs": {
            "acceptance_rate": "counts.valid / counts.total",
            "rejection_rate": "counts.invalid / counts.total",
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
        rationale=gate.rationale,
        acceptance_rate=round(acceptance_rate, 4),
        rejection_rate=round(rejection_rate, 4),
        policy_id=policy.policy_id,
    )

    # --------------------------
    # INTEGRIDAD DE ARTEFACTOS (CHAIN-OF-CUSTODY)
    # --------------------------
    integrity: dict[str, dict[str, str | None]] = {}
    artifacts_obj = manifest.get("artifacts", {})
    if isinstance(artifacts_obj, dict):
        for name, rel in artifacts_obj.items():
            if not isinstance(rel, str):
                continue
            p = run_dir / rel
            integrity[str(name)] = {"path": rel, "sha256": _sha256_or_none(p)}

    manifest["artifacts_integrity"] = integrity

    # --------------------------
    # FINALIZE MANIFEST
    # --------------------------
    manifest["run"]["status"] = "SUCCESS" if gate.decision == "PASS" else "COMPLETED_WITH_WARNINGS"
    manifest["run"]["end_utc"] = utc_now_iso()
    manifest["run"]["elapsed_ms_total"] = t_all.elapsed_ms()
    _write_json(manifest_path, manifest)

    log(
        "INFO",
        "workflow",
        "run_finished",
        "Workflow execution finished",
        status=manifest["run"]["status"],
        elapsed_ms_total=manifest["run"]["elapsed_ms_total"],
    )

    print(f"run_id={run_id}")
    print(f"run_key={run_key}")
    print(f"run_dir={run_dir}")
    print(f"status={manifest['run']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

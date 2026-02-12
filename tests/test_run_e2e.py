from __future__ import annotations

import json
import sys
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch

from workflow.run import main


def test_run_e2e_json_input_generates_artifacts(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    input_path = tmp_path / "requests.json"
    out_dir = tmp_path / "artifacts"

    input_payload = [
        {
            "id_solicitud": "REQ-5001",
            "fecha_solicitud": "2026-02-10",
            "tipo_producto": "cuenta",
            "id_cliente": "CLI-9001",
            "monto_o_limite": "1000",
            "moneda": "ARS",
            "pais": "AR",
            "is_vip": "false",
            "risk_score": "15",
        },
        {
            "id_solicitud": "REQ-5002",
            "fecha_solicitud": "2026-02-11",
            "tipo_producto": "tarjeta",
            "id_cliente": "CLI-9002",
            "monto_o_limite": "0",
            "moneda": "USD",
            "pais": "AR",
            "is_vip": "true",
            "risk_score": "40",
        },
    ]
    input_path.write_text(json.dumps(input_payload), encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "workflow.run",
            "--input",
            str(input_path),
            "--format",
            "json",
            "--out",
            str(out_dir),
            "--run-label",
            "e2e_json",
        ],
    )
    rc = main()
    assert rc == 0

    run_base = out_dir / "runs"
    run_dirs = [p for p in run_base.iterdir() if p.is_dir()]
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    quality = json.loads((run_dir / "data_quality_report.json").read_text(encoding="utf-8"))

    assert manifest["input"]["format"] == "json"
    assert manifest["counts"]["total"] == 2
    assert quality["totals"]["total"] == 2
    assert (run_dir / "decision_log.jsonl").exists()
    assert (run_dir / "normalized_requests.csv").exists()
    assert (run_dir / "rejected_requests.csv").exists()

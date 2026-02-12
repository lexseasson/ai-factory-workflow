from __future__ import annotations

import json
from pathlib import Path

from workflow.io import read_requests


def _fw(value: str, width: int) -> str:
    return value[:width].ljust(width)


def _build_cobol_line(
    *,
    id_solicitud: str,
    fecha_solicitud: str,
    tipo_producto: str,
    id_cliente: str,
    monto_o_limite: str,
    moneda: str,
    pais: str,
    is_vip: str,
    risk_score: str,
) -> str:
    return "".join(
        [
            _fw(id_solicitud, 12),
            _fw(fecha_solicitud, 10),
            _fw(tipo_producto, 12),
            _fw(id_cliente, 12),
            _fw(monto_o_limite, 12),
            _fw(moneda, 3),
            _fw(pais, 2),
            _fw(is_vip, 5),
            _fw(risk_score, 3),
        ]
    )


def test_read_json_format(tmp_path: Path) -> None:
    p = tmp_path / "input.json"
    payload = [
        {
            "id_solicitud": "REQ-1",
            "fecha_solicitud": "2026-02-10",
            "tipo_producto": "cuenta",
            "id_cliente": "CLI-1",
            "monto_o_limite": "1000",
            "moneda": "ARS",
            "pais": "AR",
            "is_vip": "false",
            "risk_score": "20",
        }
    ]
    p.write_text(json.dumps(payload), encoding="utf-8")

    rows = read_requests(p, input_format="json")
    assert len(rows) == 1
    assert rows[0].id_solicitud == "REQ-1"


def test_read_txt_delimited_format(tmp_path: Path) -> None:
    p = tmp_path / "input.txt"
    p.write_text(
        (
            "id_solicitud|fecha_solicitud|tipo_producto|id_cliente|monto_o_limite|"
            "moneda|pais|is_vip|risk_score\n"
            "REQ-2|2026-02-10|tarjeta|CLI-2|2000|USD|AR|true|10\n"
        ),
        encoding="utf-8",
    )

    rows = read_requests(p, input_format="txt")
    assert len(rows) == 1
    assert rows[0].id_cliente == "CLI-2"


def test_read_cobol_fixed_width_format(tmp_path: Path) -> None:
    p = tmp_path / "input.cob"
    line = _build_cobol_line(
        id_solicitud="REQ-3",
        fecha_solicitud="2026-02-10",
        tipo_producto="servicio",
        id_cliente="CLI-3",
        monto_o_limite="3000",
        moneda="EUR",
        pais="UY",
        is_vip="false",
        risk_score="55",
    )
    p.write_text(line + "\n", encoding="utf-8")

    rows = read_requests(p, input_format="cobol")
    assert len(rows) == 1
    assert rows[0].moneda == "EUR"

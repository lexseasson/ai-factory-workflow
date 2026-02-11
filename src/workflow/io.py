from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

from workflow.models import RawRequest

REQUIRED_COLUMNS: tuple[str, ...] = (
    "id_solicitud",
    "fecha_solicitud",
    "tipo_producto",
    "id_cliente",
    "monto_o_limite",
    "moneda",
    "pais",
    "is_vip",
    "risk_score",
)


class InputFormatError(ValueError):
    pass


def read_csv(path: Path) -> list[RawRequest]:
    if not path.exists():
        raise InputFormatError(f"Input file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise InputFormatError("CSV has no header row")

        missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            raise InputFormatError(f"CSV missing required columns: {missing}")

        rows: list[RawRequest] = []
        for row in reader:

            def g(row_: dict[str, str | None], k: str) -> str:
                v = row_.get(k)
                return "" if v is None else str(v)

            rows.append(
                RawRequest(
                    id_solicitud=g(row, "id_solicitud"),
                    fecha_solicitud=g(row, "fecha_solicitud"),
                    tipo_producto=g(row, "tipo_producto"),
                    id_cliente=g(row, "id_cliente"),
                    monto_o_limite=g(row, "monto_o_limite"),
                    moneda=g(row, "moneda"),
                    pais=g(row, "pais"),
                    is_vip=g(row, "is_vip"),
                    risk_score=g(row, "risk_score"),
                )
            )
        return rows


def write_clean_csv(path: Path, rows: Iterable[dict[str, object]]) -> None:
    rows_list = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows_list:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows_list[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_list)

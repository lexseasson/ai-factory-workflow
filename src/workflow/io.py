from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
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


@dataclass(frozen=True)
class FixedWidthField:
    name: str
    start: int
    end: int


DEFAULT_COBOL_LAYOUT: tuple[FixedWidthField, ...] = (
    FixedWidthField("id_solicitud", 0, 12),
    FixedWidthField("fecha_solicitud", 12, 22),
    FixedWidthField("tipo_producto", 22, 34),
    FixedWidthField("id_cliente", 34, 46),
    FixedWidthField("monto_o_limite", 46, 58),
    FixedWidthField("moneda", 58, 61),
    FixedWidthField("pais", 61, 63),
    FixedWidthField("is_vip", 63, 68),
    FixedWidthField("risk_score", 68, 71),
)


def _build_raw_request(row: Mapping[str, object | None]) -> RawRequest:
    def g(k: str) -> str:
        v = row.get(k)
        return "" if v is None else str(v)

    return RawRequest(
        id_solicitud=g("id_solicitud"),
        fecha_solicitud=g("fecha_solicitud"),
        tipo_producto=g("tipo_producto"),
        id_cliente=g("id_cliente"),
        monto_o_limite=g("monto_o_limite"),
        moneda=g("moneda"),
        pais=g("pais"),
        is_vip=g("is_vip"),
        risk_score=g("risk_score"),
    )


def _assert_required_columns(cols: Iterable[str]) -> None:
    colset = set(cols)
    missing = [c for c in REQUIRED_COLUMNS if c not in colset]
    if missing:
        raise InputFormatError(f"Input missing required columns: {missing}")


def read_csv(path: Path) -> list[RawRequest]:
    if not path.exists():
        raise InputFormatError(f"Input file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise InputFormatError("CSV has no header row")
        _assert_required_columns(reader.fieldnames)
        return [_build_raw_request(dict(row)) for row in reader]


def read_json(path: Path) -> list[RawRequest]:
    if not path.exists():
        raise InputFormatError(f"Input file not found: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise InputFormatError(f"Invalid JSON file: {path}") from exc

    if isinstance(payload, dict) and "requests" in payload:
        records = payload.get("requests")
    else:
        records = payload

    if not isinstance(records, list):
        raise InputFormatError("JSON root must be a list or object with 'requests' list")

    rows: list[RawRequest] = []
    for i, item in enumerate(records):
        if not isinstance(item, dict):
            raise InputFormatError(f"JSON record at index {i} is not an object")
        _assert_required_columns(item.keys())
        rows.append(_build_raw_request(item))
    return rows


def _detect_delimiter(header_line: str) -> str | None:
    for candidate in ("|", "\t", ";", ","):
        if candidate in header_line:
            return candidate
    return None


def read_txt_delimited(path: Path) -> list[RawRequest]:
    if not path.exists():
        raise InputFormatError(f"Input file not found: {path}")

    lines = path.read_text(encoding="utf-8-sig").splitlines()
    non_empty = [ln for ln in lines if ln.strip()]
    if not non_empty:
        raise InputFormatError("TXT input is empty")

    delim = _detect_delimiter(non_empty[0])
    if delim is None:
        raise InputFormatError(
            "TXT format not recognized as delimited text; use --format cobol for fixed-width files"
        )

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delim)
        if reader.fieldnames is None:
            raise InputFormatError("TXT has no header row")
        _assert_required_columns(reader.fieldnames)
        return [_build_raw_request(dict(row)) for row in reader]


def read_cobol_fixed_width(
    path: Path, layout: tuple[FixedWidthField, ...] = DEFAULT_COBOL_LAYOUT
) -> list[RawRequest]:
    if not path.exists():
        raise InputFormatError(f"Input file not found: {path}")

    rows: list[RawRequest] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        row = {f.name: line[f.start : f.end].strip() for f in layout}
        _assert_required_columns(row.keys())
        rows.append(_build_raw_request(row))

    if not rows:
        raise InputFormatError("Fixed-width input has no data rows")
    return rows


def read_requests(path: Path, input_format: str = "auto") -> list[RawRequest]:
    fmt = input_format.lower().strip()
    if fmt == "auto":
        suffix = path.suffix.lower()
        if suffix == ".csv":
            fmt = "csv"
        elif suffix == ".json":
            fmt = "json"
        elif suffix in {".txt"}:
            fmt = "txt"
        elif suffix in {".dat", ".cob"}:
            fmt = "cobol"
        else:
            raise InputFormatError(
                f"Unsupported input extension '{suffix}'. Use --format csv|json|txt|cobol"
            )

    if fmt == "csv":
        return read_csv(path)
    if fmt == "json":
        return read_json(path)
    if fmt == "txt":
        return read_txt_delimited(path)
    if fmt in {"cobol", "fixed", "fixed-width"}:
        return read_cobol_fixed_width(path)
    raise InputFormatError(f"Unsupported format '{input_format}'. Use csv|json|txt|cobol")


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

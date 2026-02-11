from __future__ import annotations

from datetime import date, datetime

from workflow.models import NormalizedRequest, RawRequest


class NormalizationError(ValueError):
    pass


def _parse_date(s: str) -> date:
    s2 = s.strip()
    # Aceptamos solo ISO YYYY-MM-DD (para mantener claridad y auditabilidad)
    try:
        return datetime.strptime(s2, "%Y-%m-%d").date()
    except Exception as exc:
        raise NormalizationError(
            f"Invalid fecha_solicitud format (expected YYYY-MM-DD): '{s}'"
        ) from exc


def _parse_amount(s: str) -> float:
    s2 = s.strip()
    if s2 == "":
        raise NormalizationError("monto_o_limite is empty")
    try:
        return float(s2)
    except Exception as exc:
        raise NormalizationError(f"monto_o_limite is not numeric: '{s}'") from exc


def _parse_bool(s: str) -> bool:
    s2 = s.strip().lower()
    if s2 in {"true", "1", "yes", "y"}:
        return True
    if s2 in {"false", "0", "no", "n"}:
        return False
    raise NormalizationError(f"is_vip is not a boolean: '{s}'")


def _parse_int(s: str) -> int:
    s2 = s.strip()
    if s2 == "":
        raise NormalizationError("risk_score is empty")
    try:
        return int(s2)
    except Exception as exc:
        raise NormalizationError(f"risk_score is not an int: '{s}'") from exc


def _risk_bucket(score: int) -> str:
    if score < 34:
        return "LOW"
    if score < 67:
        return "MED"
    return "HIGH"


def normalize(raw: RawRequest) -> NormalizedRequest:
    # trimming + casing
    tipo = raw.tipo_producto.strip().lower()
    moneda = raw.moneda.strip().upper()
    pais = raw.pais.strip().upper()

    return NormalizedRequest(
        id_solicitud=raw.id_solicitud.strip(),
        fecha_solicitud=_parse_date(raw.fecha_solicitud),
        tipo_producto=tipo,
        id_cliente=raw.id_cliente.strip(),
        monto_o_limite=_parse_amount(raw.monto_o_limite),
        moneda=moneda,
        pais=pais,
        is_vip=_parse_bool(raw.is_vip),
        risk_score=_parse_int(raw.risk_score),
        risk_bucket=_risk_bucket(_parse_int(raw.risk_score)),
    )

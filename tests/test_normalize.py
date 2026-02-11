from __future__ import annotations

import pytest

from workflow.models import RawRequest
from workflow.normalize import NormalizationError, normalize


def test_normalize_ok() -> None:
    raw = RawRequest(
        id_solicitud=" REQ-1 ",
        fecha_solicitud="2026-02-10",
        tipo_producto="Cuenta ",
        id_cliente=" CLI-1 ",
        monto_o_limite="1000",
        moneda="ars",
        pais="ar",
        is_vip="true",
        risk_score="40",
    )
    nr = normalize(raw)
    assert nr.id_solicitud == "REQ-1"
    assert nr.moneda == "ARS"
    assert nr.pais == "AR"
    assert nr.risk_bucket in {"LOW", "MED", "HIGH"}


def test_normalize_bad_date() -> None:
    raw = RawRequest(
        id_solicitud="REQ-2",
        fecha_solicitud="2026/02/10",
        tipo_producto="cuenta",
        id_cliente="CLI-2",
        monto_o_limite="1000",
        moneda="ARS",
        pais="AR",
        is_vip="false",
        risk_score="10",
    )
    with pytest.raises(NormalizationError):
        normalize(raw)

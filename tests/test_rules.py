from datetime import date

from workflow.engine import validate
from workflow.models import NormalizedRequest
from workflow.rules import AmountRangeRule, CurrencyAllowedRule, RequiredFieldsRule


def _nr(moneda: str, monto: float, id_cliente: str = "CLI-1") -> NormalizedRequest:
    return NormalizedRequest(
        id_solicitud="REQ-1",
        fecha_solicitud=date(2026, 2, 10),
        tipo_producto="cuenta",
        id_cliente=id_cliente,
        monto_o_limite=monto,
        moneda=moneda,
        pais="AR",
        is_vip=False,
        risk_score=10,
        risk_bucket="LOW",
    )


def test_validate_accept() -> None:
    rules = [RequiredFieldsRule(), CurrencyAllowedRule(), AmountRangeRule()]
    vr = validate(_nr("ARS", 1000), rules)
    assert vr.decision.value == "ACCEPT"


def test_validate_reject_currency() -> None:
    rules = [RequiredFieldsRule(), CurrencyAllowedRule(), AmountRangeRule()]
    vr = validate(_nr("BRL", 1000), rules)
    assert vr.decision.value == "REJECT"
    assert any(f.rule_id == "CURRENCY_ALLOWED" for f in vr.failures)

import xml.etree.ElementTree as ET
from unittest.mock import MagicMock

import pytest

from tools.cc_lists import ConstantContactError, ConstantContactLists
from tools.dp_client import DonorPerfectClient, DonorPerfectError
from tools.reconcile import reconcile


# ---- reconcile --------------------------------------------------------------

def test_reconcile_sets_and_gap():
    rec = reconcile(["A@x.org", "b@x.org", " c@x.org "], ["b@x.org", "c@x.org", "legacy@x.org", "old@x.org"])
    assert rec.missing_from_crm == {"a@x.org"}
    assert rec.stale_in_crm == {"legacy@x.org", "old@x.org"}
    assert rec.gap == 1


def test_reconcile_report_flags_drift():
    rec = reconcile(["a@x.org"], ["a@x.org"] + [f"legacy{i}@x.org" for i in range(40)])
    assert "NEEDS ATTENTION" in rec.report(expected_gap=30, tolerance=5)
    assert "OK" in rec.report(expected_gap=40, tolerance=5)


# ---- DonorPerfect -----------------------------------------------------------

def _dp_with_response(xml_text: str) -> DonorPerfectClient:
    dp = DonorPerfectClient(api_key="test")
    resp = MagicMock(status_code=200, text=xml_text)
    resp.raise_for_status = MagicMock()
    dp.session = MagicMock()
    dp.session.get.return_value = resp
    return dp


def test_dp_find_by_email_parses_rows():
    dp = _dp_with_response(
        '<result><record><field name="donor_id" value="42"/><field name="email" value="a@x.org"/></record></result>'
    )
    row = dp.find_by_email("A@x.org")
    assert row == {"donor_id": "42", "email": "a@x.org"}
    sent = dp.session.get.call_args.kwargs["params"]
    assert sent["apikey"] == "test"
    assert "'a@x.org'" in sent["action"]


def test_dp_raises_on_error_element():
    dp = _dp_with_response("<result><error>Invalid API key</error></result>")
    with pytest.raises(DonorPerfectError):
        dp.query("SELECT 1")


def test_dp_save_params_escape_quotes():
    params = DonorPerfectClient._params(0, {"first_name": "O'Brien", "last_name": "X"})
    assert params.startswith("'0','O''Brien','X'")


# ---- Constant Contact -------------------------------------------------------

def _cc_with(responses: list[tuple[int, dict]]) -> ConstantContactLists:
    cc = ConstantContactLists(access_token="t")
    cc.session = MagicMock()
    mocks = []
    for status, body in responses:
        m = MagicMock(status_code=status, text="x" if body else "")
        m.json.return_value = body
        mocks.append(m)
    cc.session.request.side_effect = mocks
    return cc


def test_cc_list_id_by_name_case_insensitive():
    cc = _cc_with([(200, {"lists": [{"name": "Active Partner List", "list_id": "L1"}]})])
    assert cc.list_id_by_name("active partner list") == "L1"


def test_cc_missing_list_is_explicit_error():
    cc = _cc_with([(200, {"lists": []})])
    with pytest.raises(ConstantContactError, match="renamed or deleted"):
        cc.list_id_by_name("Gone")


def test_cc_remove_only_calls_remove_endpoint_never_unsubscribe():
    cc = _cc_with([
        (200, {"contacts": [{"contact_id": "C1", "list_memberships": ["L1", "L2"]}]}),
        (201, {}),
    ])
    assert cc.remove_from_list("a@x.org", "L1") is True
    calls = [c.args for c in cc.session.request.call_args_list]
    assert calls[1][0] == "POST"
    assert calls[1][1].endswith("/activities/remove_list_memberships")
    assert not any("unsubscribe" in c[1] for c in calls)


def test_cc_remove_when_not_member_is_noop():
    cc = _cc_with([(200, {"contacts": [{"contact_id": "C1", "list_memberships": ["L2"]}]})])
    assert cc.remove_from_list("a@x.org", "L1") is False
    assert cc.session.request.call_count == 1

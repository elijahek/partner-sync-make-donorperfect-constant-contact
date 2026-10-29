"""Minimal DonorPerfect XML API client.

DonorPerfect exposes a single endpoint that accepts an API key plus either a
SQL-style ``dpoquery`` or a named ``action`` such as ``dp_savedonor``. Responses
are XML. This wrapper covers the handful of calls the partner sync needs and
returns plain Python structures.

Usage::

    dp = DonorPerfectClient(api_key=os.environ["DP_API_KEY"])
    donor = dp.find_by_email("someone@example.org")
    dp.set_udf(donor["donor_id"], "IS_PARTNER", "Y")

Never log the API key. Never commit it.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Iterable

import requests

DP_ENDPOINT = "https://www.donorperfect.net/prod/xmlapi/"


class DonorPerfectError(RuntimeError):
    pass


@dataclass
class DonorPerfectClient:
    api_key: str
    endpoint: str = DP_ENDPOINT
    timeout: int = 30
    session: requests.Session = field(default_factory=requests.Session)

    # ---- low level -------------------------------------------------------

    def _get(self, params: dict[str, Any]) -> ET.Element:
        params = {"apikey": self.api_key, **params}
        resp = self.session.get(self.endpoint, params=params, timeout=self.timeout)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        err = root.find(".//error")
        if err is not None and (err.text or "").strip():
            raise DonorPerfectError(err.text.strip())
        return root

    @staticmethod
    def _rows(root: ET.Element) -> list[dict[str, str]]:
        rows = []
        for record in root.iter("record"):
            row = {}
            for f in record.findall("field"):
                name = f.get("name") or f.get("id") or ""
                row[name.lower()] = (f.get("value") if f.get("value") is not None else (f.text or "")).strip()
            rows.append(row)
        return rows

    def query(self, sql: str) -> list[dict[str, str]]:
        """Run a read-only dpoquery and return rows as dicts keyed by lowercase column."""
        return self._rows(self._get({"action": sql}))

    # ---- reads -----------------------------------------------------------

    def find_by_email(self, email: str) -> dict[str, str] | None:
        email = email.strip().replace("'", "''").lower()
        rows = self.query(
            "SELECT donor_id, first_name, last_name, email, address, city, state, zip "
            f"FROM dp WHERE LOWER(email) = '{email}'"
        )
        return rows[0] if rows else None

    def partners(self, flag_field: str = "IS_PARTNER") -> list[dict[str, str]]:
        return self.query(
            f"SELECT d.donor_id, d.email FROM dp d JOIN dpudf u ON u.donor_id = d.donor_id "
            f"WHERE u.{flag_field} = 'Y'"
        )

    # ---- writes ----------------------------------------------------------

    def save_donor(self, donor_id: int | str, **fields: str) -> str:
        """Create (donor_id=0) or update a donor's standard fields. Returns the donor id."""
        params = {"action": "dp_savedonor", "params": self._params(donor_id, fields)}
        root = self._get(params)
        rows = self._rows(root)
        return rows[0].get("donor_id", str(donor_id)) if rows else str(donor_id)

    def set_udf(self, donor_id: int | str, field_name: str, value: str) -> None:
        """Write one user-defined field. Values are passed through unchanged."""
        self._get({
            "action": "dp_save_udf_xml",
            "params": f"'{donor_id}','{field_name}','{self._esc(value)}'",
        })

    # ---- helpers ---------------------------------------------------------

    @staticmethod
    def _esc(value: str) -> str:
        return str(value).replace("'", "''")

    @classmethod
    def _params(cls, donor_id: int | str, fields: dict[str, str]) -> str:
        order = ["first_name", "last_name", "middle_name", "suffix", "title", "salutation",
                 "prof_title", "opt_line", "address", "address2", "city", "state", "zip",
                 "country", "address_type", "home_phone", "business_phone", "fax_phone",
                 "mobile_phone", "email", "org_rec", "donor_type", "nomail", "nomail_reason",
                 "narrative", "user_id"]
        values: Iterable[str] = (cls._esc(fields.get(k, "")) for k in order)
        return f"'{donor_id}'," + ",".join(f"'{v}'" for v in values)

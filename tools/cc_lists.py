"""Constant Contact v3 list-membership helpers.

Design rule baked in: these functions only ever add a contact to a list or
remove it from a list. They never change subscription status, never
unsubscribe, and never delete a contact. If you need those, you want a person,
not a script.

Usage::

    cc = ConstantContactLists(access_token=token)
    list_id = cc.list_id_by_name("Active Partner List")
    cc.add_to_list("someone@example.org", list_id)
    cc.remove_from_list("someone@example.org", list_id)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import requests

CC_BASE = "https://api.cc.email/v3"


class ConstantContactError(RuntimeError):
    pass


@dataclass
class ConstantContactLists:
    access_token: str
    base: str = CC_BASE
    timeout: int = 30
    session: requests.Session = field(default_factory=requests.Session)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

    def _req(self, method: str, path: str, **kw):
        resp = self.session.request(method, f"{self.base}{path}", headers=self._headers(), timeout=self.timeout, **kw)
        if resp.status_code >= 400:
            raise ConstantContactError(f"{method} {path} -> {resp.status_code}: {resp.text[:300]}")
        return resp.json() if resp.text else {}

    # ---- lists -----------------------------------------------------------

    def lists(self) -> list[dict]:
        return self._req("GET", "/contact_lists", params={"include_count": "true", "limit": 1000}).get("lists", [])

    def list_id_by_name(self, name: str) -> str:
        for lst in self.lists():
            if lst.get("name", "").strip().lower() == name.strip().lower():
                return lst["list_id"]
        raise ConstantContactError(f"List not found: {name!r}. It may have been renamed or deleted.")

    # ---- contacts --------------------------------------------------------

    def contact_by_email(self, email: str) -> dict | None:
        data = self._req("GET", "/contacts", params={"email": email.strip().lower(), "include": "list_memberships"})
        contacts = data.get("contacts", [])
        return contacts[0] if contacts else None

    def add_to_list(self, email: str, list_id: str) -> str:
        """Add by email. Creates the contact if needed, with the email as its primary address.

        Uses the sign-up form endpoint, which is additive: it never alters an
        existing contact's subscription status.
        """
        payload = {"email_address": email.strip().lower(), "list_memberships": [list_id]}
        data = self._req("POST", "/contacts/sign_up_form", json=payload)
        return data.get("contact_id", "")

    def remove_from_list(self, email: str, list_id: str) -> bool:
        """Remove from one list. Returns False if the contact or membership doesn't exist."""
        contact = self.contact_by_email(email)
        if not contact:
            return False
        if list_id not in contact.get("list_memberships", []):
            return False
        self._req("POST", "/activities/remove_list_memberships", json={
            "source": {"contact_ids": [contact["contact_id"]]},
            "list_ids": [list_id],
        })
        return True

    def sms_consent_status(self, email: str) -> str | None:
        """Return the SMS consent status ('explicit', 'pending', ...) or None."""
        contact = self.contact_by_email(email)
        if not contact:
            return None
        for ch in contact.get("sms_channel", []) or []:
            consents = ch.get("sms_channel_consents") or []
            if consents:
                return consents[0].get("consent_type")
        return None

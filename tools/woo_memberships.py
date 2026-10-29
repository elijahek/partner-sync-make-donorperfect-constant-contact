"""Read active memberships from WooCommerce Memberships via the WC REST API.

Requires a REST API key pair with read permission (WooCommerce → Settings →
Advanced → REST API). Pass them in; don't hardcode them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

import requests

ACTIVE_STATUSES = {"wcm-active", "wcm-pending", "active", "pending-cancellation", "wcm-pending-cancellation"}


@dataclass
class WooMemberships:
    site: str                       # e.g. https://example.org
    consumer_key: str
    consumer_secret: str
    timeout: int = 30
    session: requests.Session = field(default_factory=requests.Session)

    def _get(self, path: str, **params) -> list[dict]:
        url = f"{self.site.rstrip('/')}/wp-json/wc/v3{path}"
        resp = self.session.get(url, params=params, auth=(self.consumer_key, self.consumer_secret), timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def iter_memberships(self, status: str | None = None) -> Iterator[dict]:
        page = 1
        while True:
            params = {"per_page": 100, "page": page}
            if status:
                params["status"] = status
            batch = self._get("/memberships/members", **params)
            if not batch:
                return
            yield from batch
            if len(batch) < 100:
                return
            page += 1

    def active_emails(self) -> set[str]:
        """Emails of everyone the website considers an active partner."""
        emails: set[str] = set()
        for m in self.iter_memberships():
            if m.get("status") in ACTIVE_STATUSES:
                email = (m.get("customer_email") or (m.get("customer") or {}).get("email") or "").strip().lower()
                if email:
                    emails.add(email)
        return emails

"""Website-vs-CRM partner reconciliation report.

Produces the same three numbers the morning count-check scenario emails:
active on the website, flagged as partner in DonorPerfect, and the two
difference sets. Run it when the nightly email looks wrong and you want the
names behind the numbers.

    DP_API_KEY=... WC_SITE=... WC_KEY=... WC_SECRET=... python -m tools.reconcile
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Reconciliation:
    website: frozenset[str]
    crm: frozenset[str]

    @property
    def missing_from_crm(self) -> frozenset[str]:
        return self.website - self.crm

    @property
    def stale_in_crm(self) -> frozenset[str]:
        return self.crm - self.website

    @property
    def gap(self) -> int:
        return len(self.crm) - len(self.website)

    def report(self, expected_gap: int = 0, tolerance: int = 5) -> str:
        lines = [
            f"Website active partners: {len(self.website)}",
            f"DonorPerfect partners:   {len(self.crm)}",
            f"Gap (CRM - website):     {self.gap}  (expected about {expected_gap})",
        ]
        if abs(self.gap - expected_gap) > tolerance:
            lines.append("STATUS: NEEDS ATTENTION - gap moved outside tolerance")
        else:
            lines.append("STATUS: OK")
        if self.missing_from_crm:
            lines.append("\nOn website, not flagged in DonorPerfect:")
            lines += [f"  - {e}" for e in sorted(self.missing_from_crm)]
        if self.stale_in_crm:
            lines.append("\nFlagged in DonorPerfect, not active on website:")
            lines += [f"  - {e}" for e in sorted(self.stale_in_crm)]
        return "\n".join(lines)


def reconcile(website_emails, crm_emails) -> Reconciliation:
    norm = lambda s: frozenset(e.strip().lower() for e in s if e and e.strip())
    return Reconciliation(norm(website_emails), norm(crm_emails))


def main() -> int:
    from .dp_client import DonorPerfectClient
    from .woo_memberships import WooMemberships

    dp = DonorPerfectClient(api_key=os.environ["DP_API_KEY"])
    wc = WooMemberships(os.environ["WC_SITE"], os.environ["WC_KEY"], os.environ["WC_SECRET"])
    rec = reconcile(wc.active_emails(), (r["email"] for r in dp.partners()))
    print(rec.report(expected_gap=int(os.environ.get("EXPECTED_GAP", "0"))))
    return 0 if "OK" in rec.report() else 1


if __name__ == "__main__":
    sys.exit(main())

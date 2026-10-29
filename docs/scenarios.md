# Scenario catalogue

Nine Make scenarios. Names below are descriptive; the live account uses short letter codes. IDs, connection numbers, and webhook URLs are intentionally omitted.

## Real-time (webhook-triggered)

### Status sync
- **Trigger:** WooCommerce Memberships webhook on membership status change.
- **Steps:** look up the DonorPerfect record by WooCommerce customer email → map membership status to Is-a-Partner + Partner Status → write Membership Type and start/end dates → apply the gifted rule (a gifted membership sets Partner Status = Gifted and never touches billing fields) → call *Checkout answers* for the same customer.
- **Idempotent:** re-running on the same event produces no change.

### New partner
- **Trigger:** WooCommerce Memberships webhook on membership created.
- **Steps:** find-or-create DonorPerfect donor → fill title and phone if empty → write checkout answers → add contact to the Partner Alerts list (and the SMS list if opted in) → email Partner Relations a one-paragraph summary.
- **Why separate from Status sync:** creation needs the full checkout payload; status changes do not.

### Contact changes
- **Trigger:** WooCommerce `customer.updated` webhook.
- **Steps:** compare incoming street + 5-digit ZIP and email to DonorPerfect → if different, update DonorPerfect and the contact in both Constant Contact accounts → email Partner Relations what changed.
- **Guard:** ZIP-only changes are flagged in the email rather than written silently; they are usually a typo.

### Checkout answers
- **Trigger:** internal webhook, called by *Status sync* and *Catch-up*.
- **Steps:** read the most recent order's custom checkout fields (date of birth, spouse, how heard, listen via, text opt-in) → write to DonorPerfect user-defined fields, empty-only → text opt-in overwrites.

## Scheduled

| Time (ET) | Scenario | Purpose |
|---|---|---|
| 11:00 PM | Catch-up | Re-posts the last 26 hours of membership and subscription events through *Status sync* and *Checkout answers*, so a missed webhook is corrected within a day. |
| 12:30 AM | Newsletter lists | Adds active partners to the Newsletter account's Active Partner list and Active Newsletter list; removes paused and cancelled from the partner list only. |
| 1:15 AM | Full status check | Pulls every active membership from WooCommerce and every Is-a-Partner record from DonorPerfect, diffs, and corrects DonorPerfect toward the website. |
| 1:45 AM | Partner Alerts lists | Removes lapsed partners from the Active Partner list, maintains Canceled/Paused and Pending Cancellation lists, emails list counts. A count shown as "–" means a list was renamed or deleted and the scenario settings need updating. |
| 7:00 AM | Count check | Emails DonorPerfect partner count vs. website count. A fixed gap of roughly 30 records is expected (legacy records with no website account); a moving gap is the signal. |

## Error handling

- Every scenario has a single error route that emails the engineer with the module name and the input bundle's customer email (no other PII).
- Nothing retries automatically against DonorPerfect; a failed write is reported and corrected by the next nightly reconciliation.
- Constant Contact rate limits are handled with a 2-second sleep between list operations in the nightly scenarios.

## Credit budget

Make operations are the real constraint. Changes made to stay inside the plan:
- Catch-up window reduced from 7 days to 26 hours.
- Full status check limited to active memberships rather than all customers.
- Reconciliation emails replaced per-record emails.

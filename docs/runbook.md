# Runbook

## Weekday morning check (10 minutes)

1. **Make:** open the scenario list. Any scenario switched off, or any errors or warnings in the last 24 hours, gets looked at first.
2. **Nightly emails** (all sent from the automation mailbox):
   - *Partner sync check*: DonorPerfect count vs. website count. Compare the gap to the usual baseline. A gap that moved by more than a handful of records since yesterday means a webhook or a nightly job failed.
   - *Partner Alerts lists – nightly check*: list counts. A count of "–" means a list was renamed or deleted in Constant Contact; update the list names in the scenario settings.
   - *Newsletter list updated*: who was added or removed.
   - *Checkout answers from renewals*: what was written to DonorPerfect.
   - *DonorPerfect updated: address*: address changes. If only the ZIP changed, check the order; it is usually a typo and worth a quick note to the partner.
3. **Partner Relations questions:** answer in plain language. No scenario names, no field codes.

## Telling a webhook miss from a logic bug

- A webhook miss shows up as one record wrong today and correct tomorrow (the nightly catch-up fixed it). Check WooCommerce → Settings → Advanced → Webhooks for delivery failures.
- A logic bug shows up as the same kind of record wrong every day. Find the rule in `decision-rules.md` that should have handled it and check the filter in the scenario.

## Patching a scenario safely

- Edit the existing scenario in place. Do not clone from a blueprint export; exports can embed connection details.
- Change one module, run once with a known test customer, read the execution log, then turn the scheduler back on.

## Reading Constant Contact data when the UI isn't enough

The Partner Alerts account is reachable only through Make. For a one-off read, build a temporary on-demand scenario that queries the list and posts the result to a temporary webhook, run it once, read the hook log, then delete both. Keep the payload small; hook logs truncate around 10 KB.

## WooCommerce side

- The checkout text opt-in plugin logs under WooCommerce → Status → Logs. Scheduled Actions may sit pending until wp-admin is loaded; use the Run link if a batch is late.

## When DonorPerfect is wrong and the website is right

Do nothing by hand. The 1:15 AM full status check corrects DonorPerfect toward the website. If it is urgent, run the full status check manually.

## When the website is wrong

Fix the membership in WooCommerce. Every downstream system follows within a day, and the real-time scenarios follow within seconds.

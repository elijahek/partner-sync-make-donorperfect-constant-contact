# Decision rules

Every rule here came out of a conversation with the people who own the data (Partner Relations and Finance). The sync enforces them; it does not decide them.

## Source of truth

- **WooCommerce Memberships** define who is an active partner, not Subscriptions. Memberships cover offline payers and gifted partnerships; subscriptions only cover card-paying partners.
- WooCommerce statuses `active` and `pending-cancellation` are both treated as active. The partner keeps access and keeps receiving alerts until the paid term ends.
- DonorPerfect holds two partner fields: a boolean **Is a Partner** used only by automation, and a separate **Partner Status** dropdown (active, paused, pending cancellation, expired, gifted) for staff.

## Writing to DonorPerfect

- Fill **empty** fields only. Never overwrite data a person entered.
- Exception: **text-alert opt-in**. The website's most recent checkout answer always wins, in both directions.
- Renewal checkout answers go in at the moment of renewal, not in the nightly batch.
- Never regenerate or rotate the DonorPerfect API key from inside an automation.

## Constant Contact

- **Never unsubscribe** a contact through the API. Removal from a list is the only allowed negative action. Unsubscribes are the contact's own decision.
- Never delete a contact.
- Two accounts, two jobs:
  - *Partner Alerts* account: Active Partner list, SMS list, Pending Cancellation, Gifted, Canceled/Paused. Fed in real time for additions and nightly for removals.
  - *Newsletter* account: Active Partner list and Active Newsletter list. Partners are added to both; paused and cancelled come off the partner list only, never the newsletter.
- A new partner appears on the alerts list **immediately**. Overnight was tried first and Partner Relations found it too slow for welcome texts.
- SMS consent that Constant Contact shows as "pending" means the partner never answered the confirmation text. Only the partner can resolve it; the API cannot promote pending to explicit consent, so the sync leaves it alone.

## Texting

- No one is texted without consent recorded at checkout.
- Once someone replies STOP, nothing more goes to that number. There is no automated re-confirmation list for renewing partners who opted out.

## Welcome sequence

- Brand-new partners and partners returning after six or more months away enter the welcome workflow.
- Routine renewals do not. Re-sending a welcome to a ten-year partner was the first complaint the system generated.

## Change control

- The automation proposes; a person approves. Nightly emails to Partner Relations list every change made, so a wrong rule is caught the next morning, not the next quarter.
- Policy changes (what counts as active, who gets which list) are decisions for the staff who own the relationship, presented as options with trade-offs. The engineer's job is to implement the choice, not make it.

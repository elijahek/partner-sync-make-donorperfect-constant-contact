# Field mapping

How data moves between the three systems. Field codes for DonorPerfect user-defined fields are shown generically; the live codes are account-specific.

## WooCommerce → DonorPerfect

| WooCommerce | DonorPerfect | Rule |
|---|---|---|
| Customer email | Email (match key) | Match on primary email first; fall back to first + last + ZIP. |
| Billing first / last name | First Name / Last Name | Fill if empty. |
| Billing address, city, state, ZIP | Address block | Update when street + 5-digit ZIP differ. |
| Billing phone | Home/Mobile Phone | Fill if empty. |
| Checkout: Title | Title | Fill if empty. |
| Checkout: Spouse name | Spouse | Fill if empty. |
| Checkout: Date of birth | Birth Date | Fill if empty. |
| Checkout: How did you hear about us | UDF: How Heard | Fill if empty. |
| Checkout: Where do you listen | UDF: Listen Via | Fill if empty. |
| Checkout: Text alert opt-in | UDF: Text Opt-In | **Always overwrite** with the latest answer. |
| Membership status | UDF: Is a Partner (Y/N) | active, pending-cancellation → Y; paused, expired, cancelled → N. |
| Membership status | UDF: Partner Status | active → Active; pending-cancellation → Pending Cancellation; paused → Paused; expired/cancelled → Expired; gifted plan → Gifted. |
| Membership plan | UDF: Membership Type | Plan name. |
| Membership start / end | UDF: Partner Since / Partner Until | Start fills once; end updates on every renewal. |

## DonorPerfect → Constant Contact (Partner Alerts account)

| Condition | List action |
|---|---|
| Is a Partner = Y | Add to Active Partner list |
| Is a Partner = N | Remove from Active Partner list |
| Text Opt-In = Y and SMS consent not "pending" | Add to SMS list |
| Partner Status = Pending Cancellation | Add to Pending Cancellation list |
| Partner Status = Gifted | Add to Gifted list |
| Partner Status = Paused or Expired | Add to Canceled/Paused list; remove from Active |

## WooCommerce → Constant Contact (Newsletter account)

| Condition | List action |
|---|---|
| Membership active or pending-cancellation | Add to Active Partner list and Active Newsletter list |
| Membership paused, expired, cancelled | Remove from Active Partner list only |

Primary email only; no secondary emails are written to either account.

## Known data quirks

- Many legacy DonorPerfect records carry one spouse's name with the other spouse's email. Matching on email alone attaches website activity to the record with that email, which is usually correct for list purposes but wrong for salutations. Open item for Partner Relations.
- Partner Status values in DonorPerfect had inconsistent capitalization from years of manual entry. The sync writes canonical values; a one-time cleanup normalized the rest.
- A fixed gap of around 30 partners exists between DonorPerfect and the website: offline payers from before the website existed. They are legitimately partners and are excluded from the drift alert.

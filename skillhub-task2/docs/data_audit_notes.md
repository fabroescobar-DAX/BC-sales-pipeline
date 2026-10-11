# SkillHub PH — Data Audit Notes

**Scope:** `subscriptions_export.csv` (959 raw rows). One row per customer
subscription: signup date, plan, acquisition channel, payment method,
status, cancel date, cancel reason.

## Issues found and how they were handled

- **3 fully blank rows** — export artifacts, no information content.
  Dropped.
- **6 exact duplicate rows** (same `customer_id`, every field identical) —
  export duplication, not six real re-signups. Dropped, kept first
  occurrence.
- **Casing inconsistency** on `plan` (`basic`/`BASIC`/`Basic`) and
  `signup_channel` (`paid ads`/`Paid Ads`). Standardized to Title Case.
  Same lesson as the BrightCart project: this doesn't just look
  untidy — `GROUP BY plan` before fixing this would have silently
  split one plan into three rows.
- **Mixed date formats** (`YYYY-MM-DD`, `MM/DD/YYYY`, `DD-Mon-YYYY`) in
  both `signup_date` and `cancel_date`. Parsed to a single ISO date type.
- **4 rows where `cancel_date` is on or before `signup_date`** — physically
  impossible (can't cancel before or the instant you sign up), almost
  certainly a data-entry error on the cancel date. **Not dropped** — the
  customer, plan, and channel data in these rows is still real and
  usable for segment-level counts. Flagged with `flag_invalid_cancel_date`
  and excluded only from the tenure/retention calculations, where a
  negative or zero tenure would distort the numbers.
- **15 rows missing `payment_method`.** Left blank, not defaulted — this
  field isn't used in the churn analysis, but a default would misrepresent
  actual payment mix if anyone queries it later.
- **`cancel_reason` is blank on ~45% of cancelled rows.** Not a cleaning
  issue — this is realistic: self-serve cancellations rarely get a reason
  logged unless the customer goes through a support flow. Documented here
  rather than treated as missing data to fix, because it isn't fixable;
  it's a known gap in what the product captures. Worth flagging to the
  client as a product/process improvement, not a data quality bug.

## Question for the client

`cancel_reason` capture is sparse enough (~45% blank) that any
reason-level breakdown in this analysis is directional, not definitive.
If churn-reason analysis becomes a priority, the cancellation flow should
prompt for a reason before completing, not treat it as optional.

## Result

959 raw rows → 950 clean rows (3 blank + 6 duplicate dropped). 4 rows
flagged (not dropped) for an invalid cancel date. See
`scripts/clean_data.py` for the exact, reproducible logic.

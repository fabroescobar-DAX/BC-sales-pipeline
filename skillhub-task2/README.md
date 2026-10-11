# SkillHub PH — Subscriber Churn Analysis

A churn/retention analysis for a fictional Cagayan de Oro-based online
course subscription service. Unlike a straight pipeline-and-dashboard
project, the deliverable here is a **written recommendation a
stakeholder can act on** — the analysis exists to support that memo,
not the other way around.

**Stack:** Python (pandas, scipy) for cleaning, statistical testing, and
charts → SQL for the queries a stakeholder would ask for directly.

## The question

Subscriber churn has been climbing. Why, and what should the business
do about it? See **[`reports/churn_memo.md`](reports/churn_memo.md)**
for the answer — that's the actual deliverable.

## What this project demonstrates

- **Going from data to a decision, not just a chart.** The memo leads
  with recommendations, not methodology — the way an analyst actually
  communicates to a non-technical stakeholder.
- **Statistical rigor behind the claims.** Every segment difference
  cited in the memo (churn by plan, by channel, the price-increase
  effect) is backed by a chi-square test, not an eyeballed bar chart.
  See `scripts/analyze_churn.py`.
- **Cohort retention analysis.** Month-by-month signup cohorts tracked
  for 3- and 6-month retention, the standard way subscription
  businesses watch for a problem before it shows up in the churn total.
- **The same documentation discipline as the BrightCart project**:
  every cleaning decision explained, not hidden, including a known gap
  in the data (`cancel_reason` is only ~45% captured) that's flagged as
  a product issue for the client rather than silently worked around.

## Structure

| Path | What's in it |
|---|---|
| `data/raw/` | Original export |
| `data/clean/` | Cleaned CSV, output of `clean_data.py` |
| `scripts/generate_raw_data.py` | Synthetic data generator (reproducible, seeded) |
| `scripts/clean_data.py` | Cleaning logic, every decision logged |
| `scripts/analyze_churn.py` | Cohort retention, segment churn rates, significance tests, charts |
| `sql/churn_queries.sql` | The on-demand queries behind the headline numbers |
| `docs/data_audit_notes.md` | Full data audit |
| `reports/churn_memo.md` | **The deliverable** — findings and recommendations for the stakeholder |
| `reports/cohort_retention_chart.png`, `churn_by_segment_chart.png` | Supporting charts, referenced in the memo |

## Key finding

Churn isn't random — it's concentrated in Paid Ads-acquired customers
(65.4% vs. 35.6% for Referral) and in Basic-tier subscribers (58.7% vs.
22.2% for Premium), and the February Standard-plan price increase
roughly doubled 90-day cancellations among existing subscribers (19.3%
→ 39.2%, p = 0.001). All three findings are addressed with a specific
recommendation in the memo.

"""
Churn & retention analysis for SkillHub PH.
Reads data/clean/subscriptions_clean.csv, writes findings to stdout
and two charts to reports/.
"""
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AS_OF = pd.Timestamp("2025-09-30")
PRICE_INCREASE = pd.Timestamp("2025-02-01")

df = pd.read_csv("/home/claude/skillhub-task2/data/clean/subscriptions_clean.csv", parse_dates=["signup_date", "cancel_date"])

# Exclude the 4 rows with an invalid (pre-signup) cancel_date from all
# tenure/retention math — the signup/plan/channel data is fine, but we
# can't trust a negative-tenure row in a "how long do people stay" analysis.
analysis_df = df[df["flag_invalid_cancel_date"] == 0].copy()
print(f"Rows in analysis set: {len(analysis_df)} (excluded {df['flag_invalid_cancel_date'].sum()} invalid-cancel-date rows)")

# --- 1. Headline churn rate ---
n_total = len(analysis_df)
n_cancelled = (analysis_df["status"] == "Cancelled").sum()
print(f"\nOverall churn rate: {n_cancelled}/{n_total} = {n_cancelled/n_total:.1%}")

# --- 2. Churn rate by plan ---
print("\nChurn rate by plan:")
by_plan = analysis_df.groupby("plan")["status"].apply(lambda s: (s == "Cancelled").mean())
counts_plan = analysis_df.groupby("plan").size()
for plan, rate in by_plan.sort_values(ascending=False).items():
    print(f"  {plan:10s} {rate:.1%}  (n={counts_plan[plan]})")

# --- 3. Churn rate by channel ---
print("\nChurn rate by signup_channel:")
by_channel = analysis_df.groupby("signup_channel")["status"].apply(lambda s: (s == "Cancelled").mean())
counts_channel = analysis_df.groupby("signup_channel").size()
for ch, rate in by_channel.sort_values(ascending=False).items():
    print(f"  {ch:15s} {rate:.1%}  (n={counts_channel[ch]})")

# --- 4. Statistical significance: is churn associated with plan / channel? ---
for col in ["plan", "signup_channel"]:
    ct = pd.crosstab(analysis_df[col], analysis_df["status"])
    chi2, p, dof, exp = chi2_contingency(ct)
    print(f"\nChi-square test, status ~ {col}: chi2={chi2:.1f}, p={p:.2e}")

# --- 5. Price-increase effect on Standard plan ---
std = analysis_df[analysis_df["plan"] == "Standard"].copy()
window_end = PRICE_INCREASE + pd.Timedelta(days=90)

# customers who were "at risk" (already subscribed, not yet cancelled) going into the window
at_risk_before = std[(std["signup_date"] < PRICE_INCREASE) &
                      ((std["cancel_date"].isna()) | (std["cancel_date"] >= PRICE_INCREASE))]
cancelled_in_window = at_risk_before[(at_risk_before["cancel_date"] >= PRICE_INCREASE) &
                                      (at_risk_before["cancel_date"] < window_end)]
rate_in_window = len(cancelled_in_window) / len(at_risk_before) if len(at_risk_before) else float("nan")

# baseline: same plan, same 90-day window length, prior quarter (Nov 2024 - Jan 2025)
baseline_start = PRICE_INCREASE - pd.Timedelta(days=90)
at_risk_baseline = std[(std["signup_date"] < baseline_start) &
                        ((std["cancel_date"].isna()) | (std["cancel_date"] >= baseline_start))]
cancelled_baseline = at_risk_baseline[(at_risk_baseline["cancel_date"] >= baseline_start) &
                                       (at_risk_baseline["cancel_date"] < PRICE_INCREASE)]
rate_baseline = len(cancelled_baseline) / len(at_risk_baseline) if len(at_risk_baseline) else float("nan")

print(f"\nStandard plan, 90-day cancellation rate among at-risk subscribers:")
print(f"  Prior quarter (Nov 2024-Jan 2025, pre price increase): {rate_baseline:.1%}  (n at risk={len(at_risk_baseline)})")
print(f"  Post price-increase quarter (Feb-Apr 2025):             {rate_in_window:.1%}  (n at risk={len(at_risk_before)})")

# --- 6. Cohort retention: % of each signup-month cohort still active at 3 and 6 months ---
analysis_df["signup_month"] = analysis_df["signup_date"].dt.to_period("M")

def retained_at(row, months):
    cutoff = row["signup_date"] + pd.DateOffset(months=months)
    if cutoff > AS_OF:
        return np.nan  # not enough time has passed to know yet
    if pd.isna(row["cancel_date"]):
        return 1
    return 1 if row["cancel_date"] > cutoff else 0

analysis_df["retained_3mo"] = analysis_df.apply(lambda r: retained_at(r, 3), axis=1)
analysis_df["retained_6mo"] = analysis_df.apply(lambda r: retained_at(r, 6), axis=1)

cohort_retention = analysis_df.groupby("signup_month").agg(
    cohort_size=("customer_id", "count"),
    retained_3mo=("retained_3mo", "mean"),
    retained_6mo=("retained_6mo", "mean"),
).reset_index()
cohort_retention["signup_month"] = cohort_retention["signup_month"].astype(str)
print("\nCohort retention (first/last 5 cohorts shown):")
print(cohort_retention.to_string(index=False))
cohort_retention.to_csv("/home/claude/skillhub-task2/reports/cohort_retention.csv", index=False)

# --- Chart 1: 3-month retention by signup cohort over time ---
plot_df = cohort_retention.dropna(subset=["retained_3mo"])
plt.figure(figsize=(9, 4.5))
plt.plot(plot_df["signup_month"], plot_df["retained_3mo"] * 100, marker="o", color="#2f6f6f")
plt.ylabel("% retained at 3 months")
plt.xlabel("Signup cohort (month)")
plt.title("3-Month Retention by Signup Cohort")
plt.xticks(rotation=45, ha="right")
plt.ylim(0, 100)
plt.tight_layout()
plt.savefig("/home/claude/skillhub-task2/reports/cohort_retention_chart.png", dpi=150)
plt.close()

# --- Chart 2: churn rate by plan and channel ---
fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
by_plan.sort_values(ascending=False).mul(100).plot(kind="bar", ax=axes[0], color="#2f6f6f")
axes[0].set_title("Churn Rate by Plan")
axes[0].set_ylabel("% cancelled")
axes[0].tick_params(axis="x", rotation=0)

by_channel.sort_values(ascending=False).mul(100).plot(kind="bar", ax=axes[1], color="#8a4f7d")
axes[1].set_title("Churn Rate by Signup Channel")
axes[1].set_ylabel("% cancelled")
axes[1].tick_params(axis="x", rotation=30)
for ax in axes:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig("/home/claude/skillhub-task2/reports/churn_by_segment_chart.png", dpi=150)
plt.close()

print("\nCharts written to reports/cohort_retention_chart.png and reports/churn_by_segment_chart.png")

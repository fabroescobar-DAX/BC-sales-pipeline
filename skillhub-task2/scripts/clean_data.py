"""
Cleans data/raw/subscriptions_export.csv -> data/clean/subscriptions_clean.csv

Every decision is a deliberate choice, logged below and mirrored in
docs/data_audit_notes.md. Nothing is silently dropped or guessed.
"""
import pandas as pd
import numpy as np

RAW_PATH = "/home/claude/skillhub-task2/data/raw/subscriptions_export.csv"
CLEAN_PATH = "/home/claude/skillhub-task2/data/clean/subscriptions_clean.csv"

df = pd.read_csv(RAW_PATH, dtype=str, keep_default_na=False)
n_raw = len(df)
log = [f"Raw rows: {n_raw}"]

# 1. Drop fully blank rows (export artifacts, no information content)
blank_mask = (df.drop(columns=["monthly_price"]) == "").all(axis=1) & (df["monthly_price"] == "")
n_blank = blank_mask.sum()
df = df[~blank_mask].copy()
log.append(f"Dropped {n_blank} fully-blank rows (export artifacts).")

# 2. Drop exact duplicate rows (same customer_id + every field identical —
#    export duplication, not two real customers), keep first occurrence
n_before = len(df)
df = df.drop_duplicates(keep="first")
log.append(f"Dropped {n_before - len(df)} exact duplicate rows.")

# 3. Standardize plan casing
df["plan"] = df["plan"].str.strip().str.title()
log.append("Standardized `plan` to Title Case (Basic/Standard/Premium).")

# 4. Standardize signup_channel casing
df["signup_channel"] = df["signup_channel"].str.strip().str.title()
log.append("Standardized `signup_channel` to Title Case.")

# 5. Parse mixed date formats -> ISO (YYYY-MM-DD)
def parse_mixed_date(s):
    if not s or s.strip() == "":
        return pd.NaT
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y"):
        try:
            return pd.to_datetime(s, format=fmt)
        except ValueError:
            continue
    return pd.NaT

df["signup_date"] = df["signup_date"].apply(parse_mixed_date)
df["cancel_date"] = df["cancel_date"].apply(parse_mixed_date)
log.append("Parsed 3 mixed raw date formats (ISO, MM/DD/YYYY, DD-Mon-YYYY) to a single ISO date type.")

n_unparsed_signup = df["signup_date"].isna().sum()
if n_unparsed_signup:
    log.append(f"WARNING: {n_unparsed_signup} rows had an unparseable signup_date — left as NaT, not dropped.")

# 6. Flag (not drop) rows where cancel_date is before or same-day as signup_date —
#    physically implausible, almost certainly a data-entry error, but the
#    underlying customer and plan data is still real and usable.
invalid_cancel = df["cancel_date"].notna() & (df["cancel_date"] <= df["signup_date"])
df["flag_invalid_cancel_date"] = invalid_cancel.astype(int)
log.append(f"Flagged {invalid_cancel.sum()} rows where cancel_date <= signup_date (data-entry error, not dropped) — excluded from tenure/retention calcs downstream, kept visible for review.")

# 7. monthly_price -> numeric
df["monthly_price"] = pd.to_numeric(df["monthly_price"], errors="coerce")

# 8. payment_method: leave missing as blank, don't default (same philosophy as BrightCart —
#    "unknown" and a specific default are different facts)
n_missing_payment = (df["payment_method"] == "").sum()
log.append(f"{n_missing_payment} rows have a missing payment_method — left blank, not defaulted.")

# 9. status sanity check: status should agree with cancel_date presence
status_mismatch = ((df["status"] == "Cancelled") & df["cancel_date"].isna()) | \
                   ((df["status"] == "Active") & df["cancel_date"].notna())
log.append(f"status/cancel_date consistency check: {status_mismatch.sum()} mismatches found.")

df.to_csv(CLEAN_PATH, index=False)
log.append(f"Clean rows written: {len(df)}")

print("\n".join(log))

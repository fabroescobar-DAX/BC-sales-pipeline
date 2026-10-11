"""
Generates the raw, messy 'export' for the SkillHub PH churn project.
This simulates what an analyst would actually be handed: real signal
buried in the data, plus the kind of mess every real export has.

Run once to produce data/raw/subscriptions_export.csv, then never
re-run (would change the story the whole project is built on).
"""
import random
from datetime import date, timedelta

random.seed(42)

N_CUSTOMERS = 950

PLANS = ["Basic", "Standard", "Premium"]
PLAN_PRICE = {"Basic": 199, "Standard": 349, "Premium": 599}  # PHP/month
CHANNELS = ["Organic", "Paid Ads", "Referral", "Social Media"]
PAYMENT_METHODS = ["GCash", "Credit Card", "Bank Transfer"]
CANCEL_REASONS = [
    "Too expensive", "Not enough new content", "Found a free alternative",
    "Technical issues", "No longer needed",
]

START = date(2024, 4, 1)
END = date(2025, 9, 30)
PRICE_INCREASE_DATE = date(2025, 2, 1)  # Standard plan price hike


def random_date(start, end):
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def fmt_date(d, fmt_choice):
    if fmt_choice == 0:
        return d.strftime("%Y-%m-%d")
    elif fmt_choice == 1:
        return d.strftime("%m/%d/%Y")
    else:
        return d.strftime("%d-%b-%Y")


rows = []
customer_id_counter = 1001

for _ in range(N_CUSTOMERS):
    cid = f"CUS-{customer_id_counter}"
    customer_id_counter += 1

    signup = random_date(START, END)
    plan = random.choices(PLANS, weights=[0.5, 0.35, 0.15])[0]
    channel = random.choices(CHANNELS, weights=[0.35, 0.3, 0.2, 0.15])[0]
    payment = random.choice(PAYMENT_METHODS)

    # --- baseline monthly churn hazard, varies by plan and channel ---
    base_hazard = {"Basic": 0.10, "Standard": 0.06, "Premium": 0.03}[plan]
    if channel == "Paid Ads":
        base_hazard *= 1.8          # paid-ads-acquired users churn much faster
    elif channel == "Referral":
        base_hazard *= 0.6          # referred users stick around

    # simulate month-by-month survival from signup to END
    cancel_date = None
    cursor = signup
    month = 0
    while cursor < END:
        month += 1
        hazard = base_hazard
        # price-increase shock: Standard plan churn spikes for 3 months after
        if plan == "Standard" and PRICE_INCREASE_DATE <= cursor < PRICE_INCREASE_DATE + timedelta(days=90):
            hazard *= 3.2
        if random.random() < hazard:
            # cancels sometime in this month
            cancel_date = cursor + timedelta(days=random.randint(1, 28))
            if cancel_date > END:
                cancel_date = None
            break
        cursor += timedelta(days=30)

    status = "Cancelled" if cancel_date else "Active"

    # cancel reason: often missing in real exports (support never logs it on self-serve cancels)
    cancel_reason = ""
    if cancel_date:
        if random.random() < 0.55:
            cancel_reason = random.choice(CANCEL_REASONS)

    date_fmt_choice = random.choice([0, 0, 1, 2])  # mostly ISO, some mixed

    rows.append({
        "customer_id": cid,
        "signup_date": fmt_date(signup, date_fmt_choice),
        "plan": plan,
        "signup_channel": channel,
        "payment_method": payment,
        "monthly_price": PLAN_PRICE[plan],
        "status": status,
        "cancel_date": fmt_date(cancel_date, date_fmt_choice) if cancel_date else "",
        "cancel_reason": cancel_reason,
    })

# --- inject realistic mess ---

# 1. casing inconsistency on plan + channel (a handful of rows)
for r in random.sample(rows, 25):
    r["plan"] = r["plan"].lower() if random.random() < 0.5 else r["plan"].upper()
for r in random.sample(rows, 20):
    r["signup_channel"] = r["signup_channel"].replace("Paid Ads", "paid ads").replace("Social Media", "social media")

# 2. a few duplicate customer_id rows (export glitch, exact duplicates)
dupes = random.sample(rows, 6)
rows.extend([dict(r) for r in dupes])

# 3. a few rows with cancel_date before signup_date (data entry error)
for r in random.sample([r for r in rows if r["status"] == "Cancelled"], 4):
    r["cancel_date"] = r["signup_date"]  # will look like day-0 cancellation, suspicious

# 4. missing payment_method on some rows
for r in random.sample(rows, 15):
    r["payment_method"] = ""

# 5. a few completely blank rows (export artifact)
for _ in range(3):
    rows.append({k: "" for k in rows[0].keys()})

random.shuffle(rows)

import csv
out_path = "/home/claude/skillhub-task2/data/raw/subscriptions_export.csv"
with open(out_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows to {out_path}")

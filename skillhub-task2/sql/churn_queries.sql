-- Core churn queries, written against a `subscriptions_clean` table
-- loaded from data/clean/subscriptions_clean.csv (same column names).
-- The full statistical analysis (chi-square tests, cohort retention,
-- the price-increase comparison) lives in scripts/analyze_churn.py —
-- these are the queries a stakeholder would actually ask for on demand.

-- 1. Overall churn rate (excluding the 4 invalid-cancel-date rows)
SELECT
    SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled,
    COUNT(*) AS total,
    ROUND(SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) / COUNT(*) * 100, 1) AS churn_rate_pct
FROM subscriptions_clean
WHERE flag_invalid_cancel_date = 0;

-- 2. Churn rate by plan
SELECT
    plan,
    COUNT(*) AS n_customers,
    ROUND(SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) / COUNT(*) * 100, 1) AS churn_rate_pct
FROM subscriptions_clean
WHERE flag_invalid_cancel_date = 0
GROUP BY plan
ORDER BY churn_rate_pct DESC;

-- 3. Churn rate by acquisition channel
SELECT
    signup_channel,
    COUNT(*) AS n_customers,
    ROUND(SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) / COUNT(*) * 100, 1) AS churn_rate_pct
FROM subscriptions_clean
WHERE flag_invalid_cancel_date = 0
GROUP BY signup_channel
ORDER BY churn_rate_pct DESC;

-- 4. Monthly cancellations, Standard plan only — eyeball check for the
--    Feb 2025 price-increase spike referenced in reports/churn_memo.md
SELECT
    DATE_FORMAT(cancel_date, '%Y-%m') AS cancel_month,
    COUNT(*) AS cancellations
FROM subscriptions_clean
WHERE plan = 'Standard'
  AND status = 'Cancelled'
  AND flag_invalid_cancel_date = 0
GROUP BY cancel_month
ORDER BY cancel_month;

-- 5. Rows flagged for the invalid cancel-date issue (for review, not deletion)
SELECT customer_id, signup_date, cancel_date, plan, status
FROM subscriptions_clean
WHERE flag_invalid_cancel_date = 1;

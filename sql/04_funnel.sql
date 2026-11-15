-- 04_funnel.sql

CREATE OR REPLACE TABLE user_flags AS
SELECT
    user_id,
    BOOL_OR(event_type = 'view') AS has_view,
    BOOL_OR(event_type = 'cart') AS has_cart,
    BOOL_OR(event_type = 'purchase') AS has_purchase,
    BOOL_OR(event_type = 'remove_from_cart') AS has_remove
FROM events
GROUP BY user_id;

WITH counts AS (
    SELECT
        COUNT(*) AS total_users,
        COUNT(*) FILTER (WHERE has_view) AS view_users,
        COUNT(*) FILTER (WHERE has_view AND has_cart) AS view_cart_users,
        COUNT(*) FILTER (
            WHERE has_view AND has_cart AND has_purchase
        ) AS view_cart_purchase_users
    FROM user_flags
)
SELECT
    *,
    ROUND(100.0 * view_users / NULLIF(total_users, 0), 2) AS view_rate_pct,
    ROUND(100.0 * view_cart_users / NULLIF(view_users, 0), 2) AS cart_rate_pct,
    ROUND(
        100.0 * view_cart_purchase_users / NULLIF(view_cart_users, 0), 2
    ) AS purchase_rate_pct,
    ROUND(
        100.0 * view_cart_purchase_users / NULLIF(view_users, 0), 2
    ) AS view_to_purchase_rate_pct
FROM counts;
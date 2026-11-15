-- 07_price.sql

WITH price_bands AS (
    SELECT
        user_id,
        event_type,
        price,
        CASE
            WHEN price < 5 THEN 1
            WHEN price < 10 THEN 2
            WHEN price < 20 THEN 3
            WHEN price < 50 THEN 4
            ELSE 5
        END AS price_band
    FROM events
    WHERE price > 0
),
band_counts AS (
    SELECT
        price_band,
        COUNT(DISTINCT user_id) FILTER (WHERE event_type = 'view') AS view_users,
        COUNT(DISTINCT user_id) FILTER (WHERE event_type = 'cart') AS cart_users,
        COUNT(DISTINCT user_id) FILTER (WHERE event_type = 'purchase') AS purchase_users,
        COALESCE(SUM(price) FILTER (WHERE event_type = 'purchase'), 0) AS revenue
    FROM price_bands
    GROUP BY price_band
)
SELECT
    *,
    ROUND(100.0 * purchase_users / NULLIF(view_users, 0), 2)
        AS view_to_purchase_rate_pct
FROM band_counts
ORDER BY price_band;
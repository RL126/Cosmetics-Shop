-- 08_cart_time.sql

CREATE OR REPLACE TABLE cart_to_buy AS
WITH t AS (
    SELECT
        user_id,
        event_type,
        event_time,
        MIN(event_time) FILTER (WHERE event_type = 'cart')
            OVER (PARTITION BY user_id) AS first_cart
    FROM events
)
SELECT
    user_id,
    first_cart,
    MIN(event_time) AS first_purchase,
    DATE_DIFF('second', first_cart, MIN(event_time)) / 60.0 AS minutes
FROM t
WHERE event_type = 'purchase'
  AND event_time >= first_cart
GROUP BY user_id, first_cart;


SELECT
    CASE
        WHEN minutes < 10   THEN '1 <10min'
        WHEN minutes < 60   THEN '2 10-60min'
        WHEN minutes < 1440 THEN '3 1-24h'
        WHEN minutes < 4320 THEN '4 1-3d'
        ELSE '5 >3d'
    END AS time_band,
    COUNT(*) AS users,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM cart_to_buy
GROUP BY time_band
ORDER BY time_band;

SELECT MEDIAN(minutes) AS median_minutes FROM cart_to_buy;
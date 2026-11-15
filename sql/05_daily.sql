-- 05_daily.sql

CREATE OR REPLACE TABLE daily AS
SELECT
    CAST(event_time AS DATE) AS event_date,
    COUNT(DISTINCT user_id) AS active_users,
    COUNT(DISTINCT user_id) FILTER (WHERE event_type = 'purchase') AS purchase_users, 
    COUNT(DISTINCT user_id) FILTER (WHERE event_type = 'view') AS view_users,
    COUNT(DISTINCT user_id) FILTER (WHERE event_type = 'cart') AS cart_users
FROM events
GROUP BY event_date
ORDER BY event_date;

SELECT * FROM daily ORDER BY event_date LIMIT 10;

CREATE OR REPLACE TABLE daily_tagged AS
SELECT
    *,
    CASE
        WHEN purchase_users > 1.5 * (SELECT MEDIAN(purchase_users) FROM daily)
            THEN 'Peak Day'
        ELSE 'Normal Day'
    END AS day_type
FROM daily;

SELECT event_date, purchase_users, day_type
FROM daily_tagged
WHERE day_type = 'Peak Day'
ORDER BY event_date;

SELECT
    day_type,
    ROUND(AVG(active_users), 2) AS avg_active_users,
    ROUND(AVG(purchase_users), 2) AS avg_purchase_users,
    ROUND(AVG(cart_users * 100.0 / view_users), 1)     AS view_to_cart_pct,
    ROUND(AVG(purchase_users * 100.0 / cart_users), 1) AS cart_to_purchase_pct,
    ROUND(AVG(purchase_users * 100.0 / active_users), 1) AS purchase_rate_pct
FROM daily_tagged
GROUP BY day_type
ORDER BY day_type;


SELECT event_date, view_users, cart_users FROM daily ORDER BY event_date LIMIT 5;
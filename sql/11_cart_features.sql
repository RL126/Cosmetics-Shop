-- 11_cart_features.sql
-- Build features for: "24h after first add-to-cart, will a non-buyer purchase in the next 7 days?"

CREATE OR REPLACE TABLE cart_features AS
WITH
-- 1. Each user's first add-to-cart time
first_cart AS (
    SELECT user_id, MIN(event_time) AS first_cart
    FROM events
    WHERE event_type = 'cart'
    GROUP BY user_id
),

-- 2. Observation window: all events up to 24h after the first cart
observed AS (
    SELECT e.*, fc.first_cart
    FROM events e
    JOIN first_cart fc USING (user_id)
    WHERE e.event_time < fc.first_cart + INTERVAL 1 DAY
),

-- 3. Features (only from the observation window, so no leakage)
features AS (
    SELECT
        user_id,
        ANY_VALUE(first_cart)                                          AS first_cart,
        COUNT(*) FILTER (WHERE event_type = 'view')                    AS views,
        COUNT(DISTINCT product_id) FILTER (WHERE event_type = 'view')  AS products_viewed,
        COUNT(*) FILTER (WHERE event_type = 'cart')                    AS carts,
        COUNT(*) FILTER (WHERE event_type = 'remove_from_cart')        AS removes,
        COUNT(DISTINCT user_session)                                   AS sessions,
        SUM(price) FILTER (WHERE event_type = 'cart')                  AS cart_value,
        AVG(price) FILTER (WHERE event_type = 'cart')                  AS avg_cart_price,
        COUNT(*) FILTER (WHERE event_type = 'purchase')                AS purchases_24h,
        DATE_DIFF('second', MIN(event_time), ANY_VALUE(first_cart)) / 86400.0
                                                                       AS days_active_before_cart
    FROM observed
    GROUP BY user_id
),

-- 4. Label: did the user buy between 24h and 8 days after the first cart?
labels AS (
    SELECT
        fc.user_id,
        BOOL_OR(
            e.event_type = 'purchase'
            AND e.event_time >= fc.first_cart + INTERVAL 1 DAY
            AND e.event_time <  fc.first_cart + INTERVAL 8 DAY
        ) AS bought_next7d
    FROM first_cart fc
    LEFT JOIN events e USING (user_id)
    GROUP BY fc.user_id
)

SELECT
    f.*,
    (CAST(f.first_cart AS DATE) IN
        (SELECT event_date FROM daily_tagged WHERE day_type = 'Peak Day'))::INT AS cart_on_peak_day,
    COALESCE(l.bought_next7d, FALSE)::INT AS bought_next7d
FROM features f
JOIN labels l USING (user_id)
WHERE f.purchases_24h = 0                                -- only users who did NOT buy in the first 24h
  AND f.first_cart < TIMESTAMP '2019-11-23 00:00:00';    -- must have a full 8-day window inside November

-- Check
SELECT
    COUNT(*)                     AS users,
    ROUND(AVG(bought_next7d) * 100, 1) AS buy_rate_pct
FROM cart_features;
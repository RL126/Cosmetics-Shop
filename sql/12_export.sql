-- daily numbers for the dashboard
COPY (
    SELECT
        event_date,
        day_type,
        active_users,
        view_users,
        cart_users,
        purchase_users
    FROM daily_tagged
    ORDER BY event_date
) TO 'dashboard_daily.csv' (HEADER);

-- price bands
COPY (
    WITH b AS (
        SELECT *,
            CASE
                WHEN price < 5  THEN '1 <5'
                WHEN price < 10 THEN '2 5-10'
                WHEN price < 20 THEN '3 10-20'
                WHEN price < 50 THEN '4 20-50'
                ELSE '5 50+'
            END AS price_band
        FROM events
        WHERE price > 0
    )
    SELECT
        price_band,
        COUNT(DISTINCT user_id) FILTER (WHERE event_type = 'view')     AS view_users,
        COUNT(DISTINCT user_id) FILTER (WHERE event_type = 'purchase') AS purchase_users,
        ROUND(SUM(price) FILTER (WHERE event_type = 'purchase'), 2)    AS revenue
    FROM b
    GROUP BY price_band
    ORDER BY price_band
) TO 'dashboard_price.csv' (HEADER);

-- rfm segments
COPY (
    SELECT
        segment,
        COUNT(*) AS buyers,
        ROUND(SUM(monetary), 2) AS revenue
    FROM rfm_segments
    GROUP BY segment
    ORDER BY revenue DESC
) TO 'dashboard_rfm.csv' (HEADER);
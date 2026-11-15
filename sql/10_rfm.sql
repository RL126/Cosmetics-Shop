-- 10_rfm.sql

CREATE OR REPLACE TABLE rfm AS
SELECT
    user_id,
    DATE_DIFF('day', MAX(event_time)::DATE, DATE '2019-12-01') AS recency,
    COUNT(DISTINCT user_session) AS frequency,
    SUM(price) AS monetary
FROM events
WHERE event_type = 'purchase'
  AND price > 0
GROUP BY user_id;

WITH labeled AS (
    SELECT
        user_id,
        monetary,
        recency <= (SELECT MEDIAN(recency) FROM rfm) AS r_high,
        frequency >= 2 AS f_high,
        monetary >= (SELECT MEDIAN(monetary) FROM rfm) AS m_high
    FROM rfm
)
SELECT
    r_high,
    f_high,
    m_high,
    COUNT(*) AS buyers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS buyers_pct,
    ROUND(SUM(monetary), 2) AS revenue,
    ROUND(
        100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER (),
        2
    ) AS revenue_pct
FROM labeled
GROUP BY r_high, f_high, m_high
ORDER BY revenue DESC;

CREATE OR REPLACE TABLE rfm_segments AS
WITH flags AS (
    SELECT
        *,
        recency <= (SELECT MEDIAN(recency) FROM rfm) AS r_high,
        frequency >= 2 AS f_high,
        monetary >= (SELECT MEDIAN(monetary) FROM rfm) AS m_high
    FROM rfm
)
SELECT
    *,
    CASE
        WHEN r_high AND f_high AND m_high THEN 'Champions'
        WHEN r_high AND NOT f_high AND m_high THEN 'New Big Spenders'
        WHEN NOT r_high AND NOT f_high AND m_high THEN 'At-risk Big Spenders'
        WHEN NOT r_high AND f_high AND m_high THEN 'Cannot Lose'
        WHEN r_high AND NOT f_high AND NOT m_high THEN 'New Low Spenders'
        WHEN NOT r_high AND NOT f_high AND NOT m_high THEN 'Hibernating'
        WHEN r_high AND f_high AND NOT m_high THEN 'Loyal Low Spenders'
        WHEN NOT r_high AND f_high AND NOT m_high THEN 'Lapsing Low Spenders'
    END AS segment
FROM flags;

-- check segments
SELECT segment, COUNT(*) AS buyers
FROM rfm_segments
GROUP BY segment
ORDER BY buyers DESC;
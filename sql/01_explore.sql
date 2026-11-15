-- 01_explore.sql  

-- 1.total_rows
SELECT COUNT(*) AS total_rows FROM raw;

-- 2.total unique users
SELECT COUNT(DISTINCT user_id) AS unique_users FROM raw;

-- 3.total events by type
SELECT event_type, COUNT(*) AS event_count
FROM raw
GROUP BY event_type
ORDER BY event_count DESC;

-- 4.total missing sessions
SELECT COUNT(*) AS missing_sessions FROM raw WHERE user_session IS NULL;

-- 5.total negative prices
SELECT COUNT(*) AS negative_prices FROM raw WHERE price < 0;

-- 6.total zero price rows
SELECT event_type, COUNT(*) AS zero_price_rows
FROM raw
WHERE price = 0
GROUP BY event_type;
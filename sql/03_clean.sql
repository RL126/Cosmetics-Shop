-- 03_clean.sql 

--build cleaned table events
CREATE OR REPLACE TABLE events AS
SELECT DISTINCT *
FROM raw
WHERE user_session IS NOT NULL   --delete rows with missing user_session
  AND price >= 0;                --delete rows with negative prices, keep rows with price 0

--check cleaned rows count
SELECT COUNT(*) AS clean_rows FROM events;
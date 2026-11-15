-- 1.total duplicate rows
SELECT
    (SELECT COUNT(*) FROM raw)
    - (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM raw)) AS duplicate_rows;

-- 2.each event type's duplicate rows
WITH grouped AS (
    SELECT *, COUNT(*) AS row_count
    FROM raw
    GROUP BY ALL
)
SELECT event_type, SUM(row_count - 1) AS duplicate_rows
FROM grouped
GROUP BY event_type
ORDER BY duplicate_rows DESC;
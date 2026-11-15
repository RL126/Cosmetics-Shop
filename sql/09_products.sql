-- 09_products.sql
CREATE or REPLACE TABLE product_stats AS
SELECT
    product_id,
    ANY_VALUE(brand) AS brand,
    AVG(price) FILTER (WHERE price > 0) AS avg_price,
    COUNT(DISTINCT user_id) FILTER (WHERE event_type = 'view') AS view_users,
    COUNT(DISTINCT user_id) FILTER (WHERE event_type = 'cart') AS cart_users,
    COUNT(DISTINCT user_id) FILTER (WHERE event_type = 'purchase') AS purchase_users
FROM events
GROUP BY product_id;

WITH ranked AS (
    SELECT
        *,
        RANK() OVER (ORDER BY view_users DESC) AS view_rank,
        ROUND(100.0 * purchase_users / view_users, 2) AS conv
    FROM product_stats
    WHERE view_users > 0
)
SELECT *
FROM ranked
WHERE view_rank <= 200
ORDER BY conv ASC, view_users DESC
LIMIT 10;
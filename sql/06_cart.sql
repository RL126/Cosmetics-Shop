-- 06_cart.sql

SELECT
    COUNT(*) FILTER (WHERE has_cart) AS cart_users,
    COUNT(*) FILTER (WHERE has_cart AND has_purchase) AS cart_purchase_users,
    COUNT(*) FILTER (WHERE has_cart AND NOT has_purchase) AS cart_no_purchase_users,
    COUNT(*) FILTER (
        WHERE has_cart AND NOT has_purchase AND has_remove
    ) AS cart_no_purchase_remove_users
FROM user_flags;
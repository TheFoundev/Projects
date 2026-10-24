SELECT
    ROUND(100.0 * SUM(CASE WHEN orders > 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS repeat_rate
FROM (
    SELECT customer_id, COUNT(*) AS orders
    FROM orders
    WHERE status = 'paid'
    GROUP BY customer_id
)

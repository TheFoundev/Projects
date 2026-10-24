SELECT
    substr(order_date, 1, 7) AS month,
    ROUND(SUM(quantity * unit_price), 2) AS revenue
FROM orders
WHERE status = 'paid'
GROUP BY month
ORDER BY month

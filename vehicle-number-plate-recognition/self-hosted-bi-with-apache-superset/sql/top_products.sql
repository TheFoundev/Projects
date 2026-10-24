SELECT
    product,
    SUM(quantity) AS units,
    ROUND(SUM(quantity * unit_price), 2) AS revenue
FROM orders
WHERE status = 'paid'
GROUP BY product
ORDER BY revenue DESC
LIMIT 5

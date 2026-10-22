SELECT
    region,
    ROUND(100.0 * SUM(quantity * unit_price) /
        (SELECT SUM(quantity * unit_price) FROM orders WHERE status = 'paid'), 1) AS pct
FROM orders
WHERE status = 'paid'
GROUP BY region
ORDER BY pct DESC

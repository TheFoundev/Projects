SELECT
    order_date,
    COUNT(*) AS orders,
    ROUND(SUM(revenue), 2) AS revenue
FROM {{ ref('staging_orders') }}
GROUP BY order_date

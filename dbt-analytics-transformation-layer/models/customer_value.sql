SELECT
    customer_id,
    COUNT(*) AS orders,
    ROUND(SUM(revenue), 2) AS lifetime_value
FROM {{ ref('staging_orders') }}
GROUP BY customer_id

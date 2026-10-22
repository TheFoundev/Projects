SELECT
    c.customer_id,
    c.country,
    v.orders,
    v.lifetime_value,
    CASE
        WHEN v.lifetime_value >= 300 THEN 'high'
        WHEN v.lifetime_value >= 120 THEN 'medium'
        ELSE 'low'
    END AS segment
FROM raw_customers c
JOIN {{ ref('customer_value') }} v ON c.customer_id = v.customer_id

SELECT
    segment,
    COUNT(*) AS customers,
    ROUND(AVG(lifetime_value), 2) AS avg_lifetime_value
FROM {{ ref('mart_customer_segments') }}
GROUP BY segment

SELECT
    order_id,
    customer_id,
    DATE(order_ts) AS order_date,
    quantity,
    unit_price,
    ROUND(quantity * unit_price, 2) AS revenue
FROM raw_orders
WHERE status = 'paid'

CREATE DATABASE IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.sales
(
    order_id UInt32,
    order_date Date,
    customer_name String,
    city String,
    product_name String,
    price Decimal(12, 2),
    quantity UInt32
)
ENGINE = MergeTree()
ORDER BY order_date;

INSERT INTO analytics.sales VALUES
(1, '2026-08-01', 'Budi', 'Jakarta', 'Laptop', 10000000, 1),
(2, '2026-08-02', 'Andi', 'Bandung', 'Mouse', 300000, 2),
(3, '2026-08-03', 'Siti', 'Surabaya', 'Keyboard', 500000, 1);
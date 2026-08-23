CREATE DATABASE IF NOT EXISTS olist;

CREATE TABLE IF NOT EXISTS olist.customers
(
    customer_id String,
    customer_unique_id String,
    customer_zip_code_prefix UInt32,
    customer_city String,
    customer_state String
)
ENGINE = MergeTree
ORDER BY customer_id;
-- ============================================================
-- 1. Distribusi jumlah customer per state (basic aggregation)
-- ============================================================
SELECT
    customer_state,
    count() AS total_customers
FROM olist.customers
GROUP BY customer_state
ORDER BY total_customers DESC;


-- ============================================================
-- 2. Top 10 kota dengan customer terbanyak
-- ============================================================
SELECT
    customer_city,
    customer_state,
    count() AS total_customers
FROM olist.customers
GROUP BY customer_city, customer_state
ORDER BY total_customers DESC
LIMIT 10;


-- ============================================================
-- 3. Persentase kontribusi tiap state terhadap total customer
--    (window function - khas OLAP)
-- ============================================================
SELECT
    customer_state,
    count() AS total_customers,
    round(count() * 100.0 / sum(count()) OVER (), 2) AS pct_of_total
FROM olist.customers
GROUP BY customer_state
ORDER BY total_customers DESC;


-- ============================================================
-- 4. Ranking state berdasarkan jumlah customer
--    (RANK / DENSE_RANK - window function)
-- ============================================================
SELECT
    customer_state,
    count() AS total_customers,
    RANK() OVER (ORDER BY count() DESC) AS rank_state
FROM olist.customers
GROUP BY customer_state;


-- ============================================================
-- 5. Deteksi customer_unique_id yang punya lebih dari 1 customer_id
--    (analisis pelanggan berulang / repeat customer pattern)
-- ============================================================
SELECT
    customer_unique_id,
    count() AS jumlah_customer_id
FROM olist.customers
GROUP BY customer_unique_id
HAVING jumlah_customer_id > 1
ORDER BY jumlah_customer_id DESC;


-- ============================================================
-- 6. Rasio unique customer vs total baris customer_id
--    (mendeteksi duplikasi identitas pelanggan)
-- ============================================================
SELECT
    count() AS total_rows,
    uniqExact(customer_unique_id) AS unique_customers,
    round(uniqExact(customer_unique_id) * 100.0 / count(), 2) AS pct_unique
FROM olist.customers;


-- ============================================================
-- 7. Distribusi customer berdasarkan prefix zip code
--    (grouping berdasarkan 2 digit awal zip - analisis wilayah)
-- ============================================================
SELECT
    substring(toString(customer_zip_code_prefix), 1, 2) AS zip_prefix_2,
    count() AS total_customers
FROM olist.customers
GROUP BY zip_prefix_2
ORDER BY total_customers DESC
LIMIT 20;


-- ============================================================
-- 8. Cross-tab sederhana: jumlah kota unik per state
--    (khas OLAP cube - roll-up per dimensi wilayah)
-- ============================================================
SELECT
    customer_state,
    uniqExact(customer_city) AS jumlah_kota_unik,
    count() AS total_customers
FROM olist.customers
GROUP BY customer_state
ORDER BY total_customers DESC;


-- ============================================================
-- 9. Menggunakan GROUP BY ... WITH ROLLUP
--    (subtotal per state + grand total - fitur OLAP klasik)
-- ============================================================
SELECT
    customer_state,
    customer_city,
    count() AS total_customers
FROM olist.customers
GROUP BY customer_state, customer_city
    WITH ROLLUP
ORDER BY customer_state, customer_city;


-- ============================================================
-- 10. State dengan konsentrasi customer di 1 kota terbesar
--     (deteksi dominasi kota tunggal per state)
-- ============================================================
SELECT
    customer_state,
    customer_city,
    count() AS total_customers,
    round(count() * 100.0 / sum(count()) OVER (PARTITION BY customer_state), 2) AS pct_dalam_state
FROM olist.customers
GROUP BY customer_state, customer_city
ORDER BY customer_state, pct_dalam_state DESC;
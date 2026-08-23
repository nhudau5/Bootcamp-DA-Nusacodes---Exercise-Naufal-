-- ============================================================
-- 1. PERFORMA PRODUK — TERLARIS & PALING MENGUNTUNGKAN
-- ============================================================

-- 1a. Kategori produk terlaris (by jumlah item terjual)
SELECT
    dp.product_category_name,
    count() AS total_items_sold,
    sum(foi.price) AS total_revenue
FROM fact_order_items foi
JOIN dim_products dp ON foi.product_id = dp.product_id
GROUP BY dp.product_category_name
ORDER BY total_items_sold DESC
LIMIT 10;


-- 1b. Kategori produk paling menguntungkan (by total revenue)
SELECT
    dp.product_category_name,
    count() AS total_items_sold,
    sum(foi.price) AS total_revenue,
    round(avg(foi.price), 2) AS avg_price_per_item
FROM fact_order_items foi
JOIN dim_products dp ON foi.product_id = dp.product_id
GROUP BY dp.product_category_name
ORDER BY total_revenue DESC
LIMIT 10;


-- 1c. Kontribusi tiap kategori terhadap total revenue keseluruhan (window function)
SELECT
    dp.product_category_name,
    sum(foi.price) AS total_revenue,
    round(sum(foi.price) * 100.0 / sum(sum(foi.price)) OVER (), 2) AS pct_of_total_revenue
FROM fact_order_items foi
JOIN dim_products dp ON foi.product_id = dp.product_id
GROUP BY dp.product_category_name
ORDER BY total_revenue DESC;


-- ============================================================
-- 2. PERFORMA SELLER / PENJUAL
-- ============================================================

-- 2a. Top 10 seller berdasarkan total revenue
SELECT
    ds.seller_id,
    ds.seller_city,
    ds.seller_state,
    count(DISTINCT foi.order_id) AS total_orders,
    sum(foi.price) AS total_revenue
FROM fact_order_items foi
JOIN dim_sellers ds ON foi.seller_id = ds.seller_id
GROUP BY ds.seller_id, ds.seller_city, ds.seller_state
ORDER BY total_revenue DESC
LIMIT 10;


-- 2b. Ranking seller per state (window function - siapa yang paling unggul di tiap wilayah)
SELECT *
FROM
(
    SELECT
        seller_state,
        seller_id,
        total_revenue,
        RANK() OVER (PARTITION BY seller_state ORDER BY total_revenue DESC) AS rank_in_state
    FROM
    (
        SELECT
            ds.seller_state AS seller_state,
            ds.seller_id AS seller_id,
            sum(foi.price) AS total_revenue
        FROM fact_order_items foi
        JOIN dim_sellers ds ON foi.seller_id = ds.seller_id
        GROUP BY ds.seller_state, ds.seller_id
    )
)
WHERE rank_in_state <= 3
ORDER BY seller_state, rank_in_state;

-- 2c. Distribusi jumlah seller & rata-rata revenue per state
SELECT
    ds.seller_state,
    uniqExact(ds.seller_id) AS total_sellers,
    sum(foi.price) AS total_revenue,
    round(sum(foi.price) / uniqExact(ds.seller_id), 2) AS avg_revenue_per_seller
FROM fact_order_items foi
JOIN dim_sellers ds ON foi.seller_id = ds.seller_id
GROUP BY ds.seller_state
ORDER BY total_revenue DESC;


-- ============================================================
-- 3. ANALISIS REVIEW / KEPUASAN PELANGGAN
-- ============================================================

-- 3a. Distribusi review score keseluruhan
SELECT
    review_score,
    count() AS total_reviews,
    round(count() * 100.0 / sum(count()) OVER (), 2) AS pct_of_total
FROM fact_reviews
GROUP BY review_score
ORDER BY review_score DESC;


-- 3b. Rata-rata review score per kategori produk (kategori dengan kepuasan terendah)
SELECT
    dp.product_category_name,
    round(avg(fr.review_score), 2) AS avg_review_score,
    count() AS total_reviews
FROM fact_reviews fr
JOIN fact_order_items foi ON fr.order_id = foi.order_id
JOIN dim_products dp ON foi.product_id = dp.product_id
GROUP BY dp.product_category_name
HAVING total_reviews >= 30
ORDER BY avg_review_score ASC
LIMIT 10;


-- 3c. Korelasi keterlambatan pengiriman vs review score
SELECT
    CASE
        WHEN fo.order_delivered_customer_date > fo.order_estimated_delivery_date THEN 'Terlambat'
        ELSE 'Tepat Waktu'
    END AS status_pengiriman,
    round(avg(fr.review_score), 2) AS avg_review_score,
    count() AS total_orders
FROM fact_orders fo
JOIN fact_reviews fr ON fo.order_id = fr.order_id
WHERE fo.order_delivered_customer_date IS NOT NULL
GROUP BY status_pengiriman;


-- 3d. Seller dengan rata-rata review terburuk (minimal 20 order, biar nggak bias sample kecil)
SELECT
    ds.seller_id,
    ds.seller_state,
    count(DISTINCT foi.order_id) AS total_orders,
    round(avg(fr.review_score), 2) AS avg_review_score
FROM fact_order_items foi
JOIN dim_sellers ds ON foi.seller_id = ds.seller_id
JOIN fact_reviews fr ON foi.order_id = fr.order_id
GROUP BY ds.seller_id, ds.seller_state
HAVING total_orders >= 20
ORDER BY avg_review_score ASC
LIMIT 10;


-- ============================================================
-- 4. TOP 10 PRODUK TERLARIS (per product_id individual)
-- ============================================================

SELECT
    foi.product_id,
    dp.product_category_name,
    count() AS total_items_sold,
    sum(foi.price) AS total_revenue,
    round(avg(fr.review_score), 2) AS avg_review_score
FROM fact_order_items foi
JOIN dim_products dp ON foi.product_id = dp.product_id
LEFT JOIN fact_reviews fr ON foi.order_id = fr.order_id
GROUP BY foi.product_id, dp.product_category_name
ORDER BY total_items_sold DESC
LIMIT 10;

-- ============================================================
-- 5. TREN REVENUE & JUMLAH ORDER PER BULAN
-- ============================================================

SELECT
    toStartOfMonth(fo.order_purchase_timestamp) AS order_month,
    count(DISTINCT fo.order_id) AS total_orders,
    sum(foi.price) AS total_revenue,
    round(sum(foi.price) / count(DISTINCT fo.order_id), 2) AS avg_order_value
FROM fact_orders fo
JOIN fact_order_items foi ON fo.order_id = foi.order_id
WHERE fo.order_status NOT IN ('unavailable', 'canceled')
GROUP BY order_month
ORDER BY order_month;
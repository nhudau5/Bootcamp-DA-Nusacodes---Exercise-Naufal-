import pandas as pd
from clickhouse_driver import Client
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

CLICKHOUSE_HOST = "localhost"
CLICKHOUSE_PORT = 9000
CLICKHOUSE_DATABASE = "olist"
CLICKHOUSE_USER = "default"
CLICKHOUSE_PASSWORD = "admin123"


def get_client():
    return Client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        database=CLICKHOUSE_DATABASE,
        user=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
    )


# ============================================================
# SCHEMA (CREATE TABLE IF NOT EXISTS)
# ============================================================


def create_tables():

    print("=" * 60)
    print("CREATE TABLES (IF NOT EXISTS)")
    print("=" * 60)

    client = get_client()

    client.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_customers
        (
            customer_id String,
            customer_unique_id String,
            customer_zip_code_prefix Int64,
            customer_city String,
            customer_state String
        )
        ENGINE = ReplacingMergeTree()
        ORDER BY customer_id
        """
    )

    client.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_sellers
        (
            seller_id String,
            seller_zip_code_prefix Int64,
            seller_city String,
            seller_state String
        )
        ENGINE = ReplacingMergeTree()
        ORDER BY seller_id
        """
    )

    client.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_products
        (
            product_id String,
            product_category_name String,
            product_weight_g Int64,
            product_length_cm Int64,
            product_height_cm Int64,
            product_width_cm Int64
        )
        ENGINE = ReplacingMergeTree()
        ORDER BY product_id
        """
    )

    client.execute(
        """
        CREATE TABLE IF NOT EXISTS fact_orders
        (
            order_id String,
            customer_id String,
            order_status String,
            order_purchase_timestamp DateTime,
            order_approved_at Nullable(DateTime),
            order_delivered_carrier_date Nullable(DateTime),
            order_delivered_customer_date Nullable(DateTime),
            order_estimated_delivery_date DateTime
        )
        ENGINE = MergeTree()
        ORDER BY (order_purchase_timestamp, order_id)
        """
    )

    client.execute(
        """
        CREATE TABLE IF NOT EXISTS fact_order_items
        (
            order_id String,
            order_item_id Int32,
            product_id String,
            seller_id String,
            shipping_limit_date DateTime,
            price Float64,
            freight_value Float64
        )
        ENGINE = MergeTree()
        ORDER BY (order_id, order_item_id)
        """
    )

    client.execute(
        """
        CREATE TABLE IF NOT EXISTS fact_payments
        (
            order_id String,
            payment_sequential Int32,
            payment_type String,
            payment_installments Int32,
            payment_value Float64
        )
        ENGINE = MergeTree()
        ORDER BY (order_id, payment_sequential)
        """
    )

    client.execute(
        """
        CREATE TABLE IF NOT EXISTS fact_reviews
        (
            review_id String,
            order_id String,
            review_score Int32,
            review_comment_title String,
            review_comment_message String,
            review_creation_date DateTime,
            review_answer_timestamp Nullable(DateTime)
        )
        ENGINE = MergeTree()
        ORDER BY (order_id, review_id)
        """
    )

    client.disconnect()

    print("Semua tabel siap.\n")


# ============================================================
# GENERIC HELPERS
# ============================================================


def extract_csv(filename):

    path = DATA_DIR / filename

    print(f"Reading file: {path}")

    df = pd.read_csv(path)

    print(f"Rows extracted : {len(df):,}")
    print(f"Columns        : {len(df.columns)}")

    df.columns = df.columns.str.strip().str.lower()

    return df


def load_table(df, table_name, columns):

    data = df[columns].values.tolist()

    client = get_client()

    columns_sql = ",\n            ".join(columns)

    client.execute(
        f"""
        INSERT INTO {table_name}
        (
            {columns_sql}
        )
        VALUES
        """,
        data,
    )

    result = client.execute(f"SELECT count() FROM {table_name}")

    client.disconnect()

    print(f"Rows loaded into {table_name} : {len(data):,}")
    print(f"Rows in ClickHouse ({table_name}) : {result[0][0]:,}\n")


def to_datetime(df, columns):
    for col in columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
        # clickhouse-driver expects python datetime / None, not pandas NaT
        df[col] = df[col].astype(object).where(df[col].notnull(), None)
    return df


# ============================================================
# CUSTOMERS
# ============================================================


def transform_customers(df):

    df = df.drop_duplicates()

    for col in ["customer_id", "customer_unique_id", "customer_city", "customer_state"]:
        df[col] = df[col].astype("string").str.strip().fillna("unknown").astype(str)

    df["customer_zip_code_prefix"] = (
        pd.to_numeric(df["customer_zip_code_prefix"], errors="coerce")
        .fillna(0)
        .astype("int64")
    )

    df = df.dropna(subset=["customer_id"])

    return df[
        [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ]
    ]


def run_customers():
    print("\n" + "=" * 60)
    print("DIM_CUSTOMERS")
    print("=" * 60)
    df = extract_csv("olist_customers_dataset.csv")
    df = transform_customers(df)
    load_table(
        df,
        "dim_customers",
        [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ],
    )


# ============================================================
# SELLERS
# ============================================================


def transform_sellers(df):

    df = df.drop_duplicates()

    for col in ["seller_id", "seller_city", "seller_state"]:
        df[col] = df[col].astype("string").str.strip().fillna("unknown").astype(str)

    df["seller_zip_code_prefix"] = (
        pd.to_numeric(df["seller_zip_code_prefix"], errors="coerce")
        .fillna(0)
        .astype("int64")
    )

    df = df.dropna(subset=["seller_id"])

    return df[["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"]]


def run_sellers():
    print("\n" + "=" * 60)
    print("DIM_SELLERS")
    print("=" * 60)
    df = extract_csv("olist_sellers_dataset.csv")
    df = transform_sellers(df)
    load_table(
        df,
        "dim_sellers",
        ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"],
    )


# ============================================================
# PRODUCTS
# ============================================================


def transform_products(df):

    df = df.drop_duplicates()

    df["product_id"] = df["product_id"].astype("string").str.strip().astype(str)

    df["product_category_name"] = (
        df["product_category_name"]
        .astype("string")
        .str.strip()
        .fillna("unknown")
        .astype(str)
    )

    for col in [
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int64")

    df = df.dropna(subset=["product_id"])

    return df[
        [
            "product_id",
            "product_category_name",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ]
    ]


def run_products():
    print("\n" + "=" * 60)
    print("DIM_PRODUCTS")
    print("=" * 60)
    df = extract_csv("olist_products_dataset.csv")
    df = transform_products(df)
    load_table(
        df,
        "dim_products",
        [
            "product_id",
            "product_category_name",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
    )


# ============================================================
# ORDERS
# ============================================================


def transform_orders(df):

    df = df.drop_duplicates()

    for col in ["order_id", "customer_id", "order_status"]:
        df[col] = df[col].astype("string").str.strip().astype(str)

    date_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    df = to_datetime(df, date_cols)

    # order_purchase_timestamp & order_estimated_delivery_date tidak boleh null
    df = df.dropna(
        subset=["order_id", "order_purchase_timestamp", "order_estimated_delivery_date"]
    )

    return df[
        [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
    ]


def run_orders():
    print("\n" + "=" * 60)
    print("FACT_ORDERS")
    print("=" * 60)
    df = extract_csv("olist_orders_dataset.csv")
    df = transform_orders(df)
    load_table(
        df,
        "fact_orders",
        [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )


# ============================================================
# ORDER ITEMS
# ============================================================


def transform_order_items(df):

    df = df.drop_duplicates()

    for col in ["order_id", "product_id", "seller_id"]:
        df[col] = df[col].astype("string").str.strip().astype(str)

    df["order_item_id"] = (
        pd.to_numeric(df["order_item_id"], errors="coerce").fillna(0).astype("int32")
    )
    df["price"] = (
        pd.to_numeric(df["price"], errors="coerce").fillna(0).astype("float64")
    )
    df["freight_value"] = (
        pd.to_numeric(df["freight_value"], errors="coerce").fillna(0).astype("float64")
    )

    df = to_datetime(df, ["shipping_limit_date"])
    df = df.dropna(subset=["shipping_limit_date"])

    return df[
        [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ]
    ]


def run_order_items():
    print("\n" + "=" * 60)
    print("FACT_ORDER_ITEMS")
    print("=" * 60)
    df = extract_csv("olist_order_items_dataset.csv")
    df = transform_order_items(df)
    load_table(
        df,
        "fact_order_items",
        [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ],
    )


# ============================================================
# PAYMENTS
# ============================================================


def transform_payments(df):

    df = df.drop_duplicates()

    for col in ["order_id", "payment_type"]:
        df[col] = df[col].astype("string").str.strip().astype(str)

    df["payment_sequential"] = (
        pd.to_numeric(df["payment_sequential"], errors="coerce")
        .fillna(0)
        .astype("int32")
    )
    df["payment_installments"] = (
        pd.to_numeric(df["payment_installments"], errors="coerce")
        .fillna(0)
        .astype("int32")
    )
    df["payment_value"] = (
        pd.to_numeric(df["payment_value"], errors="coerce").fillna(0).astype("float64")
    )

    return df[
        [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ]
    ]


def run_payments():
    print("\n" + "=" * 60)
    print("FACT_PAYMENTS")
    print("=" * 60)
    df = extract_csv("olist_order_payments_dataset.csv")
    df = transform_payments(df)
    load_table(
        df,
        "fact_payments",
        [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ],
    )


# ============================================================
# REVIEWS
# ============================================================


def transform_reviews(df):

    df = df.drop_duplicates()

    for col in ["review_id", "order_id"]:
        df[col] = df[col].astype("string").str.strip().astype(str)

    # Komentar review banyak kosong -> isi string kosong (bukan Nullable, biar simpel)
    for col in ["review_comment_title", "review_comment_message"]:
        df[col] = df[col].astype("string").str.strip().fillna("").astype(str)

    df["review_score"] = (
        pd.to_numeric(df["review_score"], errors="coerce").fillna(0).astype("int32")
    )

    df = to_datetime(df, ["review_creation_date", "review_answer_timestamp"])
    df = df.dropna(subset=["review_id", "order_id", "review_creation_date"])

    return df[
        [
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ]
    ]


def run_reviews():
    print("\n" + "=" * 60)
    print("FACT_REVIEWS")
    print("=" * 60)
    df = extract_csv("olist_order_reviews_dataset.csv")
    df = transform_reviews(df)
    load_table(
        df,
        "fact_reviews",
        [
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ],
    )


# ============================================================
# MAIN ETL PIPELINE
# ============================================================


def main():

    print("\n")
    print("=" * 60)
    print("OLIST FULL DATASET ETL PIPELINE")
    print("=" * 60)

    create_tables()

    run_customers()
    run_sellers()
    run_products()
    run_orders()
    run_order_items()
    run_payments()
    run_reviews()

    print("=" * 60)
    print("ETL PIPELINE COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()

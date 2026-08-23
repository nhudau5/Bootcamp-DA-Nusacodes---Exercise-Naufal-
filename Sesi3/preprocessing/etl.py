import pandas as pd
from clickhouse_driver import Client
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "olist_customers_dataset.csv"

CLICKHOUSE_HOST = "localhost"
CLICKHOUSE_PORT = 9000
CLICKHOUSE_DATABASE = "olist"


# ============================================================
# EXTRACT
# ============================================================


def extract_data():

    print("=" * 60)
    print("EXTRACT")
    print("=" * 60)

    print(f"Reading file: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)

    print(f"Rows extracted : {len(df):,}")
    print(f"Columns        : {len(df.columns)}")

    print("\nColumns:")
    print(df.columns.tolist())

    return df


# ============================================================
# TRANSFORM
# ============================================================


def transform_data(df):

    print("\n" + "=" * 60)
    print("TRANSFORM")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Clean column names
    # --------------------------------------------------------

    df.columns = df.columns.str.strip().str.lower()

    print("\nColumn names cleaned.")

    # --------------------------------------------------------
    # 2. Remove duplicate rows
    # --------------------------------------------------------

    before_duplicate = len(df)

    df = df.drop_duplicates()

    after_duplicate = len(df)

    print(f"Duplicate removed : {before_duplicate - after_duplicate:,}")

    # --------------------------------------------------------
    # 3. Remove whitespace pada kolom string
    # --------------------------------------------------------

    text_columns = df.select_dtypes(include="object").columns

    for column in text_columns:
        df[column] = df[column].astype("string").str.strip()

    print("Whitespace cleaned.")

    # --------------------------------------------------------
    # 4. Handle missing value
    # --------------------------------------------------------

    print("\nMissing values BEFORE transformation:")

    print(df.isnull().sum())

    # customer_unique_id
    df["customer_unique_id"] = df["customer_unique_id"].fillna("unknown")

    # customer_city
    df["customer_city"] = df["customer_city"].fillna("unknown")

    # customer_state
    df["customer_state"] = df["customer_state"].fillna("unknown")

    # --------------------------------------------------------
    # 5. Convert zip code menjadi numeric
    # --------------------------------------------------------

    df["customer_zip_code_prefix"] = pd.to_numeric(
        df["customer_zip_code_prefix"], errors="coerce"
    )

    # Missing zip code menjadi 0
    df["customer_zip_code_prefix"] = (
        df["customer_zip_code_prefix"].fillna(0).astype("int64")
    )

    # --------------------------------------------------------
    # 6. Remove customer_id yang kosong
    # --------------------------------------------------------

    before_id = len(df)

    df = df.dropna(subset=["customer_id"])

    after_id = len(df)

    print(f"Rows removed because customer_id is empty : {before_id - after_id:,}")

    # --------------------------------------------------------
    # 7. Pastikan tipe data sesuai ClickHouse
    # --------------------------------------------------------

    df["customer_id"] = df["customer_id"].astype(str)

    df["customer_unique_id"] = df["customer_unique_id"].astype(str)

    df["customer_city"] = df["customer_city"].astype(str)

    df["customer_state"] = df["customer_state"].astype(str)

    # --------------------------------------------------------
    # 8. Select final columns
    # --------------------------------------------------------

    df = df[
        [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ]
    ]

    print("\nMissing values AFTER transformation:")

    print(df.isnull().sum())

    print(f"\nRows after transformation : {len(df):,}")

    print("\nData preview:")

    print(df.head())

    return df


# ============================================================
# LOAD
# ============================================================


def load_data(df):

    print("\n" + "=" * 60)
    print("LOAD")
    print("=" * 60)

    client = Client(
        host="localhost",
        port=9000,
        database="olist",
        user="default",
        password="admin123",
    )

    data = df[
        [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ]
    ].values.tolist()

    client.execute(
        """
        INSERT INTO customers
        (
            customer_id,
            customer_unique_id,
            customer_zip_code_prefix,
            customer_city,
            customer_state
        )
        VALUES
        """,
        data,
    )

    print(f"Rows loaded: {len(data):,}")

    result = client.execute("SELECT count() FROM customers")

    print(f"Rows in ClickHouse: {result[0][0]:,}")

    client.disconnect()

# ============================================================
# MAIN ETL PIPELINE
# ============================================================


def main():

    print("\n")
    print("=" * 60)
    print("OLIST CUSTOMER ETL PIPELINE")
    print("=" * 60)

    # EXTRACT
    df = extract_data()

    # TRANSFORM
    df = transform_data(df)

    # LOAD
    load_data(df)

    print("\n" + "=" * 60)
    print("ETL PIPELINE COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()

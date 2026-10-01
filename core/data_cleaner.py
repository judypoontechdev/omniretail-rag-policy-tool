import os
import re
import pandas as pd
from core.config import CSV_PATH

def clean_customer_orders(file_path: str = CSV_PATH) -> pd.DataFrame:
    """
    Cleans messy transactional order data:
    1. Trims extraneous whitespace and quotes from string fields.
    2. Standardizes uppercase region codes.
    3. Coerces currency strings with symbols to valid numeric floats.
    4. Robustly parses mixed date formats (ISO, DD/MM/YYYY, Mon-YYYY).
    """
    if not os.path.exists(file_path):
        print(f"Warning: CSV file not found at {file_path}")
        return pd.DataFrame()

    df = pd.read_csv(file_path)

    # 1. Clean string columns and strip quotation padding
    str_cols = ["order_id", "customer_name", "product_name", "shipping_region", "order_status"]
    for col in str_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip(" \"'")
                .replace({"nan": None, "None": None, "N/A": None, "null": None, "": None})
            )

    # 2. Normalize region casing
    if "shipping_region" in df.columns:
        df["shipping_region"] = df["shipping_region"].str.upper()

    # 3. Clean numeric price fields and remove currency symbols
    if "order_amount" in df.columns:
        df["order_amount"] = (
            df["order_amount"]
            .astype(str)
            .str.replace(r"[£$,]", "", regex=True)
            .str.strip()
        )
        df["order_amount"] = pd.to_numeric(df["order_amount"], errors="coerce").fillna(0.0)

    # 4. Standardize dates without triggering parsing warnings
    if "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(df["order_date"], format="mixed", errors="coerce")

    return df

def get_order_by_id(order_id_raw: str) -> dict:
    """
    Retrieves a single sanitized order record matching an identifier,
    safely converting pandas NaT/NaN to None for clean JSON serialization.
    """
    if not order_id_raw:
        return {}

    df = clean_customer_orders()
    if df.empty:
        return {}

    # Normalize to OMNI-XXXX format
    normalized_id = str(order_id_raw).strip()
    if not normalized_id.startswith("OMNI-"):
        num_part = re.sub(r"\D", "", normalized_id)
        if num_part:
            normalized_id = f"OMNI-{num_part}"

    record = df[df["order_id"] == normalized_id]
    if record.empty:
        return {}

    row = record.iloc[0].to_dict()
    clean_row = {}
    for k, v in row.items():
        if pd.isna(v):
            clean_row[k] = None
        elif hasattr(v, "strftime"):
            clean_row[k] = v.strftime("%Y-%m-%d")
        else:
            clean_row[k] = v

    return clean_row

if __name__ == "__main__":
    cleaned_df = clean_customer_orders()
    print("=== Cleaned Data Preview ===")
    print(cleaned_df.head(3))
    print("\n=== Lookup Test (OMNI-1002) ===")
    print(get_order_by_id("OMNI-1002"))
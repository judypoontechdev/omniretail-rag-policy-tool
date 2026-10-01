import os
from core.config import POLICY_MD_PATH, CSV_PATH, EVAL_CSV_PATH
from core.vector_store import ingest_policy_to_chroma
from core.data_cleaner import clean_customer_orders

def setup_all():
    """
    Validates all data assets and populates the ChromaDB vector database.
    """
    print("=== Checking System Data Assets ===")
    
    # 1. Check data files existence
    for path, name in [
        (POLICY_MD_PATH, "Policy Manual (data/policy.md)"),
        (CSV_PATH, "Customer Transactions (data/customer_data.csv)"),
        (EVAL_CSV_PATH, "Evaluation Test Set (data/eval_testset.csv)")
    ]:
        if os.path.exists(path):
            print(f"Found: {name}")
        else:
            print(f"Missing: {name}")

    # 2. Ingest Policy to ChromaDB
    print("\n=== Ingesting Policy Chunks into ChromaDB ===")
    count = ingest_policy_to_chroma()
    print(f"✓ Vector store ready with {count} chunks indexed.")

    # 3. Verify Customer Data Cleaning
    print("\n=== Verifying Dirty Data Cleaning Pipeline ===")
    df = clean_customer_orders()
    print(f"Cleaned {len(df)} customer transaction rows successfully.")

    print("\nSetup Complete! You can now run the app via 'uvicorn main:app --reload'.")

if __name__ == "__main__":
    setup_all()
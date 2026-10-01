import os
import pandas as pd
from core.config import EVAL_CSV_PATH
from core.extractor import extract_inquiry_details
from core.rag_engine import run_rag_pipeline

def run_offline_evaluation():
    """
    Evaluates the RAG system against the ground truth test suite.
    Calculates Category Classification Accuracy and Policy Decision Accuracy.
    """
    if not os.path.exists(EVAL_CSV_PATH):
        print(f"❌ Evaluation dataset not found at: {EVAL_CSV_PATH}")
        return

    df = pd.read_csv(EVAL_CSV_PATH)
    total_cases = len(df)
    category_matches = 0
    decision_matches = 0

    results = []

    print(f"=== Starting Offline Evaluation on {total_cases} Test Cases ===")

    for _, row in df.iterrows():
        test_id = row.get("test_id")
        query = str(row.get("query", ""))
        expected_cat = str(row.get("expected_category", "")).strip().lower()
        expected_dec = str(row.get("expected_decision", "")).strip().lower()

        # Run extraction & pipeline
        inquiry_obj = extract_inquiry_details(query)
        res = run_rag_pipeline(inquiry_obj)

        actual_cat = res["category"].strip().lower()
        actual_dec = res["decision"].strip().lower()

        cat_correct = (actual_cat == expected_cat)
        dec_correct = (actual_dec in expected_dec or expected_dec in actual_dec)

        if cat_correct:
            category_matches += 1
        if dec_correct:
            decision_matches += 1

        results.append({
            "test_id": test_id,
            "query": query[:40] + "...",
            "expected_category": expected_cat,
            "actual_category": actual_cat,
            "category_correct": cat_correct,
            "expected_decision": expected_dec,
            "actual_decision": actual_dec,
            "decision_correct": dec_correct
        })

    cat_acc = (category_matches / total_cases) * 100
    dec_acc = (decision_matches / total_cases) * 100

    print("\n=== Evaluation Summary ===")
    print(f"Total Test Cases Evaluated: {total_cases}")
    print(f"Category Accuracy: {cat_acc:.1f}% ({category_matches}/{total_cases})")
    print(f"Decision Accuracy: {dec_acc:.1f}% ({decision_matches}/{total_cases})")

    # Output detailed dataframe preview
    eval_summary_df = pd.DataFrame(results)
    out_path = os.path.join(os.path.dirname(EVAL_CSV_PATH), "eval_results.csv")
    eval_summary_df.to_csv(out_path, index=False)
    print(f"✓ Detailed evaluation results exported to: {out_path}")

if __name__ == "__main__":
    run_offline_evaluation()
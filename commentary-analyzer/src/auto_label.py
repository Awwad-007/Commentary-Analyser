import os
import sys
import pickle
import pandas as pd

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

MODEL_PATH = "model/classifier.pkl"
VECTORIZER_PATH = "model/vectorizer.pkl"
LABELED_DIR = "data/labeled"
CONFIDENCE_THRESHOLD = 0.60  # below this = needs_review

def load_model():
    """Loads the trained classifier and vectorizer from disk."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
        print("Error: classifier.pkl or vectorizer.pkl not found in model/.")
        print("Run train.py first.")
        sys.exit(1)

    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(VECTORIZER_PATH, "rb") as f:
        vectorizer = pickle.load(f)

    return model, vectorizer

def label_file(csv_path, model, vectorizer):
    """
    Reads a cleaned CSV (must have a 'text' column), predicts a label
    and confidence score for each row, and flags low-confidence rows.
    """
    df = pd.read_csv(csv_path)

    if "text" not in df.columns:
        print(f"Skipping {csv_path}: no 'text' column found.")
        return None

    # Vectorize all the text at once
    X = vectorizer.transform(df["text"])

    # predict() gives the label, predict_proba() gives confidence per class
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)

    # For each row, the confidence is the highest probability across all classes
    confidences = probabilities.max(axis=1)

    df["predicted_label"] = predictions
    df["confidence"] = confidences.round(3)
    df["needs_review"] = df["confidence"] < CONFIDENCE_THRESHOLD

    # Keep only the columns we actually want in the output
    result = df[["text", "predicted_label", "confidence", "needs_review"]]
    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: py src\\auto_label.py data\\processed\\<filename>_clean.csv")
        print("\nExample:")
        print("  py src\\auto_label.py data\\processed\\elclassico_2024_clean.csv")
        sys.exit(1)

    csv_path = sys.argv[1]

    if not os.path.exists(csv_path):
        print(f"Error: file not found: {csv_path}")
        sys.exit(1)

    model, vectorizer = load_model()

    print(f"Labeling {csv_path} ...")
    result = label_file(csv_path, model, vectorizer)

    if result is None:
        return

    os.makedirs(LABELED_DIR, exist_ok=True)
    output_path = os.path.join(LABELED_DIR, "auto_labeled.csv")
    result.to_csv(output_path, index=False)

    total = len(result)
    needs_review_count = result["needs_review"].sum()

    print(f"\nLabeled {total} sentences")
    print(f"  {total - needs_review_count} confident predictions")
    print(f"  {needs_review_count} flagged as needs_review (confidence < {int(CONFIDENCE_THRESHOLD*100)}%)")
    print(f"\nSaved to {output_path}")

if __name__ == "__main__":
    main()
import os
import re
import pandas as pd

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"

def split_into_sentences(text):
    """
    Splits a blob of text into sentences.
    We split on '.', '!', or '?' followed by a space or newline,
    which is good enough for commentary-style text.
    """
    # Normalize newlines to spaces first so we don't split mid-sentence
    text = text.replace("\n", " ")
    # Split on sentence-ending punctuation followed by whitespace
    raw_sentences = re.split(r'(?<=[.!?])\s+', text)
    return raw_sentences

def clean_sentence(sentence):
    """
    Strips whitespace and returns None if the sentence is junk
    (empty or too short to be meaningful commentary).
    """
    cleaned = sentence.strip()
    if len(cleaned) < 20:
        return None
    return cleaned

def process_file(filepath, filename):
    """
    Reads one .txt file, splits + cleans it into sentences,
    and saves the result as a CSV in data/processed/.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    sentences = split_into_sentences(text)

    cleaned_sentences = []
    for s in sentences:
        cleaned = clean_sentence(s)
        if cleaned is not None:
            cleaned_sentences.append(cleaned)

    # Build the output dataframe with a single "text" column
    df = pd.DataFrame({"text": cleaned_sentences})

    # match_name is the filename without the .txt extension
    match_name = os.path.splitext(filename)[0]
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    output_path = os.path.join(PROCESSED_DIR, f"{match_name}_clean.csv")
    df.to_csv(output_path, index=False)

    print(f"{filename}: found {len(sentences)} raw sentences, kept {len(cleaned_sentences)} after cleaning")
    print(f"  -> saved to {output_path}")

def main():
    if not os.path.exists(RAW_DIR):
        print(f"No {RAW_DIR} folder found. Nothing to process.")
        return

    txt_files = [f for f in os.listdir(RAW_DIR) if f.endswith(".txt")]

    if not txt_files:
        print(f"No .txt files found in {RAW_DIR}.")
        return

    print(f"Found {len(txt_files)} file(s) to process: {txt_files}\n")

    for filename in txt_files:
        filepath = os.path.join(RAW_DIR, filename)
        process_file(filepath, filename)

if __name__ == "__main__":
    main()
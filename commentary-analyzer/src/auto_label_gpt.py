# auto-labels commentary using Groq (free forever)
# install: pip install groq python-dotenv

import os
import pandas as pd
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def label_sentence(sentence):
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",  # free model on Groq
            messages=[
                {
                    "role": "system",
                    "content": """You label football commentary sentences.
Label as exactly one of:
- hyped: dramatic, excited, emotional language
- neutral: factual, just describing what happened
- biased: favoring one team, unfair criticism of refs

Reply with ONLY the single word label. Nothing else."""
                },
                {
                    "role": "user",
                    "content": sentence
                }
            ],
            max_tokens=5,
            temperature=0
        )
        label = response.choices[0].message.content.strip().lower()
        if label not in ["hyped", "neutral", "biased"]:
            return "neutral"
        return label
    except Exception as e:
        print(f"error: {e}")
        return "neutral"

def auto_label_file(input_csv, output_csv="data/labeled/train.csv"):
    df = pd.read_csv(input_csv)
    if "text" not in df.columns:
        print("CSV must have a text column")
        return

    print(f"labeling {len(df)} sentences with Groq (free)...")
    labels = []

    for i, row in df.iterrows():
        label = label_sentence(row["text"])
        labels.append(label)
        print(f"{i+1}/{len(df)} — {label}: {row['text'][:60]}...")
        time.sleep(0.3)

    df["label"] = labels

    try:
        existing = pd.read_csv(output_csv)
        combined = pd.concat([existing, df[["text","label"]]], ignore_index=True)
        combined.drop_duplicates(subset="text", inplace=True)
        combined.to_csv(output_csv, index=False)
        print(f"done — train.csv now has {len(combined)} rows")
    except FileNotFoundError:
        df[["text","label"]].to_csv(output_csv, index=False)
        print(f"created train.csv with {len(df)} rows")

if __name__ == "__main__":
    auto_label_file("data/processed/elclassico_2024_clean.csv")
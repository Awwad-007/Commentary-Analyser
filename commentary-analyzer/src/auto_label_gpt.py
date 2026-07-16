# uses openai to automatically label commentary sentences
# much faster than doing it manually
# needs OPENAI_API_KEY in your .env file

import os
import pandas as pd
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def label_sentence(sentence):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """You are labeling football commentary sentences.
Label each sentence as exactly one of these three categories:
- hyped: dramatic, excited, emotional language about a great moment
- neutral: factual description of what happened, no emotion
- biased: favoring one team, criticizing refs unfairly, loaded language against a team

Reply with ONLY the label — one word, nothing else."""
                },
                {
                    "role": "user",
                    "content": sentence
                }
            ],
            max_tokens=10,
            temperature=0
        )
        label = response.choices[0].message.content.strip().lower()
        if label not in ["hyped", "neutral", "biased"]:
            return "neutral"
        return label
    except Exception as e:
        print(f"error labeling: {e}")
        return "neutral"

def auto_label_file(input_csv, output_csv=None):
    df = pd.read_csv(input_csv)
    if "text" not in df.columns:
        print("CSV must have a 'text' column")
        return

    print(f"labeling {len(df)} sentences...")
    labels = []
    for i, row in df.iterrows():
        label = label_sentence(row["text"])
        labels.append(label)
        print(f"{i+1}/{len(df)} — {label}: {row['text'][:60]}...")
        time.sleep(0.5)  # avoid hitting rate limits

    df["label"] = labels

    if output_csv is None:
        output_csv = "data/labeled/train.csv"

    # append to existing train.csv instead of overwriting
    try:
        existing = pd.read_csv(output_csv)
        combined = pd.concat([existing, df[["text", "label"]]], ignore_index=True)
        combined.drop_duplicates(subset="text", inplace=True)
        combined.to_csv(output_csv, index=False)
        print(f"added {len(df)} rows — train.csv now has {len(combined)} total rows")
    except FileNotFoundError:
        df[["text", "label"]].to_csv(output_csv, index=False)
        print(f"created train.csv with {len(df)} rows")

if __name__ == "__main__":
    # run on your processed file
    auto_label_file("data/processed/elclassico_2024_clean.csv")
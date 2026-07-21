# generates diverse training data using Groq (free)
# run: py src\generate_data.py

import os
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
import time

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_sentences(label, count=50):
    prompt = f"""Generate {count} unique, varied football commentary sentences that are clearly "{label}".

Rules:
- Each sentence must be different — vary the players, teams, moments, style
- Make them sound like real TV commentary
- Do NOT number them
- One sentence per line
- Only output the sentences, nothing else

Label definitions:
- hyped: dramatic, excited, emotional (goals, saves, big moments)
- neutral: factual, calm description of what happened
- biased: clearly favoring one team OR unfairly criticizing refs/opponents"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.9
    )
    
    raw = response.choices[0].message.content.strip()
    sentences = [s.strip() for s in raw.split("\n") if len(s.strip()) > 20]
    return sentences

def build_dataset():
    all_rows = []
    labels = ["hyped", "neutral", "biased"]
    
    for label in labels:
        print(f"generating {label} sentences...")
        sentences = generate_sentences(label, count=80)
        for s in sentences:
            all_rows.append({"text": s, "label": label})
        print(f"got {len(sentences)} {label} sentences")
        time.sleep(2)

    df = pd.DataFrame(all_rows)
    df.drop_duplicates(subset="text", inplace=True)

    try:
        existing = pd.read_csv("data/labeled/train.csv")
        combined = pd.concat([existing, df], ignore_index=True)
        combined.drop_duplicates(subset="text", inplace=True)
        combined.to_csv("data/labeled/train.csv", index=False)
        print(f"done — train.csv now has {len(combined)} rows")
    except FileNotFoundError:
        df.to_csv("data/labeled/train.csv", index=False)
        print(f"created train.csv with {len(df)} rows")

if __name__ == "__main__":
    build_dataset()
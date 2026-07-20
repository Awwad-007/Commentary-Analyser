import os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import pandas as pd
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sentence_transformers import SentenceTransformer

# load data
df = pd.read_csv("data/labeled/train.csv")
print(f"loaded {len(df)} rows")
print(df["label"].value_counts())

# check balance
min_count = df["label"].value_counts().min()
if min_count < 10:
    print("warning: some labels have very few examples — run generate_data.py first")

# encode text using sentence transformer
print("encoding sentences...")
encoder = SentenceTransformer("all-MiniLM-L6-v2")
X = encoder.encode(df["text"].tolist(), show_progress_bar=True)
y = df["label"]

# split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# train
clf = LogisticRegression(max_iter=1000)
clf.fit(X_train, y_train)

# evaluate
predictions = clf.predict(X_test)
print("\nresults:")
print(classification_report(y_test, predictions))

# save
os.makedirs("model", exist_ok=True)
pickle.dump(clf, open("model/classifier.pkl", "wb"))
pickle.dump(encoder, open("model/encoder.pkl", "wb"))
print("saved classifier.pkl and encoder.pkl")
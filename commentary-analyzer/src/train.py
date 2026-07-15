import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import pickle

# step 1 — load your labeled data
df = pd.read_csv("data/labeled/train.csv")
print(f"loaded {len(df)} labeled rows")
print(df["label"].value_counts())

# step 2 — split into training and testing
X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["label"], test_size=0.2, random_state=42
)

# step 3 — convert text to numbers (TF-IDF)
vectorizer = TfidfVectorizer()
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# step 4 — train the model
model = LogisticRegression()
model.fit(X_train_vec, y_train)

# step 5 — see how well it did
predictions = model.predict(X_test_vec)
print("\nmodel results:")
print(classification_report(y_test, predictions))

# step 6 — save the model so app.py can use it later
pickle.dump(model, open("model/classifier.pkl", "wb"))
pickle.dump(vectorizer, open("model/vectorizer.pkl", "wb"))
print("\nmodel saved to model/")
# ⚽ Football Commentary Bias Detector

An ML-powered web app that analyzes football commentary and detects 
whether each line is **hyped**, **neutral**, or **biased**.

## What it does
- Pick a famous match from a dropdown (UCL Final, El Clásico)
- OR paste any commentary text manually
- Get a full bias report: team share, commentator score, line-by-line breakdown

## Tech Stack
- Python, scikit-learn, Streamlit, pandas
- TF-IDF + Logistic Regression classifier
- HuggingFace Transformers (upgrade path)

## Run locally
pip install -r requirements.txt
streamlit run app\app.py

## Project Structure
data/raw/          → raw commentary text files
data/labeled/      → hand-labeled training data
data/matches/      → pre-analyzed match JSONs
model/             → trained classifier
src/               → data processing scripts
app/               → Streamlit frontend
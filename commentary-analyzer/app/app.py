import streamlit as st
import pickle
import json
import os
import sys
import pandas as pd

# fix path so app can find all project files
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─── load model ───────────────────────────────────────────────
@st.cache_resource
def load_model():
    model = pickle.load(open("model/classifier.pkl", "rb"))
    vectorizer = pickle.load(open("model/vectorizer.pkl", "rb"))
    return model, vectorizer

# ─── load match list ──────────────────────────────────────────
@st.cache_data
def load_matches():
    matches_dir = "data/matches"
    if not os.path.exists(matches_dir):
        return {}
    matches = {}
    for f in os.listdir(matches_dir):
        if f.endswith(".json"):
            with open(os.path.join(matches_dir, f), encoding="utf-8") as file:
                data = json.load(file)
                matches[data["match"]] = data
    return matches

# ─── analyze raw text live ────────────────────────────────────
def analyze_text(text, model, vectorizer):
    lines = [l.strip() for l in text.strip().split("\n") if len(l.strip()) > 20]
    if not lines:
        return []
    vecs = vectorizer.transform(lines)
    labels = model.predict(vecs)
    probs = model.predict_proba(vecs).max(axis=1)
    return [{"text": l, "label": lab, "confidence": round(float(p)*100, 1)}
            for l, lab, p in zip(lines, labels, probs)]

# ─── render bias report ───────────────────────────────────────
def render_report(lines_data, match_info=None):
    if not lines_data:
        st.warning("no commentary lines to analyze")
        return

    df = pd.DataFrame(lines_data)

    # match info header
    if match_info:
        st.markdown(f"### {match_info.get('match', '')}")
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"🎙️ {match_info.get('commentator', '')} — {match_info.get('channel', '')}")
        with col2:
            st.caption(f"📅 {match_info.get('date', '')}")
        if match_info.get("summary"):
            st.info(match_info["summary"])
        st.divider()

    # stat boxes
    total = len(df)
    hyped_pct = round(len(df[df.label == "hyped"]) / total * 100)
    neutral_pct = round(len(df[df.label == "neutral"]) / total * 100)
    biased_pct = round(len(df[df.label == "biased"]) / total * 100)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔥 Hyped", f"{hyped_pct}%")
    with col2:
        st.metric("😐 Neutral", f"{neutral_pct}%")
    with col3:
        st.metric("⚠️ Biased", f"{biased_pct}%")

    # bias score
    st.divider()
    bias_score = biased_pct
    if bias_score < 20:
        st.success(f"🟢 Commentator Bias Score: {bias_score}/100 — fairly balanced")
    elif bias_score < 40:
        st.warning(f"🟡 Commentator Bias Score: {bias_score}/100 — some bias detected")
    else:
        st.error(f"🔴 Commentator Bias Score: {bias_score}/100 — strong bias detected")

    # team share bars (mode 1 only)
    if match_info and match_info.get("team_share"):
        st.divider()
        st.markdown("**Commentary share by team:**")
        for team, pct in match_info["team_share"].items():
            st.write(team)
            st.progress(int(pct) / 100, text=f"{pct}%")

    # line by line breakdown
    st.divider()
    st.markdown("**Line-by-line breakdown:**")
    emoji_map = {"hyped": "🔥", "neutral": "😐", "biased": "⚠️"}
    for _, row in df.iterrows():
        emoji = emoji_map.get(row["label"], "")
        conf = f" ({row['confidence']}%)" if "confidence" in row else ""
        st.markdown(f"{emoji} `{row['label'].upper()}{conf}` — {row['text']}")

# ─── main app ─────────────────────────────────────────────────
st.set_page_config(page_title="Football Commentary Bias Detector", page_icon="⚽", layout="wide")
st.title("⚽ Football Commentary Bias Detector")
st.caption("Find out if your commentator is actually biased — or just dramatic.")

model, vectorizer = load_model()
matches = load_matches()

mode = st.sidebar.radio("Choose mode", [
    "🏆 Pick a famous match",
    "📺 YouTube link",
    "✍️ Paste your own"
])

st.sidebar.divider()
st.sidebar.caption("Built by Awwad | ML Project")

# ─── mode 1: predefined matches ───────────────────────────────
if mode == "🏆 Pick a famous match":
    if not matches:
        st.error("no match files found in data/matches/")
    else:
        selected = st.selectbox("Select a match", list(matches.keys()))
        match_data = matches[selected]
        lines_data = match_data.get("lines", [])
        render_report(lines_data, match_info=match_data)

# ─── mode 2: youtube link ─────────────────────────────────────
elif mode == "📺 YouTube link":
    st.markdown("Paste any football match YouTube link and we'll fetch the transcript automatically.")
    url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
    if st.button("Fetch & Analyze") and url:
        with st.spinner("fetching transcript..."):
            try:
                from src.youtube_fetch import fetch_transcript
                text = fetch_transcript(url)
                if text:
                    st.success(f"fetched {len(text)} characters of commentary")
                    lines_data = analyze_text(text, model, vectorizer)
                    render_report(lines_data)
                else:
                    st.error("could not fetch transcript — try a different video or use paste mode")
            except ImportError:
                st.error("youtube-transcript-api not installed. run: pip install youtube-transcript-api")

# ─── mode 3: paste your own ───────────────────────────────────
elif mode == "✍️ Paste your own":
    st.markdown("Paste any commentary text below — one line per sentence works best.")
    text = st.text_area("Commentary text", height=200,
                        placeholder="Paste match commentary here...\nEach line will be analyzed separately.")
    if st.button("Analyze") and text:
        with st.spinner("analyzing..."):
            lines_data = analyze_text(text, model, vectorizer)
            render_report(lines_data)
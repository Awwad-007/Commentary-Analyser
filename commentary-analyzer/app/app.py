import os
import json
import pickle
import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
MATCHES_DIR = "data/matches"
MODEL_PATH = "model/classifier.pkl"
VECTORIZER_PATH = "model/vectorizer.pkl"

# ─────────────────────────────────────────────
# PAGE CONFIG (must be the first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Football Commentary Bias Detector",
    page_icon="⚽",
    layout="wide",
)

# ─────────────────────────────────────────────
# CACHED LOADERS
# Streamlit re-runs the whole script on every interaction,
# so we cache anything slow/expensive (loading the model,
# reading files) to avoid redoing it every single time.
# ─────────────────────────────────────────────

@st.cache_resource
def load_model():
    """Loads the trained classifier + vectorizer once and reuses them."""
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(VECTORIZER_PATH, "rb") as f:
        vectorizer = pickle.load(f)
    return model, vectorizer


@st.cache_data
def list_match_files():
    """Returns a list of (display_name, filepath) for every JSON in data/matches/."""
    if not os.path.exists(MATCHES_DIR):
        return []

    files = [f for f in os.listdir(MATCHES_DIR) if f.endswith(".json")]
    matches = []
    for f in files:
        # Turn "ucl_final_2024.json" into "Ucl Final 2024" for the dropdown label
        display_name = f.replace(".json", "").replace("_", " ").title()
        matches.append((display_name, os.path.join(MATCHES_DIR, f)))
    return matches


def load_match_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────
# CORE ANALYSIS LOGIC
# Both modes end up calling this same function so the
# report always looks and behaves identically.
# ─────────────────────────────────────────────

def analyze_lines_live(lines, model, vectorizer):
    """
    Takes a list of raw text lines, runs them through the trained
    model, and returns a list of {"text": ..., "label": ...} dicts,
    same shape as what's stored in the match JSON files.
    """
    if not lines:
        return []

    X = vectorizer.transform(lines)
    predictions = model.predict(X)

    return [{"text": text, "label": label} for text, label in zip(lines, predictions)]


def compute_stats(lines):
    """
    Given a list of {"text", "label"} dicts, returns:
    - percentage of hyped / neutral / biased lines
    - a bias_score (0-100), calculated as the % of biased lines
    """
    total = len(lines)
    if total == 0:
        return {"hyped": 0, "neutral": 0, "biased": 0}, 0

    counts = {"hyped": 0, "neutral": 0, "biased": 0}
    for line in lines:
        label = line.get("label", "neutral")
        if label in counts:
            counts[label] += 1

    percentages = {k: round((v / total) * 100) for k, v in counts.items()}
    bias_score = percentages["biased"]  # simple definition: % of biased lines

    return percentages, bias_score


# ─────────────────────────────────────────────
# REPORT DISPLAY
# This single function renders the report for EITHER mode,
# so Mode 1 (JSON) and Mode 2 (live text) always look the same.
# ─────────────────────────────────────────────

def render_report(match_title, commentator, channel, summary, lines, team_share=None):
    st.header(match_title)

    info_bits = []
    if commentator:
        info_bits.append(f"**Commentator:** {commentator}")
    if channel:
        info_bits.append(f"**Channel:** {channel}")
    if info_bits:
        st.caption(" | ".join(info_bits))

    if summary:
        st.write(summary)

    st.divider()

    percentages, bias_score = compute_stats(lines)

    # ── 3 stat boxes ──
    col1, col2, col3 = st.columns(3)
    col1.metric("Hyped", f"{percentages['hyped']}%")
    col2.metric("Neutral", f"{percentages['neutral']}%")
    col3.metric("Biased", f"{percentages['biased']}%")

    st.divider()

    # ── Team commentary share bar ──
    if team_share:
        st.subheader("Team Commentary Share")
        for team, share in team_share.items():
            st.write(f"{team} — {share}%")
            st.progress(share / 100)

        st.divider()

    # ── Commentator bias score ──
    st.subheader("Commentator Bias Score")
    st.write(f"**{bias_score} / 100**")
    st.progress(bias_score / 100)
    if bias_score < 20:
        st.success("Low bias detected — mostly neutral commentary.")
    elif bias_score < 50:
        st.warning("Moderate bias detected — some loaded language present.")
    else:
        st.error("High bias detected — commentary leans strongly one way.")

    st.divider()

    # ── Line-by-line breakdown ──
    st.subheader("Line-by-Line Breakdown")

    label_colors = {
        "hyped": "🟠",
        "neutral": "⚪",
        "biased": "🔴",
    }

    df = pd.DataFrame(lines)
    df["label"] = df["label"].apply(lambda l: f"{label_colors.get(l, '')} {l}")
    df = df.rename(columns={"text": "Commentary Line", "label": "Label"})

    st.dataframe(df, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# SIDEBAR — MODE SELECTOR
# ─────────────────────────────────────────────

st.sidebar.title("⚽ Bias Detector")
mode = st.sidebar.radio("Choose a mode:", ["Pick a match", "Paste your own"])

# ─────────────────────────────────────────────
# MODE 1 — PICK A MATCH
# ─────────────────────────────────────────────

if mode == "Pick a match":
    matches = list_match_files()

    if not matches:
        st.warning(
            "No match files found in data/matches/. "
            "Add a .json file there first (see Task 3)."
        )
    else:
        display_names = [m[0] for m in matches]
        selected_name = st.sidebar.selectbox("Select a match:", display_names)

        # Find the matching filepath for the selected display name
        selected_filepath = next(fp for name, fp in matches if name == selected_name)
        match_data = load_match_json(selected_filepath)

        render_report(
            match_title=match_data.get("match", "Unknown Match"),
            commentator=match_data.get("commentator", ""),
            channel=match_data.get("channel", ""),
            summary=match_data.get("summary", ""),
            lines=match_data.get("lines", []),
            team_share=match_data.get("team_share"),
        )

# ─────────────────────────────────────────────
# MODE 2 — PASTE YOUR OWN
# ─────────────────────────────────────────────

else:
    st.sidebar.write("Paste commentary lines below, one per line.")

    raw_text = st.text_area(
        "Paste commentary text here (one line per sentence):",
        height=250,
        placeholder="Real Madrid take an early lead through Vinicius Junior...\nWhat a strike, absolutely unstoppable!\n...",
    )

    match_title = st.text_input("Match title (optional):", value="Custom Commentary Analysis")

    analyze_clicked = st.button("Analyze")

    if analyze_clicked:
        if not raw_text.strip():
            st.error("Please paste some commentary text first.")
        else:
            # Split on newlines, drop empty lines
            lines_input = [l.strip() for l in raw_text.split("\n") if l.strip()]

            model, vectorizer = load_model()
            analyzed_lines = analyze_lines_live(lines_input, model, vectorizer)

            render_report(
                match_title=match_title,
                commentator="",
                channel="",
                summary="",
                lines=analyzed_lines,
                team_share=None,  # can't infer team share from raw pasted text
            )
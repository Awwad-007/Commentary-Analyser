import streamlit as st
import pickle
import json
import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─── page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Football Commentary Bias Detector",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── global CSS ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Orbitron:wght@400;700;900&display=swap');

/* ── base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0f1d;
    color: #F9FAFB;
}
.stApp {
    background: linear-gradient(135deg, #0a0f1d 0%, #111827 50%, #0d1526 100%);
    min-height: 100vh;
}

/* ── hide streamlit default chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 2rem 2.5rem; max-width: 1200px; }

/* ── sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #070c1a 0%, #0e1525 100%);
    border-right: 1px solid rgba(241,191,0,0.15);
}
[data-testid="stSidebar"] .stRadio label {
    color: #9CA3AF !important;
    font-size: 0.875rem;
    padding: 0.4rem 0;
    transition: color 0.2s;
}
[data-testid="stSidebar"] .stRadio label:hover { color: #FFD700 !important; }

/* ── inputs ── */
.stTextInput input, .stTextArea textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(241,191,0,0.2) !important;
    border-radius: 10px !important;
    color: #F9FAFB !important;
    font-family: 'Inter', sans-serif !important;
    transition: border 0.3s, box-shadow 0.3s;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border: 1px solid rgba(241,191,0,0.6) !important;
    box-shadow: 0 0 20px rgba(241,191,0,0.1) !important;
}

/* ── selectbox ── */
.stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(241,191,0,0.2) !important;
    border-radius: 10px !important;
    color: #F9FAFB !important;
}

/* ── buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #E31B23, #c0151c) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.8rem !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.03em !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(227,27,35,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) scale(1.02) !important;
    box-shadow: 0 8px 25px rgba(227,27,35,0.5) !important;
    background: linear-gradient(135deg, #ff2530, #E31B23) !important;
}

/* ── progress bars ── */
.stProgress > div > div {
    background: linear-gradient(90deg, #E31B23, #FFD700) !important;
    border-radius: 99px !important;
}
.stProgress > div {
    background: rgba(255,255,255,0.06) !important;
    border-radius: 99px !important;
}

/* ── divider ── */
hr { border-color: rgba(241,191,0,0.12) !important; }

/* ── spinner ── */
.stSpinner > div { border-top-color: #FFD700 !important; }
</style>
""", unsafe_allow_html=True)

# ─── helper html components ───────────────────────────────────
def glass_card(content_html, glow="gold"):
    color = "#FFD700" if glow == "gold" else "#E31B23"
    st.markdown(f"""
    <div style="
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(241,191,0,0.18);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 0 30px rgba(227,27,35,0.07), inset 0 1px 0 rgba(255,255,255,0.05);
        margin-bottom: 1rem;
    ">{content_html}</div>
    """, unsafe_allow_html=True)

def metric_card(label, value, color="#FFD700", icon=""):
    st.markdown(f"""
    <div style="
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(241,191,0,0.15);
        border-radius: 14px;
        padding: 1.2rem 1rem;
        text-align: center;
        box-shadow: 0 0 20px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    ">
        <div style="font-size:1.6rem;margin-bottom:0.3rem">{icon}</div>
        <div style="font-size:2rem;font-weight:800;color:{color};
                    font-family:'Orbitron',sans-serif;
                    text-shadow: 0 0 20px {color}66;">{value}</div>
        <div style="font-size:0.75rem;color:#9CA3AF;
                    text-transform:uppercase;letter-spacing:0.08em;
                    margin-top:0.3rem;">{label}</div>
    </div>
    """, unsafe_allow_html=True)

def line_card(text, label, confidence=None):
    colors = {
        "hyped":   {"bg": "rgba(241,191,0,0.08)",  "border": "#FFD700", "badge": "#FFD700",  "text": "#000", "icon": "🔥"},
        "neutral": {"bg": "rgba(99,102,241,0.08)",  "border": "#6366f1", "badge": "#6366f1",  "text": "#fff", "icon": "😐"},
        "biased":  {"bg": "rgba(227,27,35,0.08)",   "border": "#E31B23", "badge": "#E31B23",  "text": "#fff", "icon": "⚠️"},
    }
    c = colors.get(label, colors["neutral"])
    conf_html = ""
    if confidence:
        conf_html = f'<span style="font-size:0.7rem;color:#9CA3AF;margin-left:0.5rem">{confidence}% confident</span>'
    st.markdown(f"""
    <div style="
        background: {c['bg']};
        border-left: 3px solid {c['border']};
        border-radius: 0 10px 10px 0;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
    ">
        <span style="font-size:0.875rem;color:#F9FAFB;flex:1;line-height:1.5">{c['icon']} {text}</span>
        <div style="display:flex;align-items:center;gap:0.5rem;flex-shrink:0">
            {conf_html}
            <span style="
                background:{c['badge']};
                color:{c['text']};
                font-size:0.65rem;
                font-weight:700;
                padding:0.2rem 0.6rem;
                border-radius:99px;
                text-transform:uppercase;
                letter-spacing:0.06em;
            ">{label}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── load model ───────────────────────────────────────────────
@st.cache_resource
def load_model():
    try:
        clf     = pickle.load(open("model/classifier.pkl", "rb"))
        encoder = pickle.load(open("model/encoder.pkl",    "rb"))
        return clf, encoder
    except FileNotFoundError:
        st.error("model files not found — run src/train.py first")
        st.stop()

# ─── load matches ─────────────────────────────────────────────
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

# ─── analyze text ─────────────────────────────────────────────
def analyze_text(text, model, encoder):
    lines = [l.strip() for l in text.strip().split("\n") if len(l.strip()) > 10]
    if not lines:
        return []
    embeddings = encoder.encode(lines)
    labels     = model.predict(embeddings)
    probs      = model.predict_proba(embeddings).max(axis=1)
    return [{"text": l, "label": lab, "confidence": round(float(p)*100, 1)}
            for l, lab, p in zip(lines, labels, probs)]

# ─── render report ────────────────────────────────────────────
def render_report(lines_data, match_info=None):
    if not lines_data:
        st.warning("no commentary lines found to analyze")
        return

    df    = pd.DataFrame(lines_data)
    total = len(df)

    hyped_pct   = round(len(df[df.label == "hyped"])   / total * 100)
    neutral_pct = round(len(df[df.label == "neutral"]) / total * 100)
    biased_pct  = round(len(df[df.label == "biased"])  / total * 100)

    # match header
    if match_info:
        st.markdown(f"""
        <div style="margin-bottom:1.5rem">
            <div style="font-family:'Orbitron',sans-serif;font-size:1.4rem;
                        font-weight:700;color:#FFD700;
                        text-shadow:0 0 30px rgba(241,191,0,0.4);
                        margin-bottom:0.3rem">
                🏆 {match_info.get('match','')}
            </div>
            <div style="color:#9CA3AF;font-size:0.85rem">
                🎙️ {match_info.get('commentator','')} &nbsp;·&nbsp;
                📺 {match_info.get('channel','')} &nbsp;·&nbsp;
                📅 {match_info.get('date','')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        if match_info.get("summary"):
            st.markdown(f"""
            <div style="
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(241,191,0,0.15);
                border-radius:12px;
                padding:1rem 1.2rem;
                color:#9CA3AF;
                font-size:0.875rem;
                line-height:1.7;
                margin-bottom:1.5rem;
            ">💬 {match_info['summary']}</div>
            """, unsafe_allow_html=True)

    # stat cards
    c1, c2, c3 = st.columns(3)
    with c1: metric_card("Hyped Lines",   f"{hyped_pct}%",   "#FFD700", "🔥")
    with c2: metric_card("Neutral Lines", f"{neutral_pct}%", "#6366f1", "😐")
    with c3: metric_card("Biased Lines",  f"{biased_pct}%",  "#E31B23", "⚠️")

    st.markdown("<br>", unsafe_allow_html=True)

    # bias score
    bias_score = biased_pct
    if bias_score < 20:
        verdict = ("🟢 Balanced Commentary", "#22c55e")
    elif bias_score < 40:
        verdict = ("🟡 Some Bias Detected",  "#FFD700")
    else:
        verdict = ("🔴 Strong Bias Detected", "#E31B23")

    st.markdown(f"""
    <div style="
        background:rgba(255,255,255,0.03);
        border:1px solid rgba(241,191,0,0.15);
        border-radius:14px;
        padding:1.2rem 1.5rem;
        display:flex;
        align-items:center;
        justify-content:space-between;
        margin-bottom:1.5rem;
    ">
        <div>
            <div style="font-size:0.75rem;color:#9CA3AF;
                        text-transform:uppercase;letter-spacing:0.08em;
                        margin-bottom:0.3rem">Commentator Bias Score</div>
            <div style="font-size:1rem;font-weight:600;color:{verdict[1]}">{verdict[0]}</div>
        </div>
        <div style="font-family:'Orbitron',sans-serif;font-size:2.5rem;
                    font-weight:900;color:{verdict[1]};
                    text-shadow:0 0 30px {verdict[1]}66">
            {bias_score}<span style="font-size:1rem">/100</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # team share bars (mode 1 only)
    if match_info and match_info.get("team_share"):
        st.markdown("""
        <div style="font-size:0.75rem;color:#9CA3AF;
                    text-transform:uppercase;letter-spacing:0.08em;
                    margin-bottom:0.8rem">⚖️ Commentary Share by Team</div>
        """, unsafe_allow_html=True)
        for team, pct in match_info["team_share"].items():
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.6rem">
                <span style="font-size:0.8rem;color:#F9FAFB;width:140px;flex-shrink:0">{team}</span>
                <div style="flex:1;height:8px;background:rgba(255,255,255,0.06);
                            border-radius:99px;overflow:hidden">
                    <div style="width:{pct}%;height:100%;
                                background:linear-gradient(90deg,#E31B23,#FFD700);
                                border-radius:99px"></div>
                </div>
                <span style="font-size:0.8rem;color:#FFD700;width:36px;text-align:right">{pct}%</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # line by line
    st.markdown("""
    <div style="font-size:0.75rem;color:#9CA3AF;
                text-transform:uppercase;letter-spacing:0.08em;
                margin-bottom:0.8rem">📋 Line-by-Line Breakdown</div>
    """, unsafe_allow_html=True)
    for _, row in df.iterrows():
        conf = row.get("confidence", None)
        line_card(row["text"], row["label"], conf)

# ─── sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1rem 0 1.5rem 0">
        <div style="font-size:2.5rem;margin-bottom:0.5rem">⚽</div>
        <div style="font-family:'Orbitron',sans-serif;font-size:0.75rem;
                    font-weight:700;color:#FFD700;letter-spacing:0.15em;
                    text-transform:uppercase">Commentary</div>
        <div style="font-family:'Orbitron',sans-serif;font-size:0.75rem;
                    font-weight:700;color:#E31B23;letter-spacing:0.15em;
                    text-transform:uppercase">Bias Detector</div>
    </div>
    <hr style="border-color:rgba(241,191,0,0.12);margin-bottom:1.2rem">
    """, unsafe_allow_html=True)

    mode = st.radio("Select Mode", [
        "🏆 Pick a famous match",
        "📺 YouTube link",
        "✍️ Paste your own"
    ])

    st.markdown("""
    <hr style="border-color:rgba(241,191,0,0.12);margin:1.5rem 0 1rem 0">
    <div style="
        background:rgba(255,255,255,0.03);
        border:1px solid rgba(241,191,0,0.12);
        border-radius:12px;
        padding:0.9rem;
        text-align:center;
    ">
        <div style="font-size:0.7rem;color:#9CA3AF;
                    text-transform:uppercase;letter-spacing:0.08em;
                    margin-bottom:0.4rem">Built by</div>
        <div style="font-weight:700;color:#F9FAFB;font-size:0.9rem">Awwad</div>
        <div style="font-size:0.7rem;color:#FFD700;margin-top:0.2rem">ML Portfolio Project</div>
    </div>
    """, unsafe_allow_html=True)

# ─── main title ───────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:2rem 0 2.5rem 0">
    <div style="font-family:'Orbitron',sans-serif;font-size:2.2rem;
                font-weight:900;line-height:1.2;margin-bottom:0.5rem">
        <span style="color:#F9FAFB">Football Commentary</span><br>
        <span style="color:#FFD700;
                     text-shadow:0 0 40px rgba(241,191,0,0.5)">Bias Detector</span>
        <span style="color:#E31B23"> ⚽</span>
    </div>
    <div style="color:#9CA3AF;font-size:0.9rem;max-width:500px;margin:0 auto">
        Powered by Sentence Transformers · Built for the beautiful game
    </div>
</div>
""", unsafe_allow_html=True)

model, encoder = load_model()
matches        = load_matches()

# ─── mode 1: predefined matches ───────────────────────────────
if mode == "🏆 Pick a famous match":
    if not matches:
        st.error("no match files found in data/matches/")
    else:
        selected   = st.selectbox("🏟️ Select a match", list(matches.keys()))
        match_data = matches[selected]
        lines_data = match_data.get("lines", [])
        st.markdown("<br>", unsafe_allow_html=True)
        render_report(lines_data, match_info=match_data)

# ─── mode 2: youtube link ─────────────────────────────────────
elif mode == "📺 YouTube link":
    st.markdown("""
    <div style="color:#9CA3AF;font-size:0.875rem;margin-bottom:1rem">
        ⚡ Paste any football match YouTube link — we'll fetch and analyze the transcript automatically.
    </div>
    """, unsafe_allow_html=True)
    url = st.text_input("🔗 YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
    if st.button("⚡ Fetch & Analyze") and url:
        with st.spinner("fetching transcript..."):
            try:
                from src.youtube_fetch import fetch_transcript
                text = fetch_transcript(url)
                if text:
                    st.success(f"✅ fetched {len(text)} characters of commentary")
                    lines_data = analyze_text(text, model, encoder)
                    st.markdown("<br>", unsafe_allow_html=True)
                    render_report(lines_data)
                else:
                    st.error("could not fetch transcript — try a different video or use paste mode")
            except ImportError:
                st.error("youtube-transcript-api not installed. run: pip install youtube-transcript-api")

# ─── mode 3: paste your own ───────────────────────────────────
elif mode == "✍️ Paste your own":
    st.markdown("""
    <div style="color:#9CA3AF;font-size:0.875rem;margin-bottom:1rem">
        ✍️ Paste any commentary text below — one sentence per line works best.
    </div>
    """, unsafe_allow_html=True)
    text = st.text_area("📝 Commentary text", height=200,
                        placeholder="Paste match commentary here...\nEach line will be analyzed separately.")
    if st.button("⚽ Analyze Commentary") and text:
        with st.spinner("analyzing..."):
            lines_data = analyze_text(text, model, encoder)
            st.markdown("<br>", unsafe_allow_html=True)
            render_report(lines_data)
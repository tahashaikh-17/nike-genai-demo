# app.py
# Nike x GenAI — Shoppable demo (Streamlit)
# Visual refresh: Nike-like header, dark theme accents, premium product cards, assistant panel

import os
import pandas as pd
import streamlit as st

# --------- OPTIONAL: OpenAI for chat ---------
USE_OPENAI = True
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    USE_OPENAI = False

# --------- DATA ---------
DATA_FILE = "nike_products.csv"   # required columns: id,name,category,price,image,description,tags

# --------- PAGE CONFIG ---------
st.set_page_config(
    page_title="Nike • GenAI Shopping",
    page_icon="🧠",
    layout="wide",
)

# --------- CUSTOM CSS (Nike-inspired) ---------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');

:root {
  --bg: #0f0f0f;
  --card: #121212;
  --ink: #f5f5f5;
  --muted: #9ca3af;
  --primary: #ffffff;
  --accent: #111111;
  --pill: #1a1a1a;
  --border: #1f1f1f;
}

html, body, [data-testid="stAppViewContainer"] *, .stMarkdown, .stText, .stButton, .stTextInput, .stSelectbox {
  font-family: 'Montserrat', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif !important;
}

[data-testid="stAppViewContainer"] {
  background: var(--bg);
  color: var(--ink);
}

header[data-testid="stHeader"] { display: none; }
footer { visibility: hidden; }

.nike-nav {
  position: sticky; top: 0; z-index: 999;
  width: 100%;
  background: #000000 !important;
  border-bottom: 1px solid var(--border);
  padding: 14px 20px;
  display: flex; align-items: center; gap: 20px;
}
.nike-logo {
  height: 20px; width: auto; filter: invert(1);
}
.nike-title {
  font-weight: 800; letter-spacing: 0.3px; font-size: 14px; color: #fff;
  opacity: .9;
}

.hero {
  padding: 28px 6px 10px 6px;
}
.hero h1 {
  margin: 0 0 4px 0;
  font-size: 34px;
  line-height: 1.1;
  font-weight: 800;
}
.hero p {
  margin: 0; color: var(--muted);
}

.filters {
  margin: 12px 0 6px 0;
  display: flex; gap: 10px; flex-wrap: wrap;
}

.grid {
  display: grid; gap: 16px;
  grid-template-columns: repeat(12, 1fr);
}
.col-9 { grid-column: span 9; }
.col-3 { grid-column: span 3; }

.card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 16px; overflow: hidden;
  transition: transform .15s ease, border-color .15s ease;
}
.card:hover { transform: translateY(-2px); border-color: #2a2a2a; }
.card-img {
  width: 100%; aspect-ratio: 4/3; object-fit: cover; background: #0b0b0b;
}
.card-content { padding: 12px; }
.card-name { font-weight: 700; font-size: 16px; margin: 6px 0 2px 0; }
.card-sub { color: var(--muted); font-size: 12px; margin-bottom: 8px; }
.card-row { display:flex; align-items:center; justify-content:space-between; gap: 10px; }
.price { font-weight: 700; }
.tag {
  background: var(--pill); color: var(--muted);
  font-size: 11px; border: 1px solid var(--border);
  border-radius: 999px; padding: 3px 8px;
}

.panel {
  background: linear-gradient(180deg, #151515, #0f0f0f);
  border: 1px solid var(--border); border-radius: 20px; padding: 16px;
}
.panel h3 {
  margin: 0 0 10px 0; font-size: 18px; font-weight: 800;
}
.chat-bubble {
  background: #121212; border: 1px solid var(--border); border-radius: 12px;
  padding: 10px 12px; margin-bottom: 8px; color: #ddd; font-size: 14px;
}
.chat-bubble.user { background: #0d0d0d; }
.small { color: var(--muted); font-size: 12px; }

.divider { height:1px; width:100%; background: var(--border); margin: 18px 0; }
</style>
""", unsafe_allow_html=True)

# --------- HEADER (Nike-like) ---------
st.markdown(
    """
    <div class="nike-nav">
        <img class="nike-logo" src="https://upload.wikimedia.org/wikipedia/commons/a/a6/Logo_NIKE.svg" alt="NIKE">
        <div class="nike-title">NIKE • GENAI SHOPPING</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------- STATE ---------
if "name" not in st.session_state:
    st.session_state.name = ""
if "cart" not in st.session_state:
    st.session_state.cart = []
if "messages" not in st.session_state:
    st.session_state.messages = []

# --------- LOAD DATA ---------
@st.cache_data
def load_products(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = ["id","name","category","price","image","description","tags"]
    cols_lower = [c.lower() for c in df.columns]
    for r in required:
        if r not in cols_lower:
            raise ValueError(f"CSV missing required column: {r}")
    def split_tags(x):
        import pandas as pd
        if pd.isna(x): return []
        return [t.strip() for t in str(x).replace("|", ",").split(",") if t.strip()]
    df.columns = [c.lower() for c in df.columns]
    df["tag_list"] = df["tags"].apply(split_tags)
    return df

try:
    products = load_products(DATA_FILE)
except Exception as e:
    st.error(f"Could not load `{DATA_FILE}`: {e}")
    st.stop()

# --------- HERO ---------
st.markdown(
    f"""
    <div class="hero">
      <h1>Shop smarter with your AI stylist</h1>
      <p>Tell me your sport, style, or goal — I’ll size you up, compare fits, and recommend the right gear. Built for { "you" if st.session_state.name else "your Nike journey"}.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------- FILTERS / BAG ---------
colL, colM, colR = st.columns([2,5,3], gap="small")

with colL:
    st.markdown("**Your name**")
    st.session_state.name = st.text_input(
        "name",
        placeholder="e.g., Taha",
        label_visibility="collapsed",
        value=st.session_state.name,
    )

with colM:
    st.markdown('<div class="filters">', unsafe_allow_html=True)
    cats = ["All"] + sorted(products["category"].dropna().unique().tolist())
    cat = st.selectbox("Category", cats, index=0, label_visibility="collapsed")
    price_max = int(products["price"].max())
    price = st.slider("Budget", 40, price_max, (40, price_max), label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

with colR:
    total = sum([p["price"] for p in st.session_state.cart]) if st.session_state.cart else 0
    st.markdown(f"**Bag**  \n<span class='small'>{len(st.session_state.cart)} items • ${total:.2f}</span>", unsafe_allow_html

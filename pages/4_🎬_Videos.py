"""
CryptoSphere — Page 4: Video Learning Center
Curated crypto educational & analysis videos by category.
Works without YouTube API key via static curated library.
"""
import streamlit as st

st.set_page_config(page_title="Videos · CryptoSphere", page_icon="🎬", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-title { font-size:2rem; font-weight:800;
  background: linear-gradient(135deg,#EC4899,#EF4444);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.video-card {
  background: rgba(19,19,43,0.9);
  border: 1px solid rgba(124,58,237,0.2);
  border-radius: 14px;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  height: 100%;
}
.video-card:hover { transform: translateY(-4px); box-shadow: 0 12px 36px rgba(124,58,237,0.2); }
.video-meta { padding: 0.8rem; }
.video-title { color: #E2E8F0; font-weight: 600; font-size: 0.85rem; line-height: 1.4; }
.video-channel { color: #7C3AED; font-size: 0.75rem; margin-top: 0.3rem; font-weight: 500; }
iframe { width: 100%; border-radius: 0; display: block; }
.search-hint { color: #64748B; font-size: 0.8rem; font-style: italic; }
.cat-desc { color: #64748B; font-size: 0.85rem; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

from src.youtube_feed import get_curated_videos, search_crypto_videos, video_embed_html, CURATED_VIDEOS

st.markdown('<span class="page-title">🎬 Crypto Video Center</span>', unsafe_allow_html=True)
st.caption("Curated cryptocurrency videos — education, analysis, DeFi & more")

# ── Search bar ─────────────────────────────────────────────────────────────
search_query = st.text_input(
    "🔍 Search for crypto videos",
    placeholder="e.g. Bitcoin halving, DeFi protocols, Ethereum merge…",
    key="yt_search"
)

if search_query:
    with st.spinner(f'Searching for "{search_query}"…'):
        results = search_crypto_videos(search_query, max_results=6)
    st.subheader(f'Results for "{search_query}"')
    cols = st.columns(3)
    for i, vid in enumerate(results):
        with cols[i % 3]:
            embed = video_embed_html(vid["id"], width=340, height=190)
            st.markdown(
                f'<div class="video-card">'
                f'{embed}'
                f'<div class="video-meta">'
                f'<div class="video-title">{vid["title"]}</div>'
                f'<div class="video-channel">📺 {vid.get("channel","")}</div>'
                f'</div></div>',
                unsafe_allow_html=True
            )
    st.divider()

# ── Category tabs ──────────────────────────────────────────────────────────
categories  = list(CURATED_VIDEOS.keys())
cat_descs   = {
    "Market Analysis": "Current market trends, price analysis & predictions from top crypto analysts.",
    "Education":       "Learn the fundamentals of blockchain, crypto, and digital assets from scratch.",
    "DeFi":            "Deep dives into decentralized finance — protocols, yield farming, and DEXes.",
    "Bitcoin":         "Everything about Bitcoin — mining, halvings, store of value, and its future.",
    "Altcoins":        "In-depth analysis of Ethereum, Solana, Cardano, Chainlink, and more.",
}

tabs = st.tabs([f"{'📊' if c=='Market Analysis' else '🎓' if c=='Education' else '💧' if c=='DeFi' else '₿' if c=='Bitcoin' else '🪙'} {c}" for c in categories])

for tab, cat in zip(tabs, categories):
    with tab:
        st.markdown(f'<p class="cat-desc">{cat_descs.get(cat,"")}</p>', unsafe_allow_html=True)
        videos = get_curated_videos(cat)
        grid   = st.columns(3)
        for i, vid in enumerate(videos):
            with grid[i % 3]:
                embed = video_embed_html(vid["id"], width=340, height=192)
                st.markdown(
                    f'<div class="video-card">'
                    f'{embed}'
                    f'<div class="video-meta">'
                    f'<div class="video-title">{vid["title"]}</div>'
                    f'<div class="video-channel">📺 {vid.get("channel","")}</div>'
                    f'</div></div><br>',
                    unsafe_allow_html=True
                )

st.divider()
st.markdown("""
<div style="color:#334155;font-size:0.75rem;text-align:center;">
🎬 Videos powered by YouTube · Add your YouTube Data API v3 key in 
<code>.streamlit/secrets.toml</code> to enable live video search
</div>
""", unsafe_allow_html=True)

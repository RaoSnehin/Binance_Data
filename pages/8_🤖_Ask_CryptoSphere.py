"""
CryptoSphere — Page 8: AI Chatbot
Ask anything about CryptoSphere, crypto concepts, or live market data.
Powered by Google Gemini 2.0 Flash with live CoinGecko context injection for truthful answers.
"""
import streamlit as st
import html as html_module

st.set_page_config(
    page_title="Ask CryptoSphere · AI Chatbot",
    page_icon="🤖",
    layout="wide",
)

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Page title */
.page-title {
    font-size: 2.2rem; font-weight: 800;
    background: linear-gradient(135deg, #A855F7 0%, #3B82F6 50%, #06B6D4 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.page-sub { color: #64748B; font-size: 0.9rem; margin-top: -0.3rem; margin-bottom: 1rem; }

/* Message bubbles */
.msg-user {
    display: flex; justify-content: flex-end; margin-bottom: 1.2rem;
}
.msg-user-bubble {
    background: linear-gradient(135deg, #7C3AED, #3B82F6);
    color: #fff;
    padding: 0.85rem 1.2rem;
    border-radius: 18px 18px 4px 18px;
    max-width: 72%;
    font-size: 0.92rem;
    line-height: 1.6;
    box-shadow: 0 4px 20px rgba(124,58,237,0.3);
    white-space: pre-wrap;
}
.msg-bot {
    display: flex; align-items: flex-start; gap: 0.75rem; margin-bottom: 1.2rem;
}
.bot-avatar {
    width: 38px; height: 38px; border-radius: 50%; flex-shrink: 0;
    background: linear-gradient(135deg, #A855F7, #06B6D4);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; color: #fff; line-height: 38px; text-align: center;
}
.msg-bot-bubble {
    background: rgba(19,19,43,0.95);
    border: 1px solid rgba(124,58,237,0.2);
    color: #E2E8F0;
    padding: 0.9rem 1.2rem;
    border-radius: 4px 18px 18px 18px;
    max-width: 76%;
    font-size: 0.92rem;
    line-height: 1.75;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    white-space: pre-wrap;
}
.msg-bot-bubble b  { color: #A78BFA; }
.msg-bot-bubble code {
    background: rgba(124,58,237,0.2); padding: 0.1rem 0.4rem;
    border-radius: 4px; font-size: 0.85rem; color: #A78BFA;
}

/* Live badge */
.live-badge {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.25);
    border-radius: 999px; padding: 0.3rem 0.9rem;
    font-size: 0.78rem; color: #22C55E; font-weight: 500;
}
.live-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #22C55E; display: inline-block;
    animation: pulse-dot 1.5s ease-in-out infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.7); }
}

/* Chat divider */
.chat-divider { border: none; border-top: 1px solid rgba(124,58,237,0.12); margin: 0.8rem 0; }

/* API note */
.api-note {
    background: rgba(234,179,8,0.08); border: 1px solid rgba(234,179,8,0.25);
    border-radius: 10px; padding: 0.7rem 0.9rem; font-size: 0.78rem;
    color: #CA8A04; margin-top: 0.5rem;
}

/* Disclaimer */
.disclaimer-bar {
    background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.2);
    border-radius: 10px; padding: 0.5rem 1rem; font-size: 0.75rem;
    color: #F87171; margin-top: 0.8rem; text-align: center;
}

/* Welcome card */
.welcome-card {
    background: linear-gradient(135deg, rgba(124,58,237,0.08), rgba(59,130,246,0.06));
    border: 1px solid rgba(124,58,237,0.2);
    border-radius: 16px; padding: 1.4rem 1.6rem; margin-bottom: 1.2rem;
}

/* Typing cursor blink */
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
.cursor { animation: blink 0.8s infinite; }
</style>
""", unsafe_allow_html=True)

from src.chatbot import get_live_context_for_prompt, stream_gemini_response


# ── API Key resolution ─────────────────────────────────────────────────────────
def resolve_api_key() -> str:
    try:
        key = st.secrets.get("GEMINI_KEY", "")
        if key and key.strip():
            return key.strip()
    except Exception:
        pass
    return st.session_state.get("gemini_api_key", "")


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🤖 CryptoBot Settings")
    st.divider()

    manual_key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="Paste your key here…",
        help="Get a free key at https://aistudio.google.com/app/apikey",
        key="gemini_key_input",
    )
    if manual_key and manual_key.strip():
        st.session_state["gemini_api_key"] = manual_key.strip()

    active_key = resolve_api_key()
    if active_key:
        st.success("✅ API key active", icon="🔑")
    else:
        st.markdown("""
        <div class="api-note">
        🔑 <b>No API key set.</b><br>
        Get a <b>free</b> Gemini key at:<br>
        <a href="https://aistudio.google.com/app/apikey" target="_blank">
        aistudio.google.com</a>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📡 Live Market Context")

    with st.spinner("Fetching live prices…"):
        live_ctx = get_live_context_for_prompt(20)

    if live_ctx.get("available"):
        fg = live_ctx.get("fear_greed", {})
        st.markdown(
            '<div class="live-badge"><span class="live-dot"></span>Live data active</div>',
            unsafe_allow_html=True,
        )
        st.caption(f"⏱ {live_ctx.get('timestamp', '')}")
        st.caption(f"😱 Fear & Greed: **{fg.get('value','?')}** — {fg.get('label','?')}")

        for sym, info in list(live_ctx.get("prices", {}).items())[:6]:
            price = info.get("price_usd", 0)
            chg   = info.get("change_24h", 0) or 0
            color = "#22C55E" if chg >= 0 else "#EF4444"
            arrow = "▲" if chg >= 0 else "▼"
            ps    = (f"${price:,.2f}" if price >= 1000
                     else f"${price:.4f}" if price >= 1
                     else f"${price:.6f}")
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;'
                f'padding:0.25rem 0;border-bottom:1px solid rgba(124,58,237,0.08);'
                f'font-size:0.8rem">'
                f'<span style="color:#94A3B8;font-weight:500">{sym}</span>'
                f'<span style="color:#E2E8F0;font-weight:600">{ps}</span>'
                f'<span style="color:{color}">{arrow}{abs(chg):.1f}%</span></div>',
                unsafe_allow_html=True,
            )
    else:
        st.warning("⚠️ Live data unavailable — bot will not cite prices")

    st.divider()
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.pop("pending_chip", None)
        st.rerun()

    st.markdown(
        '<div style="color:#334155;font-size:0.72rem;margin-top:0.5rem;text-align:center">'
        '⚠️ Not financial advice · Prices: CoinGecko</div>',
        unsafe_allow_html=True,
    )


# ── Session State ──────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">🤖 Ask CryptoSphere</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-sub">AI assistant powered by Google Gemini 2.0 Flash · '
    'Answers use <b>live CoinGecko prices</b> — prices are never fabricated</div>',
    unsafe_allow_html=True,
)


# ── Welcome card ───────────────────────────────────────────────────────────────
if not st.session_state.chat_history:
    st.markdown("""
    <div class="welcome-card">
      <div style="font-size:1.1rem;font-weight:700;color:#E2E8F0;margin-bottom:0.6rem">
        👋 Hi! I'm CryptoBot
      </div>
      <div style="color:#94A3B8;font-size:0.88rem;line-height:1.8">
        I can help you with:<br>
        &nbsp;&nbsp;• <b style="color:#A78BFA">Platform features</b> — portfolio, contagion lab, forecasts, news, academy<br>
        &nbsp;&nbsp;• <b style="color:#A78BFA">Crypto concepts</b> — DeFi, NFTs, blockchain, Layer-2, staking, halving<br>
        &nbsp;&nbsp;• <b style="color:#A78BFA">Live prices</b> — I use real CoinGecko data fetched just now<br>
        &nbsp;&nbsp;• <b style="color:#A78BFA">General learning</b> — what is Bitcoin, how do wallets work, etc.
      </div>
      <div style="color:#EF4444;font-size:0.78rem;margin-top:0.8rem">
        ⚠️ I never make up prices. If I don't have live data for a coin, I'll tell you to check the Live Market page.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Suggested questions
    st.markdown("**✨ Suggested questions — click to ask:**")
    SUGGESTED = [
        ("💼", "How does the portfolio tracker work?"),
        ("₿", "What is Bitcoin's current price?"),
        ("😱", "What is the Fear & Greed Index right now?"),
        ("🌊", "What is the Contagion Lab feature?"),
        ("🔮", "How does the 365-day forecast work?"),
        ("🎓", "What is DeFi explained simply?"),
        ("⏳", "When is the next Bitcoin halving?"),
        ("📊", "What does BTC dominance mean?"),
    ]
    cols = st.columns(4)
    for i, (emoji, question) in enumerate(SUGGESTED):
        with cols[i % 4]:
            label = f"{emoji} {question[:28]}…" if len(question) > 28 else f"{emoji} {question}"
            if st.button(label, key=f"chip_{i}", use_container_width=True):
                st.session_state["pending_chip"] = question


# ── Render existing chat history ───────────────────────────────────────────────
for msg in st.session_state.chat_history:
    safe_content = html_module.escape(msg["content"])
    if msg["role"] == "user":
        st.markdown(
            f'<div class="msg-user">'
            f'<div class="msg-user-bubble">{safe_content}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="msg-bot">'
            f'<div class="bot-avatar">🤖</div>'
            f'<div class="msg-bot-bubble">{safe_content}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── Chat input ─────────────────────────────────────────────────────────────────
st.markdown('<hr class="chat-divider">', unsafe_allow_html=True)

pending_chip = st.session_state.pop("pending_chip", None)
user_input = st.chat_input("Ask me anything about CryptoSphere or crypto…")
final_input = user_input or pending_chip


# ── Process new message ────────────────────────────────────────────────────────
if final_input and final_input.strip():
    query = final_input.strip()
    api_key = resolve_api_key()

    # Add to history
    st.session_state.chat_history.append({"role": "user", "content": query})

    # Display user bubble immediately
    safe_q = html_module.escape(query)
    st.markdown(
        f'<div class="msg-user"><div class="msg-user-bubble">{safe_q}</div></div>',
        unsafe_allow_html=True,
    )

    # Stream bot response
    typing_ph = st.empty()
    response_ph = st.empty()

    typing_ph.markdown(
        '<div class="msg-bot">'
        '<div class="bot-avatar">🤖</div>'
        '<div class="msg-bot-bubble" style="color:#64748B;font-style:italic">'
        'CryptoBot is thinking<span class="cursor">…</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    full_response = ""
    try:
        for chunk in stream_gemini_response(query, st.session_state.chat_history, api_key, live_ctx):
            full_response += chunk
            partial_safe = html_module.escape(full_response)
            response_ph.markdown(
                f'<div class="msg-bot">'
                f'<div class="bot-avatar">🤖</div>'
                f'<div class="msg-bot-bubble">{partial_safe}<span class="cursor">▌</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            typing_ph.empty()
    except Exception as e:
        full_response = f"❌ Streaming error: {e}"

    # Final render (no cursor)
    typing_ph.empty()
    final_safe = html_module.escape(full_response)
    response_ph.markdown(
        f'<div class="msg-bot">'
        f'<div class="bot-avatar">🤖</div>'
        f'<div class="msg-bot-bubble">{final_safe}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Save to history
    st.session_state.chat_history.append({"role": "assistant", "content": full_response})


# ── Disclaimer ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="disclaimer-bar">
⚠️ <b>Disclaimer:</b> CryptoBot provides information for educational purposes only.
Live prices sourced from CoinGecko (~1 min delay). <b>This is NOT financial advice.</b>
Always do your own research before making investment decisions.
</div>
""", unsafe_allow_html=True)

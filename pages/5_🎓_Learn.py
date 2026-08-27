"""
CryptoSphere — Page 5: Crypto Academy
Educational hub: glossary, concept cards, how-to guides, and a 10-question quiz.
"""
import streamlit as st
import random

st.set_page_config(page_title="Crypto Academy · CryptoSphere", page_icon="🎓", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-title { font-size:2rem; font-weight:800;
  background: linear-gradient(135deg,#22C55E,#06B6D4);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.concept-card {
  background: rgba(19,19,43,0.95);
  border: 1px solid rgba(124,58,237,0.25);
  border-radius: 16px;
  padding: 1.4rem;
  margin-bottom: 1rem;
  transition: all 0.25s;
}
.concept-card:hover { border-color: #7C3AED; box-shadow: 0 6px 28px rgba(124,58,237,0.2); }
.concept-icon { font-size: 2.4rem; margin-bottom: 0.6rem; display: block; }
.concept-title { color: #E2E8F0; font-weight: 700; font-size: 1.05rem; margin-bottom: 0.5rem; }
.concept-body  { color: #94A3B8; font-size: 0.85rem; line-height: 1.65; }
.glossary-term { color: #7C3AED; font-weight: 700; }
.glossary-def  { color: #CBD5E1; font-size: 0.88rem; }
.guide-step { background: rgba(124,58,237,0.08); border-left: 3px solid #7C3AED;
  border-radius: 0 10px 10px 0; padding: 0.7rem 1rem; margin-bottom: 0.6rem; color:#CBD5E1; font-size:0.88rem; }
.quiz-q { color:#E2E8F0; font-weight:600; font-size:0.95rem; margin-bottom:0.5rem; }
.correct { color:#22C55E; font-weight:600; }
.wrong   { color:#EF4444; font-weight:600; }
.score-badge { background:linear-gradient(135deg,#7C3AED,#06B6D4); color:white;
  border-radius:999px; padding:0.5rem 1.8rem; font-size:1.2rem; font-weight:700; display:inline-block; }
</style>
""", unsafe_allow_html=True)

st.markdown('<span class="page-title">🎓 Crypto Academy</span>', unsafe_allow_html=True)
st.caption("Learn crypto from scratch — concepts, glossary, guides & interactive quiz")

# ─────────────────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────────────────

CONCEPTS = [
    ("₿", "Bitcoin", "The original cryptocurrency created by Satoshi Nakamoto in 2009. Bitcoin is a decentralized digital currency with a fixed supply of 21 million coins. It uses a Proof-of-Work consensus mechanism and introduced the concept of blockchain to the world."),
    ("Ξ", "Ethereum", "The world's leading smart contract platform, created by Vitalik Buterin. Ethereum allows developers to build decentralized applications (dApps) using the EVM (Ethereum Virtual Machine). Transitioned to Proof-of-Stake in 'The Merge' in 2022."),
    ("🏦", "DeFi", "Decentralized Finance — financial services built on blockchains without banks or intermediaries. Includes lending (Aave), trading (Uniswap), yield farming, and stablecoins. DeFi protocols hold billions in Total Value Locked (TVL)."),
    ("🔗", "Blockchain", "A distributed ledger where transactions are grouped into blocks, cryptographically linked, and replicated across thousands of nodes. Once written, data is practically immutable. No single party controls it."),
    ("🖼️", "NFTs", "Non-Fungible Tokens — unique digital assets stored on a blockchain. Unlike Bitcoin (fungible), each NFT is one-of-a-kind. Used for digital art, gaming items, music, sports collectibles, and proof of ownership."),
    ("⚡", "Layer 2", "Scaling solutions built on top of Layer 1 blockchains (like Ethereum) to handle more transactions faster and cheaper. Examples: Polygon, Arbitrum, Optimism (rollups), and Bitcoin's Lightning Network."),
    ("🪙", "Stablecoins", "Cryptocurrencies pegged to a stable asset like the US Dollar. Types: fiat-backed (USDT, USDC), crypto-backed (DAI), and algorithmic. Used for trading, savings, and payments without volatility risk."),
    ("⛏️", "Mining", "The process of validating transactions and adding them to the blockchain using computational power (Proof-of-Work). Miners are rewarded with newly created cryptocurrency. Bitcoin mining uses ASICs and consumes significant energy."),
    ("🗳️", "Proof of Stake", "A consensus mechanism where validators 'stake' (lock up) cryptocurrency as collateral to validate transactions and create new blocks. More energy-efficient than Proof-of-Work. Used by Ethereum, Cardano, Solana."),
    ("📦", "Wallets", "Software or hardware that stores your private keys to access crypto. Hot wallets (Metamask, Trust Wallet) are connected to the internet. Cold wallets (Ledger, Trezor) are offline and more secure for long-term storage."),
    ("🔄", "DEX", "Decentralized Exchange — a peer-to-peer trading platform with no central authority. Uses Automated Market Makers (AMMs) and liquidity pools instead of order books. Examples: Uniswap, SushiSwap, Curve Finance."),
    ("🎯", "Halving", "Bitcoin's supply issuance is cut in half roughly every 4 years (every 210,000 blocks). This reduces the rate of new BTC entering circulation, historically triggering bull markets. Next halving: April 2028."),
]

GLOSSARY = {
    "HODL":      "Hold On for Dear Life — slang for holding crypto instead of selling during dips.",
    "FOMO":      "Fear Of Missing Out — buying during price peaks driven by hype.",
    "FUD":       "Fear, Uncertainty and Doubt — negative sentiment spread to drive prices down.",
    "ATH":       "All-Time High — the highest price a crypto asset has ever reached.",
    "Bull Market":"A period of rising prices and positive market sentiment.",
    "Bear Market":"A prolonged period of falling prices (typically >20% decline).",
    "Altcoin":   "Any cryptocurrency other than Bitcoin.",
    "Gas":       "Transaction fees on the Ethereum network, paid in ETH (specifically Gwei).",
    "Whale":     "An individual or entity holding a very large amount of cryptocurrency.",
    "DYOR":      "Do Your Own Research — a reminder to verify information before investing.",
    "Rekt":      "Slang for suffering a severe financial loss from bad trades.",
    "Pump & Dump":"Price manipulation scheme — artificially inflate price then sell off holdings.",
    "Moonshot":  "A very high-risk, very high-reward crypto investment.",
    "Rug Pull":  "A scam where developers abandon a project and run off with investors' funds.",
    "Staking":   "Locking up crypto to participate in network validation and earn rewards.",
    "APY":       "Annual Percentage Yield — return on investment over one year, with compounding.",
    "TVL":       "Total Value Locked — total capital deposited into DeFi protocols.",
    "CEX":       "Centralized Exchange — crypto exchange with a central authority (e.g., Binance).",
    "Web3":      "The decentralized vision of the internet powered by blockchain technology.",
    "Mempool":   "Memory pool — a waiting area for unconfirmed transactions on a blockchain.",
}

GUIDES = {
    "📊 How to Read a Candlestick Chart": [
        "Each candle represents a time period (1m, 1h, 1d, etc.)",
        "The body shows opening and closing prices. Green = price went up, Red = price went down.",
        "The wicks (thin lines) show the high and low prices during that period.",
        "A long green body with small wicks = strong buying pressure.",
        "A long red body = strong selling pressure — bears in control.",
        "Patterns like 'Doji' (tiny body) signal market indecision.",
    ],
    "🔒 How to Store Crypto Safely": [
        "Never keep large amounts on exchanges — they can be hacked (e.g., Mt. Gox).",
        "Use a hardware wallet (Ledger, Trezor) for long-term storage of significant amounts.",
        "Your private key = your crypto. Never share it with ANYONE.",
        "Write down your seed phrase (12-24 words) on paper and store offline in a safe place.",
        "Use a hot wallet (MetaMask) only for small amounts you're actively using.",
        "Enable 2FA on every exchange account. Use authenticator apps, not SMS.",
    ],
    "🏦 What is DeFi & How to Use It": [
        "DeFi = financial services without banks: lending, borrowing, trading, earning yield.",
        "You need a crypto wallet (MetaMask) and some ETH for gas fees to start.",
        "Uniswap lets you swap any ERC-20 token without an account — just connect your wallet.",
        "Aave lets you deposit crypto and earn interest, or borrow against your holdings.",
        "Always check the Total Value Locked (TVL) and audit history before using a protocol.",
        "Be aware of impermanent loss when providing liquidity to AMM pools.",
    ],
    "₿ Bitcoin Basics for Beginners": [
        "Bitcoin has a fixed supply of 21 million coins — no one can print more.",
        "Transactions are verified by miners using Proof-of-Work (SHA-256 algorithm).",
        "One Bitcoin = 100,000,000 Satoshis. You can buy fractions of a Bitcoin.",
        "Bitcoin is pseudonymous, not anonymous — all transactions are publicly visible.",
        "The halving event (every ~4 years) cuts block rewards in half, increasing scarcity.",
        "Bitcoin is accepted by major companies like Tesla, Microsoft, and PayPal.",
    ],
    "📈 Understanding Market Cycles": [
        "Crypto markets follow cycles driven by Bitcoin halvings (roughly every 4 years).",
        "Accumulation phase: Prices are flat/low. Smart money quietly buys in.",
        "Bull phase: Prices rise sharply. FOMO and mainstream media attention peak near the top.",
        "Distribution phase: Early investors start selling. Euphoria at the top.",
        "Bear phase: Prices fall 70-90%. Retail investors panic sell. Cycle resets.",
        "Indicators: Bitcoin Dominance, Fear & Greed Index, on-chain metrics (MVRV, NVT).",
    ],
}

QUIZ = [
    {"q": "What is the maximum supply of Bitcoin?", "options": ["21 million","100 million","50 million","Unlimited"], "ans": 0},
    {"q": "What year was Bitcoin's whitepaper published?", "options": ["2009","2008","2010","2007"], "ans": 1},
    {"q": "What does 'HODL' mean in crypto slang?", "options": ["A trading strategy","Hold On for Dear Life","Buy high sell low","A type of wallet"], "ans": 1},
    {"q": "What consensus mechanism does Ethereum currently use?", "options": ["Proof of Work","Delegated Proof of Stake","Proof of Stake","Proof of History"], "ans": 2},
    {"q": "Which of these is a Layer 2 scaling solution for Ethereum?", "options": ["Solana","Polygon","Litecoin","Dogecoin"], "ans": 1},
    {"q": "What is the primary purpose of a crypto 'gas fee'?", "options": ["To heat mining rigs","To pay transaction validators","To fund developer teams","To buy stablecoins"], "ans": 1},
    {"q": "What is a 'rug pull' in crypto?", "options": ["A sudden price dump by market makers","Developers abandoning a project and taking funds","A type of yield farming strategy","A Bitcoin mining technique"], "ans": 1},
    {"q": "What does 'TVL' stand for in DeFi?", "options": ["Total Value Listed","Tokenized Vault Leverage","Total Value Locked","Transaction Volume Logged"], "ans": 2},
    {"q": "Bitcoin halving occurs approximately every how many years?", "options": ["2 years","3 years","4 years","5 years"], "ans": 2},
    {"q": "What is a 'cold wallet'?", "options": ["A wallet stored in a cold country","An offline hardware device for storing crypto securely","An exchange wallet with 2FA","A wallet with a very low balance"], "ans": 1},
]

# ─────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs(["🧠 Key Concepts", "📖 Glossary", "📚 How-To Guides", "🧪 Quiz"])

# ── Tab 1: Concepts ────────────────────────────────────────────────────────
with tab1:
    st.markdown("### Core Concepts Every Crypto Investor Should Know")
    cols = st.columns(3)
    for i, (icon, title, body) in enumerate(CONCEPTS):
        with cols[i % 3]:
            st.markdown(
                f'<div class="concept-card">'
                f'<span class="concept-icon">{icon}</span>'
                f'<div class="concept-title">{title}</div>'
                f'<div class="concept-body">{body}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

# ── Tab 2: Glossary ────────────────────────────────────────────────────────
with tab2:
    st.markdown("### Crypto Glossary — 20 Essential Terms")
    search_term = st.text_input("🔍 Search glossary", placeholder="Type a term…")
    filtered = {k: v for k, v in GLOSSARY.items()
                if search_term.lower() in k.lower() or search_term.lower() in v.lower()} \
               if search_term else GLOSSARY

    for term, definition in filtered.items():
        st.markdown(
            f'<div style="padding:0.6rem 0;border-bottom:1px solid rgba(124,58,237,0.1);">'
            f'<span class="glossary-term">{term}</span> '
            f'<span class="glossary-def">— {definition}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

# ── Tab 3: Guides ──────────────────────────────────────────────────────────
with tab3:
    st.markdown("### Step-by-Step Crypto Guides")
    selected_guide = st.selectbox("Choose a guide", list(GUIDES.keys()))
    steps = GUIDES[selected_guide]
    st.markdown(f"**{selected_guide}**")
    for i, step in enumerate(steps, 1):
        st.markdown(f'<div class="guide-step"><b>Step {i}.</b> {step}</div>', unsafe_allow_html=True)

# ── Tab 4: Quiz ────────────────────────────────────────────────────────────
with tab4:
    st.markdown("### 🧪 Test Your Crypto IQ")
    st.caption("10 questions · No time limit · Instant scoring")

    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False

    if not st.session_state.quiz_submitted:
        with st.form("quiz_form"):
            for i, q in enumerate(QUIZ):
                st.markdown(f'<div class="quiz-q">Q{i+1}. {q["q"]}</div>', unsafe_allow_html=True)
                ans = st.radio("", q["options"], key=f"q_{i}", index=None, label_visibility="collapsed")
                st.session_state.quiz_answers[i] = ans
                st.markdown("<hr style='border:none;border-top:1px solid rgba(124,58,237,0.1);margin:0.5rem 0'>", unsafe_allow_html=True)
            submitted = st.form_submit_button("🎯 Submit Quiz", use_container_width=True)
            if submitted:
                st.session_state.quiz_submitted = True
                st.rerun()
    else:
        score = 0
        for i, q in enumerate(QUIZ):
            user_ans = st.session_state.quiz_answers.get(i)
            correct_txt = q["options"][q["ans"]]
            is_correct = user_ans == correct_txt
            if is_correct: score += 1
            icon = "✅" if is_correct else "❌"
            st.markdown(f'<div class="quiz-q">{icon} Q{i+1}. {q["q"]}</div>', unsafe_allow_html=True)
            if not is_correct:
                st.markdown(f'<span class="wrong">Your answer: {user_ans or "Not answered"}</span> &nbsp;·&nbsp; <span class="correct">Correct: {correct_txt}</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="correct">Correct: {correct_txt}</span>', unsafe_allow_html=True)
            st.markdown("<hr style='border:none;border-top:1px solid rgba(124,58,237,0.1);margin:0.4rem 0'>", unsafe_allow_html=True)

        grade = "🏆 Expert!" if score >= 9 else "🎓 Advanced" if score >= 7 else "📚 Intermediate" if score >= 5 else "🌱 Beginner"
        st.markdown(f"<br><div style='text-align:center'><span class='score-badge'>{grade} — {score}/10 Correct</span></div>", unsafe_allow_html=True)

        if st.button("🔄 Retake Quiz", use_container_width=True):
            st.session_state.quiz_submitted = False
            st.session_state.quiz_answers = {}
            st.rerun()

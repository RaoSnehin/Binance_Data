# 🌐 CryptoSphere

> **A centralized crypto intelligence platform for investors, traders & learners.**

[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?logo=streamlit)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 Features

| Tab | Feature | API Used |
|---|---|---|
| 🏠 **Home** | Live ticker, global stats, market heatmap, top movers | CoinGecko |
| 📊 **Live Market** | Full leaderboard, treemap, per-coin price history | CoinGecko |
| 🌊 **Contagion Lab** | PySpark volatility, ML buy/sell signals, correlation matrix | Local pipeline |
| 📰 **News Hub** | Live crypto news with sentiment badges | CryptoPanic + RSS |
| 🎬 **Videos** | Curated crypto education & analysis videos | YouTube (curated) |
| 🎓 **Academy** | Glossary, concept cards, how-to guides, 10-question quiz | Static |
| 💼 **Portfolio** | Virtual tracker with live P&L, charts, CSV export | CoinGecko |
| 🔮 **Forecast & AI** | F&G gauge, AI analyst verdicts, Bitcoin halving countdown, ML forecasts | Alternative.me + Local |

---

## 🚀 Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/cryptosphere.git
cd cryptosphere

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Add API keys
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml and add your keys

# 4. Launch
streamlit run app.py
```

Visit: **http://localhost:8501**

---

## 🌍 Deploy to Streamlit Community Cloud (Free)

**Your app will be live at: `https://cryptosphere-YOUR_NAME.streamlit.app`**

### Step-by-Step

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial CryptoSphere commit"
   git remote add origin https://github.com/YOUR_USERNAME/cryptosphere.git
   git push -u origin main
   ```

2. **Go to [share.streamlit.io](https://share.streamlit.io)**
   - Sign in with your GitHub account

3. **Click "New app"**
   - Repository: `YOUR_USERNAME/cryptosphere`
   - Branch: `main`
   - Main file: `app.py`
   - App URL: `cryptosphere` (→ `cryptosphere.streamlit.app`)

4. **Add Secrets** *(optional — app works without them)*
   - In Streamlit Cloud: **Settings → Secrets**
   - Paste:
     ```toml
     COINGECKO_KEY = "your-key-here"
     CRYPTOPANIC_KEY = "your-key-here"
     YOUTUBE_KEY = "your-key-here"
     ```

5. **Click Deploy!** 🎉

Your app auto-deploys every time you push to GitHub.

---

## 🔑 API Keys (All Free — Optional)

| API | Where to Get | Free Tier |
|---|---|---|
| CoinGecko | [coingecko.com/api](https://www.coingecko.com/en/api) | 30 calls/min |
| CryptoPanic | [cryptopanic.com/developers/api](https://cryptopanic.com/developers/api/) | Free, no CC |
| YouTube v3 | [console.cloud.google.com](https://console.cloud.google.com/) | 10,000 units/day |
| Alternative.me (Fear & Greed) | No key needed | Free |

> **The app works 100% without any API keys** — all features have graceful fallbacks.

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit, Plotly, Custom CSS (glassmorphism dark theme)
- **Data:** PySpark (local analytics pipeline), CoinGecko, Alternative.me, CryptoPanic, RSS
- **ML:** scikit-learn (Gradient Boosting Classifier, Quantile Regression)
- **Deployment:** Streamlit Community Cloud

---

## ⚠️ Disclaimer

> This platform is for **educational and demonstration purposes only**. Nothing on CryptoSphere constitutes financial advice. Always do your own research before investing.

---

*Built with ❤️ using Streamlit + PySpark*

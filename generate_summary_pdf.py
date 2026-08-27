"""
PDF Generator for CryptoSphere / Cryptiq Analytics — EY GDS Interview Summary Guide
Generates a structured, professional document named `summary.pdf`.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

PDF_FILENAME = "summary.pdf"

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(40, letter[1] - 30, "CryptoSphere — EY GDS Interview & Project Architecture Summary")
            self.drawRightString(letter[0] - 40, letter[1] - 30, "AI & Data Engineering")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(40, letter[1] - 34, letter[0] - 40, letter[1] - 34)
            
        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(40, 38, letter[0] - 40, 38)
        self.drawString(40, 26, "Confidential — Prepared for EY GDS Technical Interview")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 40, 26, page_text)
        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        PDF_FILENAME,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=46,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#1E1B4B")     # Deep Indigo / Navy
    SECONDARY = colors.HexColor("#4F46E5")   # Indigo Blue
    ACCENT = colors.HexColor("#7C3AED")      # Purple
    TEXT_DARK = colors.HexColor("#0F172A")   # Slate Dark Text
    TEXT_MUTED = colors.HexColor("#475569")  # Slate Muted Text
    BG_LIGHT = colors.HexColor("#F8FAFC")    # Slate Off-White
    BORDER_LIGHT = colors.HexColor("#E2E8F0")

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=PRIMARY,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=ACCENT,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=17,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=SECONDARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_DARK,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=4
    )

    callout_style = ParagraphStyle(
        'Callout_Text',
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=PRIMARY
    )

    q_style = ParagraphStyle(
        'Question_Style',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=PRIMARY,
        spaceBefore=6,
        spaceAfter=2
    )

    ans_style = ParagraphStyle(
        'Answer_Style',
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK,
        spaceAfter=8
    )

    story = []

    # ── HEADER & TITLE ────────────────────────────────────────────────────────
    story.append(Paragraph("CryptoSphere: Multi-Asset Crypto Intelligence Platform", title_style))
    story.append(Paragraph("End-to-End PySpark Big Data Pipeline, Quantile ML Forecasting & Grounded AI Architecture", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceAfter=10))

    # ── 1. EXECUTIVE PITCH ───────────────────────────────────────────────────
    story.append(Paragraph("1. Executive 60-Second Elevator Pitch", h1_style))
    pitch_text = """
    <b>CryptoSphere (Cryptiq Analytics)</b> is a centralized cryptocurrency intelligence and quantitative risk platform. 
    It unites distributed Big Data engineering, quantitative financial modeling, directional machine learning, 
    and grounded generative AI:
    <br/><br/>
    • <b>Big Data Ingestion:</b> An Apache PySpark pipeline processing <b>12,978 raw Binance spot CSV files</b> across 204 trading pairs, computing 16 technical and microstructure features.
    <br/>
    • <b>Systemic Risk & Contagion:</b> A 30-day rolling Pearson correlation matrix detecting cross-asset volatility spillover.
    <br/>
    • <b>Machine Learning:</b> A leakage-free <b>Gradient Boosting directional classifier</b> with dynamic CDF percentile thresholding and a <b>3-scenario Quantile Regression model (p10/p50/p90)</b> with exponential error decay for 365-day price trajectories.
    <br/>
    • <b>Storage & Interface:</b> An ACID-compliant <b>SQLite database</b> for persistent portfolio tracking and a <b>Google Gemini AI assistant</b> with live CoinGecko context injection for zero-hallucination accuracy.
    """
    
    pitch_table = Table([[Paragraph(pitch_text, callout_style)]], colWidths=[letter[0] - 80])
    pitch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(pitch_table)
    story.append(Spacer(1, 10))

    # ── 2. BUSINESS USE CASES & STAKEHOLDERS ─────────────────────────────────
    story.append(Paragraph("2. Target Audience & Business Value", h1_style))
    
    stakeholder_data = [
        [Paragraph("<b>Target Stakeholder</b>", body_style), Paragraph("<b>Business Problem</b>", body_style), Paragraph("<b>Platform Solution & Value</b>", body_style)],
        [Paragraph("<b>Quant Researchers & Risk Officers</b>", body_style), Paragraph("Hidden cross-asset contagion during market crashes.", body_style), Paragraph("<b>Contagion Lab:</b> 30-day dynamic Pearson correlation matrix and volatility distribution mapping.", body_style)],
        [Paragraph("<b>Portfolio Managers</b>", body_style), Paragraph("High tracking error and session data loss.", body_style), Paragraph("<b>Persistent Portfolio Engine:</b> SQLite-backed tracking with live mark-to-market P&L and allocation charts.", body_style)],
        [Paragraph("<b>Traders & Quant Analysts</b>", body_style), Paragraph("Single-point price forecasts fail in volatile regimes.", body_style), Paragraph("<b>Quantile Uncertainty Cone:</b> Probabilistic p10 (bear), p50 (median), and p90 (bull) 365-day price bounds.", body_style)],
        [Paragraph("<b>Retail Learners & Investors</b>", body_style), Paragraph("Data fragmentation and LLM price hallucinations.", body_style), Paragraph("<b>Grounded AI Assistant:</b> Google Gemini model injected with live real-time CoinGecko market context.", body_style)]
    ]
    
    st_table = Table(stakeholder_data, colWidths=[130, 150, 250])
    st_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EEF2FF")),
        ('TEXTCOLOR', (0, 0), (-1, 0), PRIMARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(st_table)
    story.append(Spacer(1, 10))

    # ── 3. FEATURE DEEP DIVE ─────────────────────────────────────────────────
    story.append(Paragraph("3. Detailed Feature Breakdown & Mathematical Modeling", h1_style))

    features = [
        ("Feature 1: Distributed Big Data Ingestion (PySpark)", 
         "Ingests 12,978 raw Binance spot CSV files across 204 pairs. Enforces strict StructType schema (open, high, low, close, volume, trades), extracts ticker symbols via regex path parsing, auto-normalizes timestamps across microsecond/millisecond scales, and deduplicates daily vs. monthly data."),
        
        ("Feature 2: 16-Dimensional Quantitative Signal Engineering", 
         "Calculates 16 statistical features over a 30-day window: Log Returns, EMA-12, EMA-26, MACD, RSI-14, 7-day and 14-day Rolling Volatility, Bollinger Band Position ((Price - SMA20)/(2*Std20)), Volume Surge Ratios, Lagged Bitcoin cross-returns, and risk-adjusted Safety Scores."),
        
        ("Feature 3: Leakage-Free Directional ML Classifier (src/classification.py)", 
         "Predicts tomorrow's market direction (Buy +1, Hold 0, Sell -1) using GradientBoostingClassifier. Implements dynamic empirical CDF percentile thresholds (p30 for sell, p70 for buy). Evaluated using 3-fold TimeSeriesSplit walk-forward validation with zero test-set leakage, achieving ~51.74% out-of-sample directional accuracy across 198 assets."),
        
        ("Feature 4: 365-Day Quantile Forecasting & Uncertainty Cone (src/forecasting.py)", 
         "Based on MMQR (Method of Moments Quantile Regression, Havidz et al.). Trains 3 quantile regressors using pinball loss at alpha = 0.10 (p10 pessimistic), 0.50 (p50 expected), and 0.90 (p90 optimistic). Applies an exponential error dampening factor exp(-t/180) to prevent variance explosion during multi-step recursive forecasting."),
        
        ("Feature 5: Systemic Risk & Financial Contagion Matrix (src/analytics.py)", 
         "Computes a dynamic 30-day rolling Pearson correlation matrix across all assets. Filters out stablecoins and illiquid tokens to isolate genuine cross-asset systemic risk and co-movement during market crashes."),
        
        ("Feature 6: Persistent SQLite Portfolio Tracker (src/database.py & Page 6)", 
         "Replaces volatile session memory with an embedded SQLite database (cryptosphere.db). Stores positions permanently across browser refreshes and computes live mark-to-market valuations, allocation pie charts, and P&L bar charts using real-time CoinGecko prices."),
        
        ("Feature 7: Zero-Hallucination Grounded AI Chatbot (src/chatbot.py & Page 8)", 
         "Powered by Google Gemini via direct HTTPS REST requests. Injects real-time CoinGecko top-20 prices, 24h market volume, BTC dominance, and Fear & Greed index into the system prompt with strict truthfulness negative constraints.")
    ]

    for title, desc in features:
        story.append(Paragraph(title, h2_style))
        story.append(Paragraph(desc, body_style))

    story.append(Spacer(1, 10))

    # ── 4. TECH STACK EXPLANATION ────────────────────────────────────────────
    story.append(Paragraph("4. Technology Stack & Architectural Decisions", h1_style))
    
    tech_data = [
        [Paragraph("<b>Technology</b>", body_style), Paragraph("<b>Role in Project</b>", body_style), Paragraph("<b>Why Chosen (Architectural Rationale)</b>", body_style)],
        [Paragraph("<b>Apache PySpark 3.5+</b>", body_style), Paragraph("Distributed ingestion, windowing & ETL.", body_style), Paragraph("Overcomes Pandas single-threaded memory limits across 12,978 raw CSV files.", body_style)],
        [Paragraph("<b>scikit-learn 1.3+</b>", body_style), Paragraph("Classification & Quantile Regression.", body_style), Paragraph("Provides pinball loss quantile regressors, TimeSeriesSplit CV, and joblib caching.", body_style)],
        [Paragraph("<b>Streamlit & Plotly</b>", body_style), Paragraph("Reactive web UI & financial charts.", body_style), Paragraph("Rapid Python-native presentation layer with interactive treemaps, gauges, and candlestick charts.", body_style)],
        [Paragraph("<b>SQLite3</b>", body_style), Paragraph("Persistent Portfolio Storage.", body_style), Paragraph("Zero-config, serverless ACID persistence (cryptosphere.db) surviving app restarts.", body_style)],
        [Paragraph("<b>Google Gemini REST API</b>", body_style), Paragraph("Conversational AI Assistant.", body_style), Paragraph("High inference speed; direct REST integration bypasses Python namespace collisions.", body_style)],
        [Paragraph("<b>Apache Parquet & Snappy</b>", body_style), Paragraph("Columnar Data Caching.", body_style), Paragraph("Reduces disk storage by 80% and enables sub-second dashboard load times.", body_style)]
    ]

    tech_table = Table(tech_data, colWidths=[120, 150, 260])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EEF2FF")),
        ('TEXTCOLOR', (0, 0), (-1, 0), PRIMARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 10))

    # ── 5. NON-TECHNICAL GLOSSARY ────────────────────────────────────────────
    story.append(Paragraph("5. Non-Technical Glossary for Business Stakeholders", h1_style))

    glossary_items = [
        ("Volatility", "How wildly an asset bounces up and down. High volatility means bumpy, risky rides; low volatility means steady, calm movement."),
        ("Financial Contagion", "When a crash in one coin spreads like a virus to infect other coins in the market (like falling dominoes)."),
        ("Bitcoin Halving", "An automatic event every 4 years that cuts the creation of new Bitcoins in half, reducing incoming supply and historically driving price cycles."),
        ("Market Capitalization", "The total dollar value of all existing coins of a cryptocurrency (Current Price multiplied by Circulating Supply)."),
        ("BTC Dominance", "The percentage of the total crypto market cap that belongs to Bitcoin alone (signals whether money is safe in BTC or gambling in altcoins)."),
        ("Fear & Greed Index", "A sentiment speedometer from 0 (Extreme Panic) to 100 (Extreme Euphoria/Bubble Risk)."),
        ("Quantile Uncertainty Cone", "A weather-style forecast showing worst-case (p10), most likely (p50), and best-case (p90) bounds rather than a single guessing number."),
        ("Data Leakage", "An ML error where a model accidentally peeks at future exam answers during training, leading to fake 100% scores that fail in real life."),
        ("Walk-Forward Validation", "The only honest way to test financial ML by training on past months and testing strictly on the next month, rolling forward in time."),
        ("Context Injection (Zero-Hallucination)", "Handing the AI chatbot a fresh sheet of live market numbers right before it answers, ensuring it never fabricates prices.")
    ]

    for term, definition in glossary_items:
        story.append(Paragraph(f"• <b>{term}:</b> {definition}", bullet_style))

    story.append(Spacer(1, 10))

    # ── 6. INTERVIEW Q&A ─────────────────────────────────────────────────────
    story.append(Paragraph("6. Key Technical Interview Q&A (EY GDS Focus)", h1_style))

    qa_list = [
        ("Q1: How did you ensure zero data leakage in time-series modeling?",
         "We enforced chronological splitting (80% train / 20% test), computed all features (EMA, RSI, Volatility) strictly backward using historical lags (t to t-14), validated via TimeSeriesSplit, and ensured the web dashboard only renders inferences on the out-of-sample test set."),
        
        ("Q2: Why use Quantile Regression instead of ARIMA or LSTMs for forecasting?",
         "Financial returns have fat tails and volatility clustering where point forecasts fail because they only predict the conditional mean. Quantile Regression with pinball loss models the full return distribution (p10 floor, p50 median, p90 ceiling), enhanced with exponential decay exp(-t/180) to prevent multi-step error explosion."),
        
        ("Q3: How does the AI chatbot guarantee factual accuracy?",
         "We implemented context-injected grounding: the backend fetches live CoinGecko prices, volume, and Fear & Greed metrics, injecting them directly into the Gemini prompt with negative constraints that forbid guessing missing prices.")
    ]

    for q, a in qa_list:
        story.append(Paragraph(q, q_style))
        story.append(Paragraph(f"<b>Answer:</b> {a}", ans_style))

    # Build Document with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"✅ Generated {PDF_FILENAME} successfully!")


if __name__ == "__main__":
    build_pdf()

# 📈 Indian Stock Advisor & AI Research Terminal

A production-grade, interactive quantitative screening and AI investment research web application for the Indian Stock Market (NSE). Built using **Gradio Blocks**, **yfinance**, **SQLite**, **Plotly**, **Tavily AI Search**, and **Google Gemini 2.5 Flash**.

This application transforms the original Google Colab quantitative research notebook into a deployable software product, preserving 100% of the original algorithmic trading rules and technical indicator calculations while adding real-time market intelligence and an institutional AI research analyst.

---

## 🌟 Key Features

### 1. 📊 Quantitative Screener & Scanner
- **Multi-Source Universe Selector**:
  - **NSE Main Board Equities** (`EQUITY_L.csv`, ~2,630 securities)
  - **NSE SME Platform Equities** (`SME_EQUITY_L.csv`, ~582 securities)
  - **NSE T+0 Settlement Eligible Securities** (`Eligible_T0_Securities_...xlsx`, ~524 securities)
  - **Custom File Upload** (Drag-and-drop CSV or Excel with automated symbol column detection)
  - **Manual Symbol Input** (Comma or space separated ticker entries)
- **High-Performance Ingestion Engine**:
  - Auto-flattens MultiIndex Yahoo Finance historical datasets.
  - Local **SQLite database** caching (`indian_stock_market.sqlite`) to skip duplicate downloads.
  - Interactive live progress indicator with rate limit throttle control (`pause_seconds`).
- **Exact Algorithmic Signal Engine**:
  - **50-Day & 200-Day Simple Moving Averages** (SMA50 & SMA200)
  - **14-Period Wilder's Relative Strength Index** (RSI-14 via exponential moving averages)
  - **20-Session Trailing Performance** (`Return20D_pct`)
  - **Composite Score Matrix** (-3 to +4) and Verdict Classification:
    - `BUY WATCH` (Score $\ge 3$)
    - `HOLD / WAIT` (-1 to +2)
    - `SELL WATCH` (Score $\le -2$)
- **Interactive Results Grid**: Real-time table filtering by signal verdict (`BUY WATCH`, `HOLD / WAIT`, `SELL WATCH`), ticker search, and 1-click CSV export.

### 2. 📈 Interactive Charts & Technical Deep-Dive
- **Multi-Pane Plotly Visualizer**:
  - **Pane 1**: Candlestick price chart with overlaid **SMA50** (Amber) and **SMA200** (Blue) trendlines.
  - **Pane 2**: Volume bar chart colored by bullish/bearish sessions.
  - **Pane 3**: 14-Day Wilder RSI with overbought (70) and oversold (30) boundary lines and neutral zone shading.
- **Signal Breakdown**: Explains the exact algorithmic reasons and risk factors triggered for the selected security.

### 3. 🧠 Gemini 2.5 Flash Institutional AI Advisor
- **Real-Time Web Intelligence (Tavily)**: Fetches breaking company news, quarterly earnings developments, and analyst commentary from financial media (Economic Times, Moneycontrol, Mint).
- **Institutional Investment Memorandum**: Synthesizes algorithmic signals + real-time market catalysts into a structured equity research note:
  - Executive Verdict & Conviction
  - Moving Average Trend Alignment (Golden Cross / Alignment)
  - Momentum & Overbought/Oversold Analysis
  - Actionable Trade Levels: Suggested Entry Zone, Target Price, Invalidation / Stop-Loss Level
  - Tailored answers to user analytical questions (e.g. swing trade duration, risk mitigation).

### 4. 📁 Official Eligible Securities Universe Browser
- Direct interactive viewer and search engine for the official NSE eligible security documents:
  - `EQUITY_L.csv`
  - `SME_EQUITY_L.csv`
  - `Eligible_T0_Securities_20260930121437.xlsx`
- Search by symbol, company name, series, listing date, or ISIN.

### 5. 🗄️ Database & Export Center
- Inspect database row coverage, date ranges, and download failure logs.
- One-click exports of:
  - `indian_stock_market.sqlite`
  - `indian_stock_daily_prices.csv`
  - `indian_stock_scan_results.csv`
  - `indian_stock_download_failures.csv`
- Safe database reset maintenance tools.

### 6. ⚙️ Settings & Diagnostic Suite
- Test connectivity for all 4 external APIs:
  - **Finnhub API**
  - **Twelve Data API**
  - **Tavily AI Search API**
  - **Google Gemini API** (`gemini-2.5-flash`)

---

## 📐 Project Architecture

```
ai for finance/
│
├── app.py                     # Main Gradio application entry point
├── requirements.txt           # Production package dependencies
├── README.md                  # Complete architectural & deployment documentation
├── .env.example               # Template for environment configuration
├── .env                       # Local environment variables & API keys
│
├── backend/                   # Modular backend engine
│   ├── __init__.py
│   ├── config.py              # Environment configuration & file paths
│   ├── database.py            # SQLite database schema, connections & queries
│   ├── data_loader.py         # Universe loaders (Main, SME, T0), file parsers & yfinance downloader
│   ├── technical_analysis.py  # 100% preserved Colab mathematical indicators & scoring algorithm
│   ├── external_apis.py       # Finnhub, Twelve Data & Tavily search integrations
│   ├── ai_advisor.py          # Gemini 2.5 Flash institutional research synthesis
│   └── visualizer.py          # Interactive Plotly candlestick & RSI charting
│
├── assets/                    # Presentation assets
│   └── custom.css             # Modern fintech styling & responsive layout
│
├── tests/                     # Automated test suite
│   ├── __init__.py
│   └── test_components.py     # Unit and integration test suite
│
├── EQUITY_L.csv               # Official NSE Main Board Equity Document
├── SME_EQUITY_L.csv           # Official NSE SME Platform Equity Document
└── Eligible_T0_Securities_... # Official NSE T+0 Settlement Eligible Securities Document
```

---

## 🧮 Original Notebook Mathematical Formulas Preserved

The technical scoring engine in `backend/technical_analysis.py` preserves the exact mathematical logic from Cell 12 of the original notebook:

### 1. Base Price
$$\text{Base} = \begin{cases} \text{Adj Close} & \text{if not null} \\ \text{Close} & \text{otherwise} \end{cases}$$

### 2. Moving Averages
$$\text{SMA}_{50} = \frac{1}{50}\sum_{i=0}^{49} \text{Base}_{t-i}, \quad \text{SMA}_{200} = \frac{1}{200}\sum_{i=0}^{199} \text{Base}_{t-i}$$

### 3. Wilder's 14-Period RSI
$$\Delta = \text{Base}_t - \text{Base}_{t-1}$$
$$\text{Avg Gain} = \text{EMA}(\max(\Delta, 0), \alpha = \frac{1}{14})$$
$$\text{Avg Loss} = \text{EMA}(\max(-\Delta, 0), \alpha = \frac{1}{14})$$
$$\text{RSI}_{14} = 100 - \frac{100}{1 + \frac{\text{Avg Gain}}{\text{Avg Loss}}}$$

### 4. 20-Session Percentage Return
$$\text{Return20D\_pct} = \left(\frac{\text{Base}_t - \text{Base}_{t-20}}{\text{Base}_{t-20}}\right) \times 100$$

### 5. Scoring Matrix
| Condition | Score Impact | Tag |
|---|---|---|
| $\text{Price} > \text{SMA}_{50} > \text{SMA}_{200}$ | $+2$ | Bullish Reason |
| $\text{Price} < \text{SMA}_{50} < \text{SMA}_{200}$ | $-2$ | Bearish Risk |
| $\text{SMA}_{50} > \text{SMA}_{200}$ (Golden Cross) | $+1$ | Bullish Reason |
| $\text{SMA}_{50} < \text{SMA}_{200}$ (Death Cross) | $-1$ | Bearish Risk |
| $40 \le \text{RSI}_{14} \le 65$ (Moderate Bullish) | $+1$ | Bullish Reason |
| $\text{RSI}_{14} > 70$ (Overbought) | $-1$ | Bearish Risk |
| $\text{RSI}_{14} < 30$ (Oversold) | $0$ | Bearish Risk flagged |
| $\text{Return20D\_pct} > 0$ | $+1$ | Bullish Reason |
| $\text{Return20D\_pct} \le 0$ | $-1$ | Bearish Risk |

**Verdict Rule**:
- **BUY WATCH**: Score $\ge 3$
- **SELL WATCH**: Score $\le -2$
- **HOLD / WAIT**: Otherwise

---

## 🚀 Local Installation & Execution

### Prerequisites
- Python 3.10+ (Tested on Python 3.11, 3.12, 3.13)
- Git

### 1. Clone or Navigate to Directory
```bash
cd "c:\Users\shaik\OneDrive\Desktop\ai for finance"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Verify your `.env` file contains your API keys:
```ini
FINNHUB_API_KEY=your_finnhub_api_key
TWELVE_DATA_API_KEY=your_twelve_data_api_key
TAVILY_API_KEY=your_tavily_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### 4. Run the Test Suite
```bash
python -m unittest discover tests
```

### 5. Launch the Web Application
```bash
python app.py
```
Open your browser at: `http://localhost:7860`

---

## 🤗 Deployment to Hugging Face Spaces

This repository is pre-configured for direct deployment on **Hugging Face Spaces**.

### Step 1: Create a New Space
1. Log in to [Hugging Face](https://huggingface.co/).
2. Click **New Space** (`https://huggingface.co/new-space`).
3. Set:
   - **Space Name**: `indian-stock-advisor`
   - **License**: `mit` or `apache-2.0`
   - **Space SDK**: **Gradio**
   - **Space Hardware**: Free CPU (2 vCPU, 16 GB RAM) is sufficient.

### Step 2: Set Environment Secrets
Under **Settings** -> **Variables and Secrets** in your Space, add:
- `FINNHUB_API_KEY`: `your_finnhub_api_key`
- `TWELVE_DATA_API_KEY`: `your_twelve_data_api_key`
- `TAVILY_API_KEY`: `your_tavily_api_key`
- `GEMINI_API_KEY`: `your_gemini_api_key`

### Step 3: Push Code to Space Repository
```bash
git init
git remote add space https://huggingface.co/spaces/<YOUR_USERNAME>/indian-stock-advisor
git add .
git commit -m "Deploy Indian Stock Advisor to Hugging Face Spaces"
git push space main --force
```

Hugging Face Spaces will automatically detect `app.py`, install `requirements.txt`, and build the interactive web app in seconds.

---

## 📝 Modifications Made to Original Notebook

| Original Colab Notebook Feature | New Web Application Implementation | Reason & Improvement |
|---|---|---|
| `%pip install yfinance pandas ...` in code cell | Structured `requirements.txt` | Standardized package management for local and HF Spaces deployment. |
| Hardcoded path `/content/EQUITY_L.csv` | Dynamic `backend/config.py` resolving workspace and data paths | Eliminates hardcoded Colab `/content/` paths; works cross-platform. |
| 3 manual `files.upload()` cells | Integrated **Universe Selector** (Main Board, SME Board, T+0 Eligible) + Gradio File Upload | Eliminates interactive cell blocking; provides one-click universe selection. |
| `drive.mount('/content/drive')` | Local SQLite database + Gradio file export downloads | Google Drive mount does not work outside Colab; replaced with portable database and download buttons. |
| Console `print()` and `display()` | Interactive Gradio DataFrames with column sorting, search and signal filtering | Replaces static Jupyter prints with responsive interactive grids. |
| `google.colab.sheets.InteractiveSheet` | Native Gradio DataFrame component | Colab Sheets is proprietary to Google Colab; replaced with native web tables. |
| `files.download()` calls | Gradio `gr.File` export components for SQLite and CSVs | Enables browser downloads on any server/cloud host. |
| Single-thread linear loop | Multi-tab UI with non-blocking callbacks, live progress bar, and thread-safe SQLite connection | Prevents UI freezing during long-running batch ingestion. |
| No visualization (text table only) | Multi-pane interactive **Plotly** candlestick, SMA overlays, volume and RSI chart | Provides institutional-grade technical charting for visual verification. |
| No fundamental context or AI | Integrated **Tavily AI Search** and **Google Gemini 2.5 Flash** | Fuses pure quantitative numbers with live catalysts to deliver complete research notes. |

---

## ⚠️ Features Not Migrated & Rationale

1. **`google.colab.files.upload()` and `files.download()`**:
   - *Reason*: Google Colab's JavaScript injection bridge is exclusive to Colab notebooks.
   - *Alternative*: Implemented native Gradio `gr.File` drag-and-drop upload and download components.
2. **`google.colab.drive.mount()`**:
   - *Reason*: Google Drive FUSE mounting requires an active Colab virtual machine and Google OAuth.
   - *Alternative*: SQLite database is stored locally in the application working directory and can be downloaded or backed up anytime via the Database Export tab.
3. **`google.colab.sheets.InteractiveSheet`**:
   - *Reason*: Proprietary Colab extension.
   - *Alternative*: Standardized interactive Gradio DataFrame with filtering, selection, and sorting.

---

## 🧪 Testing Results & Verification

- **Automated Unit Tests**: All 7 tests in `tests/test_components.py` passing:
  - Security documents loading & parsing: `EQUITY_L` (2,630 symbols), `SME_EQUITY_L` (582 symbols), `Eligible_T0` (524 symbols).
  - Mathematical indicator calculation accuracy (SMA50, SMA200, Wilder's RSI-14, Return20D).
  - Scoring matrix logic and decision classification (`BUY WATCH`, `HOLD / WAIT`, `SELL WATCH`).
  - Table filtering and symbol search.
  - Interactive Plotly multi-pane chart generation.
  - Database persistence and coverage queries.
- **External API Connectivity Verified**:
  - **Finnhub**: Real-time quotes tested (HTTP 200).
  - **Twelve Data**: Tested with US/NSE endpoints (HTTP 200).
  - **Tavily Search**: Real-time NSE financial news search verified (HTTP 200).
  - **Google Gemini**: Model `gemini-2.5-flash` verified generating institutional investment memorandums (HTTP 200).


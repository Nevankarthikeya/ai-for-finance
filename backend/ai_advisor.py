import json
from typing import Dict, Any, Optional
import requests

from backend.config import GEMINI_API_KEY, GEMINI_MODEL

def check_gemini_health(api_key: Optional[str] = None) -> Dict[str, Any]:
    """Test connection to Google Gemini API."""
    key = api_key or GEMINI_API_KEY
    if not key:
        return {"status": "error", "message": "No Gemini API key provided."}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}"
    try:
        payload = {
            "contents": [{"parts": [{"text": "Reply with 'Gemini Online' only."}]}],
            "generationConfig": {"maxOutputTokens": 10}
        }
        r = requests.post(url, json=payload, timeout=8)
        if r.status_code == 200:
            return {"status": "ok", "message": f"Gemini API ({GEMINI_MODEL}) Connected Successfully!"}
        return {"status": "error", "message": f"Gemini HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"status": "error", "message": f"Gemini Connection Error: {str(e)}"}

def generate_ai_stock_report(
    tech_data: Dict[str, Any],
    live_quote: Optional[Dict[str, Any]] = None,
    news_data: Optional[Dict[str, Any]] = None,
    user_query: str = "",
    api_key: Optional[str] = None
) -> str:
    """
    Generate an in-depth institutional research report using Google Gemini 2.5 Flash.
    Fuses quantitative algorithmic indicators with real-time web intelligence.
    """
    key = api_key or GEMINI_API_KEY
    if not key:
        return "⚠️ Gemini API key is missing. Please configure it in the Settings tab or .env file."

    symbol = tech_data.get("symbol", "UNKNOWN")
    date = tech_data.get("date", "N/A")
    close = tech_data.get("close", "N/A")
    rsi = tech_data.get("RSI14", "N/A")
    sma50 = tech_data.get("SMA50", "N/A")
    sma200 = tech_data.get("SMA200", "N/A")
    ret20 = tech_data.get("Return20D_pct", "N/A")
    score = tech_data.get("score", 0)
    decision = tech_data.get("decision", "HOLD / WAIT")
    reasons = tech_data.get("reasons", "None")
    risks = tech_data.get("risks", "None")

    news_text = "No real-time news available."
    if news_data:
        ans = news_data.get("answer", "")
        items = news_data.get("results", [])
        snippets = []
        if ans:
            snippets.append(f"Summary: {ans}")
        for item in items[:4]:
            t = item.get("title", "")
            c = item.get("content", "")
            snippets.append(f"- {t}: {c}")
        if snippets:
            news_text = "\n".join(snippets)

    prompt = f"""You are a Chartered Senior Quantitative Equity Analyst and Portfolio Manager specializing in the Indian Stock Market (NSE).
Provide a rigorous, data-driven investment memorandum for **{symbol}**.

### 1. Algorithmic Quantitative Metrics:
- **Symbol**: {symbol}
- **As of Date**: {date}
- **Latest Close Price**: ₹{close}
- **Decision Verdict**: {decision} (Score: {score})
- **50-Day Moving Average (SMA50)**: ₹{sma50}
- **200-Day Moving Average (SMA200)**: ₹{sma200}
- **14-Day RSI (Wilder's)**: {rsi}
- **20-Session Trailing Return**: {ret20}%
- **Bullish Factors / Algorithmic Reasons**: {reasons}
- **Bearish Factors / Identified Risks**: {risks}

### 2. Live Web Market Intelligence & News (from Tavily):
{news_text}

### 3. User Specific Question (if provided):
{user_query if user_query else "Provide a comprehensive 360-degree tactical analysis for a 2 to 8 week swing/positional timeframe."}

---
### Instructions:
Format your response with clear, elegant GitHub-style Markdown:
1. **Executive Summary & Verdict**: Bold recommendation ({decision}) with high-conviction rationale.
2. **Technical Alignment**: Analyze the interaction between Close, SMA50, and SMA200 (Golden Cross / Death Cross / Alignment), RSI momentum zone, and 20-day trend.
3. **Fundamental & Market Catalyst Synthesis**: Correlate technical signals with recent news and Indian market conditions.
4. **Actionable Trading Levels**:
   - Suggested Entry Zone (₹)
   - Take Profit / Upside Target (₹)
   - Critical Stop-Loss / Invalidation Level (₹)
   - Risk/Reward Ratio
5. **Key Vulnerabilities & Hedging Strategy**: Address specific risks flagged by the algorithm.
6. **Direct Answer to User's Query** (if provided).

Keep the tone professional, concise, authoritative, and actionable. Avoid generic fluff.
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2048
        }
    }

    try:
        r = requests.post(url, json=payload, timeout=25)
        if r.status_code == 200:
            res_json = r.json()
            candidates = res_json.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "No response generated by model.")
            return "Unable to parse model response."
        else:
            return f"⚠️ Gemini API Error (HTTP {r.status_code}): {r.text[:300]}"
    except Exception as e:
        return f"⚠️ Connection failed while contacting Gemini API: {str(e)}"


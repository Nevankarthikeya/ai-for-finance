import os
from typing import Dict, Any, List, Optional
import requests
from backend.config import FINNHUB_API_KEY, TWELVE_DATA_API_KEY, TAVILY_API_KEY

def check_finnhub_health(api_key: Optional[str] = None) -> Dict[str, Any]:
    """Test connection to Finnhub API."""
    key = api_key or FINNHUB_API_KEY
    if not key:
        return {"status": "error", "message": "No Finnhub API key provided."}
    try:
        r = requests.get(f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={key}", timeout=6)
        if r.status_code == 200:
            return {"status": "ok", "message": "Finnhub API Connected Successfully!"}
        return {"status": "error", "message": f"Finnhub HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"status": "error", "message": f"Finnhub Connection Error: {str(e)}"}

def get_finnhub_quote(symbol: str, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetch live quote from Finnhub."""
    key = api_key or FINNHUB_API_KEY
    if not key:
        return None
    clean_sym = symbol.strip().upper()
    try:
        # Try Indian suffix or bare symbol
        for s in [clean_sym, f"{clean_sym}.NS"]:
            r = requests.get(f"https://finnhub.io/api/v1/quote?symbol={s}&token={key}", timeout=6)
            if r.status_code == 200:
                data = r.json()
                if data.get("c", 0) > 0:
                    return {
                        "current_price": data.get("c"),
                        "change": data.get("d"),
                        "percent_change": data.get("dp"),
                        "high": data.get("h"),
                        "low": data.get("l"),
                        "open": data.get("o"),
                        "previous_close": data.get("pc"),
                        "timestamp": data.get("t")
                    }
        return None
    except Exception:
        return None

def get_finnhub_profile(symbol: str, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetch company profile from Finnhub."""
    key = api_key or FINNHUB_API_KEY
    if not key:
        return None
    clean_sym = symbol.strip().upper()
    try:
        for s in [clean_sym, f"{clean_sym}.NS"]:
            r = requests.get(f"https://finnhub.io/api/v1/stock/profile2?symbol={s}&token={key}", timeout=6)
            if r.status_code == 200 and r.json():
                return r.json()
        return None
    except Exception:
        return None

def check_twelve_data_health(api_key: Optional[str] = None) -> Dict[str, Any]:
    """Test connection to Twelve Data API."""
    key = api_key or TWELVE_DATA_API_KEY
    if not key:
        return {"status": "error", "message": "No Twelve Data API key provided."}
    try:
        r = requests.get(f"https://api.twelvedata.com/quote?symbol=AAPL&apikey={key}", timeout=6)
        if r.status_code == 200:
            data = r.json()
            if "status" in data and data["status"] == "error":
                return {"status": "error", "message": f"Twelve Data error: {data.get('message')}"}
            return {"status": "ok", "message": "Twelve Data API Connected Successfully!"}
        return {"status": "error", "message": f"Twelve Data HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"status": "error", "message": f"Twelve Data Connection Error: {str(e)}"}

def get_twelve_data_quote(symbol: str, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetch quote from Twelve Data."""
    key = api_key or TWELVE_DATA_API_KEY
    if not key:
        return None
    clean_sym = symbol.strip().upper()
    try:
        for params in [
            {"symbol": clean_sym, "exchange": "NSE", "apikey": key},
            {"symbol": f"{clean_sym}:NSE", "apikey": key},
            {"symbol": clean_sym, "apikey": key}
        ]:
            r = requests.get("https://api.twelvedata.com/quote", params=params, timeout=6)
            if r.status_code == 200:
                data = r.json()
                if "close" in data and data.get("status") != "error":
                    return {
                        "name": data.get("name"),
                        "exchange": data.get("exchange"),
                        "currency": data.get("currency"),
                        "open": data.get("open"),
                        "high": data.get("high"),
                        "low": data.get("low"),
                        "close": data.get("close"),
                        "change": data.get("change"),
                        "percent_change": data.get("percent_change"),
                        "volume": data.get("volume"),
                        "52w_high": data.get("fifty_two_week", {}).get("high"),
                        "52w_low": data.get("fifty_two_week", {}).get("low")
                    }
        return None
    except Exception:
        return None

def check_tavily_health(api_key: Optional[str] = None) -> Dict[str, Any]:
    """Test connection to Tavily Search API."""
    key = api_key or TAVILY_API_KEY
    if not key:
        return {"status": "error", "message": "No Tavily API key provided."}
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": key, "query": "NSE Indian market news", "max_results": 1},
            timeout=6
        )
        if r.status_code == 200:
            return {"status": "ok", "message": "Tavily Search API Connected Successfully!"}
        return {"status": "error", "message": f"Tavily HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"status": "error", "message": f"Tavily Connection Error: {str(e)}"}

def search_stock_news(symbol: str, company_name: str = "", api_key: Optional[str] = None, max_results: int = 5) -> Dict[str, Any]:
    """Search latest financial news and catalysts for a stock via Tavily."""
    key = api_key or TAVILY_API_KEY
    if not key:
        return {"answer": "", "results": [], "error": "No Tavily API key configured."}

    query_term = f"{symbol} ({company_name})" if company_name else symbol
    query = f"{query_term} NSE stock latest financial news quarterly earnings share price target India"

    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": key,
                "query": query,
                "search_depth": "basic",
                "include_answer": True,
                "max_results": max_results
            },
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            return {
                "answer": data.get("answer", ""),
                "results": data.get("results", []),
                "error": ""
            }
        return {"answer": "", "results": [], "error": f"Tavily error {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"answer": "", "results": [], "error": str(e)}


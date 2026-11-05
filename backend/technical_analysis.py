from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

def compute_indicator_series(g: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate full technical indicator series for charting and analysis.
    Preserves exact formula implementations from original notebook:
    - Base price (adj_close or close)
    - 50-day Simple Moving Average (SMA50)
    - 200-day Simple Moving Average (SMA200)
    - 14-day Wilder's RSI (RSI14)
    - 20-session return percentage (Return20D_pct)
    """
    g = g.sort_values("date").copy()
    base = g["adj_close"].where(g["adj_close"].notna(), g["close"]).astype(float)
    g["base_price"] = base
    g["SMA50"] = base.rolling(50, min_periods=50).mean()
    g["SMA200"] = base.rolling(200, min_periods=200).mean()
    
    d = base.diff()
    ag = d.clip(lower=0).ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    al = (-d.clip(upper=0)).ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    g["RSI14"] = 100 - 100 / (1 + ag / al.replace(0, np.nan))
    g["Return20D_pct"] = base.pct_change(20) * 100
    return g

def analyze_group(g: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Analyze historical price group for a single symbol.
    Preserves 100% of the original notebook algorithm, scoring rules, and decision thresholds.
    """
    g_calc = compute_indicator_series(g)
    base = g_calc["base_price"]
    valid = g_calc.dropna(subset=["RSI14"])
    if valid.empty:
        return None

    r = valid.iloc[-1]
    score = 0
    reasons = []
    risks = []

    # 1. Trend Analysis: Price vs SMA50 vs SMA200
    if pd.notna(r["SMA200"]):
        current_price = base.loc[r.name]
        if current_price > r["SMA50"] > r["SMA200"]:
            score += 2
            reasons.append("price > SMA50 > SMA200")
        elif current_price < r["SMA50"] < r["SMA200"]:
            score -= 2
            risks.append("price < SMA50 < SMA200")
        elif r["SMA50"] > r["SMA200"]:
            score += 1
            reasons.append("SMA50 > SMA200")
        else:
            score -= 1
            risks.append("SMA50 < SMA200")
    else:
        risks.append("insufficient 200-day history")

    # 2. Momentum Analysis: 14-day RSI
    if 40 <= r["RSI14"] <= 65:
        score += 1
        reasons.append("moderate RSI")
    elif r["RSI14"] > 70:
        score -= 1
        risks.append("RSI above 70")
    elif r["RSI14"] < 30:
        risks.append("RSI below 30")

    # 3. Short-Term Performance: 20-day return %
    if pd.notna(r["Return20D_pct"]):
        if r["Return20D_pct"] > 0:
            score += 1
            reasons.append("positive 20-session return")
        else:
            score -= 1
            risks.append("negative 20-session return")

    # 4. Final Decision Rule
    if score >= 3:
        decision = "BUY WATCH"
    elif score <= -2:
        decision = "SELL WATCH"
    else:
        decision = "HOLD / WAIT"

    return {
        "symbol": str(g["symbol"].iloc[-1]),
        "date": str(r["date"]),
        "close": round(float(r["close"]), 2) if pd.notna(r["close"]) else None,
        "RSI14": round(float(r["RSI14"]), 2) if pd.notna(r["RSI14"]) else None,
        "SMA50": round(float(r["SMA50"]), 2) if pd.notna(r["SMA50"]) else None,
        "SMA200": round(float(r["SMA200"]), 2) if pd.notna(r["SMA200"]) else None,
        "Return20D_pct": round(float(r["Return20D_pct"]), 2) if pd.notna(r["Return20D_pct"]) else None,
        "score": int(score),
        "decision": decision,
        "reasons": "; ".join(reasons),
        "risks": "; ".join(risks)
    }

def scan_all_symbols(all_data: pd.DataFrame) -> pd.DataFrame:
    """
    Iterate over all symbols in the dataset, compute scores, and return ranked scan DataFrame.
    """
    if all_data.empty:
        return pd.DataFrame()

    results = []
    for _, group in all_data.groupby("symbol"):
        res = analyze_group(group)
        if res:
            results.append(res)

    if not results:
        return pd.DataFrame()

    scan_df = pd.DataFrame(results)
    scan_df = scan_df.sort_values(["score", "Return20D_pct"], ascending=False).reset_index(drop=True)
    return scan_df


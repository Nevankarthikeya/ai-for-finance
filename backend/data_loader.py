import re
import time
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Callable, Any
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timezone

from backend.config import (
    FILE_EQUITY_L,
    FILE_SME_EQUITY_L,
    FILE_ELIGIBLE_T0,
    DEFAULT_START_DATE,
    DEFAULT_PAUSE_SECONDS,
    DEFAULT_SKIP_EXISTING,
    DB_PATH
)
from backend.database import (
    downloaded_ok,
    save_daily_prices,
    log_download_status
)

def norm(s: Any) -> str:
    """Normalize column header names for fuzzy matching."""
    return re.sub(r"[^a-z0-9]", "", str(s).lower())

def extract_symbols_from_df(df: pd.DataFrame) -> Tuple[List[str], str]:
    """Extract and validate ticker symbols from any DataFrame."""
    cols = {norm(c): c for c in df.columns}
    symbol_col = next(
        (cols[k] for k in ["symbol", "tradingsymbol", "ticker", "securitysymbol"] if k in cols),
        None
    )
    if symbol_col is None:
        raise ValueError(
            f"Cannot identify symbol column. Available columns: {list(df.columns)}"
        )
    raw_symbols = df[symbol_col].astype(str).str.strip().dropna().drop_duplicates().tolist()
    valid_symbols = [
        s for s in raw_symbols
        if re.fullmatch(r"[A-Za-z0-9&._-]+", s) and s.lower() not in ["nan", "none"]
    ]
    return valid_symbols, symbol_col

def load_security_document(doc_type: str) -> Tuple[pd.DataFrame, List[str]]:
    """
    Load predefined security documents or uploaded datasets.
    doc_type: 'equity_l', 'sme_equity_l', 'eligible_t0'
    """
    doc_type = doc_type.lower().strip()
    if doc_type in ["equity_l", "equity", "main"]:
        if not FILE_EQUITY_L.exists():
            raise FileNotFoundError(f"EQUITY_L.csv not found at {FILE_EQUITY_L}")
        df = pd.read_csv(FILE_EQUITY_L)
    elif doc_type in ["sme_equity_l", "sme"]:
        if not FILE_SME_EQUITY_L.exists():
            raise FileNotFoundError(f"SME_EQUITY_L.csv not found at {FILE_SME_EQUITY_L}")
        df = pd.read_csv(FILE_SME_EQUITY_L)
    elif doc_type in ["eligible_t0", "t0", "t+0"]:
        if not FILE_ELIGIBLE_T0.exists():
            raise FileNotFoundError(f"Eligible T0 Excel not found at {FILE_ELIGIBLE_T0}")
        # The T+0 document has headers on row index 2
        df = pd.read_excel(FILE_ELIGIBLE_T0, header=2)
    else:
        raise ValueError(f"Unknown document type: {doc_type}")

    symbols, _ = extract_symbols_from_df(df)
    return df, symbols

def parse_uploaded_file(file_path: str) -> Tuple[pd.DataFrame, List[str]]:
    """Parse user-uploaded CSV or Excel file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Uploaded file does not exist: {file_path}")

    ext = path.suffix.lower()
    if ext == ".csv":
        df = pd.read_csv(path)
    elif ext in [".xlsx", ".xls"]:
        try:
            df = pd.read_excel(path)
            # Check if symbol column is found, otherwise check header=2
            try:
                extract_symbols_from_df(df)
            except ValueError:
                df = pd.read_excel(path, header=2)
        except Exception:
            df = pd.read_excel(path)
    else:
        raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")

    symbols, _ = extract_symbols_from_df(df)
    return df, symbols

def parse_custom_symbols(text: str) -> List[str]:
    """Parse comma, newline, or space separated stock symbols."""
    raw_tokens = re.split(r"[,\s\n]+", text.strip())
    valid_symbols = []
    for token in raw_tokens:
        clean = token.strip().upper()
        if clean.endswith(".NS"):
            clean = clean[:-3]
        if re.fullmatch(r"[A-Za-z0-9&._-]+", clean) and clean.lower() not in ["nan", "none", ""]:
            if clean not in valid_symbols:
                valid_symbols.append(clean)
    return valid_symbols

def fetch_one_stock(
    symbol: str,
    start_date: str = DEFAULT_START_DATE,
    db_path: Optional[Path] = None,
    timeout: int = 25
) -> Tuple[bool, int, str]:
    """
    Download historical prices for one symbol from yfinance and save to database.
    Preserves exact Colab notebook ingestion logic.
    """
    clean_sym = symbol.strip().upper()
    try:
        ticker = f"{clean_sym}.NS"
        hist = yf.download(
            ticker,
            start=start_date,
            auto_adjust=False,
            progress=False,
            threads=False,
            timeout=timeout
        )
        if hist is None or hist.empty:
            raise ValueError(f"No history returned for {ticker}; symbol may be unsupported.")

        # Flatten multi-level columns if returned by yfinance
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)

        hist = hist.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume"
            }
        )

        for c in ["open", "high", "low", "close"]:
            if c not in hist.columns:
                raise ValueError(f"Missing OHLC column '{c}' in returned data: {list(hist.columns)}")

        if "adj_close" not in hist.columns:
            hist["adj_close"] = hist["close"]
        if "volume" not in hist.columns:
            hist["volume"] = np.nan

        hist = hist.reset_index()
        date_col = "Date" if "Date" in hist.columns else hist.columns[0]

        rows = []
        for _, r in hist.iterrows():
            dt = pd.to_datetime(r[date_col]).strftime("%Y-%m-%d")

            def val(k):
                v = r.get(k, np.nan)
                return None if pd.isna(v) else float(v)

            rows.append((
                clean_sym,
                dt,
                val("open"),
                val("high"),
                val("low"),
                val("close"),
                val("adj_close"),
                val("volume")
            ))

        save_daily_prices(rows, db_path)
        log_download_status(clean_sym, "success", len(rows), "", db_path)
        return True, len(rows), ""
    except Exception as e:
        err_msg = str(e)
        log_download_status(clean_sym, "failed", 0, err_msg[:500], db_path)
        return False, 0, err_msg

def run_batch_download(
    symbols: List[str],
    start_date: str = DEFAULT_START_DATE,
    skip_existing: bool = DEFAULT_SKIP_EXISTING,
    pause_seconds: float = DEFAULT_PAUSE_SECONDS,
    db_path: Optional[Path] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Dict[str, Any]:
    """
    Download historical prices for a batch of symbols with progress tracking.
    """
    ok_count = 0
    fail_count = 0
    skipped_count = 0
    total = len(symbols)

    for idx, sym in enumerate(symbols):
        if skip_existing and downloaded_ok(sym, db_path):
            skipped_count += 1
            if progress_callback:
                progress_callback(idx + 1, total, f"Skipped (already exists): {sym}")
            continue

        if progress_callback:
            progress_callback(idx + 1, total, f"Downloading: {sym} ({idx+1}/{total})")

        ok, n_rows, msg = fetch_one_stock(sym, start_date=start_date, db_path=db_path)
        if ok:
            ok_count += 1
        else:
            fail_count += 1

        if pause_seconds > 0 and (idx + 1) < total:
            time.sleep(pause_seconds)

    return {
        "total_queued": total,
        "successful": ok_count,
        "failed": fail_count,
        "skipped": skipped_count
    }


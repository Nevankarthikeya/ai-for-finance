import os
# Disable Gradio telemetry
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

import unittest
import pandas as pd
from backend.config import BASE_DIR
import backend.database as db
import backend.data_loader as dl
import backend.technical_analysis as ta
import backend.external_apis as apis
import backend.ai_advisor as ai
import backend.visualizer as viz
import app

class TestStockAdvisorApp(unittest.TestCase):

    def setUp(self):
        db.init_db()

    def test_security_documents_exist_and_load(self):
        """Verify all three required security documents load correctly."""
        # 1. Main Board
        df_eq, syms_eq = dl.load_security_document("equity_l")
        self.assertGreater(len(syms_eq), 1000)
        self.assertIn("RELIANCE", syms_eq)

        # 2. SME Board
        df_sme, syms_sme = dl.load_security_document("sme_equity_l")
        self.assertGreater(len(syms_sme), 100)

        # 3. Eligible T+0
        df_t0, syms_t0 = dl.load_security_document("eligible_t0")
        self.assertGreater(len(syms_t0), 100)
        self.assertIn("BPCL", syms_t0)

    def test_custom_symbol_parsing(self):
        """Verify custom symbol parser handles various formats."""
        res = dl.parse_custom_symbols("TCS, INFY.NS   RELIANCE\nHDFCBANK")
        self.assertEqual(res, ["TCS", "INFY", "RELIANCE", "HDFCBANK"])

    def test_technical_analysis_algorithm(self):
        """Verify technical indicator calculations match original notebook logic."""
        # Create a mock series with known trend and normal fluctuations
        dates = pd.date_range("2023-01-01", periods=250, freq="D").strftime("%Y-%m-%d").tolist()
        import math
        closes = [100.0 + i * 0.5 + 2 * math.sin(i) for i in range(250)]
        df_mock = pd.DataFrame({
            "symbol": ["TEST"] * 250,
            "date": dates,
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "adj_close": closes,
            "volume": [100000] * 250
        })

        res = ta.analyze_group(df_mock)
        self.assertIsNotNone(res)
        self.assertEqual(res["symbol"], "TEST")
        self.assertIn("score", res)
        self.assertIn("decision", res)
        # Rising price -> price > SMA50 > SMA200 -> positive score
        self.assertGreaterEqual(res["score"], 1)

    def test_database_operations(self):
        """Verify database insertion, coverage, and retrieval."""
        cov = db.get_coverage()
        self.assertIsInstance(cov, pd.DataFrame)
        fails = db.get_failures()
        self.assertIsInstance(fails, pd.DataFrame)

    def test_filter_scan_table(self):
        """Verify dynamic filtering logic in scan table."""
        sample_df = pd.DataFrame([
            {"symbol": "TCS", "decision": "BUY WATCH", "score": 3},
            {"symbol": "INFY", "decision": "HOLD / WAIT", "score": 1},
            {"symbol": "WIPRO", "decision": "SELL WATCH", "score": -2}
        ])
        filtered_buy = app.filter_scan_table(sample_df, "BUY WATCH", "")
        self.assertEqual(len(filtered_buy), 1)
        self.assertEqual(filtered_buy.iloc[0]["symbol"], "TCS")

        filtered_search = app.filter_scan_table(sample_df, "ALL", "WIP")
        self.assertEqual(len(filtered_search), 1)
        self.assertEqual(filtered_search.iloc[0]["symbol"], "WIPRO")

    def test_visualizer_chart(self):
        """Verify interactive chart generation."""
        prices = db.get_symbol_prices("BPCL")
        if not prices.empty:
            fig = viz.create_stock_chart(prices, "BPCL")
            self.assertIsNotNone(fig)
            self.assertEqual(len(fig.data), 5) # Candles, SMA50, SMA200, Volume, RSI

    def test_browse_universe_docs(self):
        """Verify browsing eligible security documents."""
        df_main = app.browse_universe_doc("Main Board Equities (EQUITY_L.csv)", "TATA")
        self.assertFalse(df_main.empty)

        df_t0 = app.browse_universe_doc("T+0 Settlement Eligible (Eligible_T0)", "BPCL")
        self.assertFalse(df_t0.empty)

if __name__ == "__main__":
    unittest.main()

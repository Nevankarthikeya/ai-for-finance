from typing import Optional
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from backend.technical_analysis import compute_indicator_series

def create_stock_chart(df: pd.DataFrame, symbol: str) -> go.Figure:
    """
    Create a professional multi-pane interactive chart for a stock:
    Pane 1: Candlesticks + SMA50 + SMA200
    Pane 2: Volume
    Pane 3: 14-Day RSI with Overbought (70) and Oversold (30) levels
    """
    if df.empty or len(df) < 5:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient historical data to render chart",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#888888")
        )
        fig.update_layout(
            template="plotly_dark",
            height=500,
            paper_bgcolor="#111827",
            plot_bgcolor="#111827"
        )
        return fig

    # Calculate indicator series
    df_calc = compute_indicator_series(df)

    # Subplots layout
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.58, 0.18, 0.24],
        subplot_titles=(
            f"<b>{symbol}</b> — Price & Moving Averages (SMA 50 / 200)",
            "Volume",
            "14-Day RSI (Relative Strength Index)"
        )
    )

    # 1. Candlestick Chart
    fig.add_trace(
        go.Candlestick(
            x=df_calc["date"],
            open=df_calc["open"],
            high=df_calc["high"],
            low=df_calc["low"],
            close=df_calc["close"],
            name="OHLC",
            increasing_line_color="#10b981", # Emerald
            decreasing_line_color="#ef4444"  # Rose
        ),
        row=1, col=1
    )

    # 2. SMA50 Overlay
    fig.add_trace(
        go.Scatter(
            x=df_calc["date"],
            y=df_calc["SMA50"],
            name="SMA 50",
            line=dict(color="#f59e0b", width=1.8), # Amber
            mode="lines"
        ),
        row=1, col=1
    )

    # 3. SMA200 Overlay
    fig.add_trace(
        go.Scatter(
            x=df_calc["date"],
            y=df_calc["SMA200"],
            name="SMA 200",
            line=dict(color="#3b82f6", width=2.0), # Blue
            mode="lines"
        ),
        row=1, col=1
    )

    # 4. Volume Bars
    vol_colors = [
        "#10b981" if c >= o else "#ef4444"
        for c, o in zip(df_calc["close"], df_calc["open"])
    ]
    fig.add_trace(
        go.Bar(
            x=df_calc["date"],
            y=df_calc["volume"],
            name="Volume",
            marker_color=vol_colors,
            opacity=0.7
        ),
        row=2, col=1
    )

    # 5. RSI(14) Line
    fig.add_trace(
        go.Scatter(
            x=df_calc["date"],
            y=df_calc["RSI14"],
            name="RSI 14",
            line=dict(color="#8b5cf6", width=1.8), # Violet
            mode="lines"
        ),
        row=3, col=1
    )

    # Overbought and Oversold RSI reference lines
    fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", line_width=1.2, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#10b981", line_width=1.2, row=3, col=1)
    fig.add_hrect(y0=30, y1=70, fillcolor="#8b5cf6", opacity=0.08, line_width=0, row=3, col=1)

    # Aesthetic Layout
    fig.update_layout(
        template="plotly_dark",
        height=720,
        margin=dict(l=50, r=40, t=50, b=40),
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11)
        ),
        xaxis_rangeslider_visible=False,
        hovermode="x unified"
    )

    fig.update_xaxes(
        gridcolor="#1e293b",
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikethickness=1,
        spikecolor="#64748b"
    )
    fig.update_yaxes(
        gridcolor="#1e293b",
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikethickness=1,
        spikecolor="#64748b"
    )

    fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI (14)", range=[0, 100], row=3, col=1)

    return fig


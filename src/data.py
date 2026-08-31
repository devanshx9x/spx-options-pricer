"""
Market data helpers: price history, realized volatility, option chain, risk-free rate.
"""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yfinance as yf


def get_price_history(symbol, years_back=2):
    """Fetch daily close price history for `symbol` going back `years_back` years."""
    if years_back <= 0:
        raise ValueError("years_back must be positive.")

    end = date.today()
    start = (pd.Timestamp(end) - pd.DateOffset(years=years_back)).date()
    ticker = yf.Ticker(symbol)
    # yfinance treats `end` as exclusive, so request through tomorrow to include
    # today's daily bar whenever it is available.
    df = ticker.history(start=start, end=end + timedelta(days=1), interval="1d")
    if df.empty:
        raise ValueError(f"No price history returned for {symbol}")
    return df, ticker


def annual_vol(df, window_days=None):
    """
    Annualized volatility from daily log returns.

    window_days : if given, only use the most recent N trading days.
                  Recommended for near-dated options so the vol estimate
                  reflects current conditions rather than the full history.
    """
    if window_days is not None and window_days < 2:
        raise ValueError("window_days must be at least 2 to estimate volatility.")

    closes = df["Close"].dropna()
    if window_days is not None:
        closes = closes.tail(window_days + 1)

    if len(closes) < 3:
        raise ValueError("At least three valid closing prices are required to estimate volatility.")
    if (closes <= 0).any():
        raise ValueError("Closing prices must be positive to estimate log-return volatility.")

    log_returns = np.log(closes / closes.shift(1)).dropna()
    if len(log_returns) < 2 or not np.isfinite(log_returns).all():
        raise ValueError("At least two finite log returns are required to estimate volatility.")

    vol = float(log_returns.std(ddof=1) * np.sqrt(252))
    if not np.isfinite(vol) or vol <= 0:
        raise ValueError("Estimated volatility must be finite and positive.")
    return vol


def get_option_chain(ticker, expiry_index=1):
    """Return (expiry_date, calls_df, puts_df) for the given expiry index."""
    expiries = ticker.options
    if expiry_index < 0 or len(expiries) <= expiry_index:
        raise ValueError(
            f"Requested expiry index {expiry_index}, but only {len(expiries)} "
            f"expiries are available for this ticker."
        )
    expiry = expiries[expiry_index]
    chain = ticker.option_chain(expiry)
    return expiry, chain.calls, chain.puts


def time_to_expiry(expiry_date_str, now=None):
    """Years until the 4:00 PM New York close on the expiry date (YYYY-MM-DD)."""
    market_tz = ZoneInfo("America/New_York")
    expiry_date = pd.to_datetime(expiry_date_str).date()
    expiry_dt = datetime.combine(expiry_date, time(16, 0), tzinfo=market_tz)

    if now is None:
        now = datetime.now(market_tz)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=market_tz)
    else:
        now = now.astimezone(market_tz)

    seconds = (expiry_dt - now).total_seconds()
    if seconds <= 0:
        raise ValueError("Expiry time has passed.")
    return seconds / (365 * 24 * 60 * 60)


def get_risk_free_rate():
    """
    10Y US Treasury yield, pulled live from ^TNX (CBOE index, quoted x10).
    Falls back to a fixed estimate if the fetch fails.
    """
    try:
        tnx = yf.Ticker("^TNX").history(period="5d")["Close"].dropna()
        return float(tnx.iloc[-1]) / 100
    except Exception:
        return 0.0424  # fallback only — update if this ever actually fires

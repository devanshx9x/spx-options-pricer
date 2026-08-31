"""
Entry point: prices an S&P 500 options chain against Black-Scholes theoretical
values and plots the Greeks.

Uses SPY (the S&P 500 ETF) rather than the ^GSPC index directly, since index
tickers generally don't carry a tradable options chain in yfinance — SPY's
chain is liquid and closely tracks the index (roughly 1/10th the price).
"""

import argparse

import pandas as pd

from src.data import (
    annual_vol,
    get_option_chain,
    get_price_history,
    get_risk_free_rate,
    time_to_expiry,
)
from src.pricing import calculate_greeks, euro_vanilla
from src.plotting import plot_greeks_dashboard, plot_theoretical_vs_actual


def main(symbol="SPY", expiry_index=1, vol_window=60, dividend_yield=0.013):
    df, ticker = get_price_history(symbol)
    vol = annual_vol(df, window_days=vol_window)
    r = get_risk_free_rate()
    S = df["Close"].iloc[-1]

    expiry, calls, puts = get_option_chain(ticker, expiry_index=expiry_index)
    T = time_to_expiry(expiry)

    print(
        f"{symbol} | Spot: {S:.2f} | Vol ({vol_window}d): {vol:.2%} | "
        f"Rate: {r:.2%} | Expiry: {expiry} | T: {T:.4f}y"
    )

    # --- Theoretical vs actual calls ---
    th_call = {
        K: euro_vanilla(S, K, T, r, vol, q=dividend_yield, option="call")
        for K in calls["strike"]
    }
    call_df = pd.DataFrame.from_dict(th_call, orient="index", columns=["theoretical"])
    call_df["actual"] = calls.set_index("strike")["lastPrice"]
    plot_theoretical_vs_actual(call_df, f"{symbol} Calls: Theoretical vs Actual", "Price")

    # --- Theoretical vs actual puts ---
    th_put = {
        K: euro_vanilla(S, K, T, r, vol, q=dividend_yield, option="put")
        for K in puts["strike"]
    }
    put_df = pd.DataFrame.from_dict(th_put, orient="index", columns=["theoretical"])
    put_df["actual"] = puts.set_index("strike")["lastPrice"]
    plot_theoretical_vs_actual(put_df, f"{symbol} Puts: Theoretical vs Actual", "Price")

    # --- Greeks dashboard (calls) ---
    greeks = {
        K: calculate_greeks(S, K, T, r, vol, q=dividend_yield, option="call")
        for K in calls["strike"]
    }
    greeks_df = pd.DataFrame.from_dict(greeks, orient="index")
    plot_greeks_dashboard(greeks_df, symbol, S, option_label="Call")

    return call_df, put_df, greeks_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="S&P 500 options pricing & Greeks")
    parser.add_argument("--symbol", default="SPY", help="Ticker to use (default: SPY)")
    parser.add_argument("--expiry-index", type=int, default=1, help="Index into ticker.options")
    parser.add_argument("--vol-window", type=int, default=60, help="Trading days for realized vol")
    parser.add_argument("--dividend-yield", type=float, default=0.013, help="Continuous dividend yield")
    args = parser.parse_args()

    main(args.symbol, args.expiry_index, args.vol_window, args.dividend_yield)

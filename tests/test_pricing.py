import math
import os
import sys
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import data
from src.data import annual_vol, get_option_chain, time_to_expiry
from src.pricing import calculate_greeks, euro_vanilla


def test_call_price_known_value():
    # Reference: S=100, K=100, T=1, r=5%, sigma=20%, q=0 -> call ~= 10.4506
    price = euro_vanilla(S=100, K=100, T=1, r=0.05, sigma=0.2, option="call")
    assert math.isclose(price, 10.4506, abs_tol=0.01)


def test_put_price_known_value():
    # Same inputs -> put ~= 5.5735
    price = euro_vanilla(S=100, K=100, T=1, r=0.05, sigma=0.2, option="put")
    assert math.isclose(price, 5.5735, abs_tol=0.01)


def test_put_call_parity():
    call = euro_vanilla(S=100, K=100, T=1, r=0.05, sigma=0.2, option="call")
    put = euro_vanilla(S=100, K=100, T=1, r=0.05, sigma=0.2, option="put")
    lhs = call - put
    rhs = 100 - 100 * math.exp(-0.05 * 1)
    assert math.isclose(lhs, rhs, abs_tol=1e-6)


def test_delta_bounds():
    call_greeks = calculate_greeks(S=100, K=100, T=1, r=0.05, sigma=0.2, option="call")
    put_greeks = calculate_greeks(S=100, K=100, T=1, r=0.05, sigma=0.2, option="put")
    assert 0 <= call_greeks["Delta"] <= 1
    assert -1 <= put_greeks["Delta"] <= 0


def test_invalid_option_type_raises():
    try:
        euro_vanilla(S=100, K=100, T=1, r=0.05, sigma=0.2, option="invalid")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_zero_or_negative_T_raises():
    try:
        euro_vanilla(S=100, K=100, T=0, r=0.05, sigma=0.2, option="call")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_price_history_requests_through_today(monkeypatch):
    class FakeTicker:
        def history(self, **kwargs):
            self.history_kwargs = kwargs
            return pd.DataFrame({"Close": [100.0]})

    ticker = FakeTicker()
    monkeypatch.setattr(data.yf, "Ticker", lambda symbol: ticker)

    data.get_price_history("SPY")

    assert ticker.history_kwargs["end"] == date.today() + timedelta(days=1)


def test_annual_vol_rejects_an_invalid_window():
    prices = pd.DataFrame({"Close": [100.0, 101.0, 102.0]})
    try:
        annual_vol(prices, window_days=0)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_annual_vol_rejects_insufficient_prices():
    prices = pd.DataFrame({"Close": [100.0, 101.0]})
    try:
        annual_vol(prices)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_same_day_expiry_has_time_value_before_market_close():
    new_york = ZoneInfo("America/New_York")
    now = datetime(2026, 9, 4, 12, 0, tzinfo=new_york)

    result = time_to_expiry("2026-09-04", now=now)

    assert math.isclose(result, 4 / (365 * 24), rel_tol=1e-12)


def test_expiry_after_market_close_raises():
    new_york = ZoneInfo("America/New_York")
    now = datetime(2026, 9, 4, 16, 0, tzinfo=new_york)

    try:
        time_to_expiry("2026-09-04", now=now)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_negative_expiry_index_raises():
    class FakeTicker:
        options = ("2026-09-04", "2026-09-11")

        def option_chain(self, expiry):
            return SimpleNamespace(calls=pd.DataFrame(), puts=pd.DataFrame())

    try:
        get_option_chain(FakeTicker(), expiry_index=-1)
        assert False, "Expected ValueError"
    except ValueError:
        pass

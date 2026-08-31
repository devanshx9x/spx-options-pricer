"""
Black-Scholes pricing engine for European options, with a dividend-yield term.

Note: SPY options are American-style, so these theoretical prices will
diverge somewhat from market prices, especially for puts, due to the
early-exercise premium that Black-Scholes does not model. Treat the
theoretical curve as a benchmark, not a "fair value" target.
"""

import numpy as np
from scipy.stats import norm


def euro_vanilla(S, K, T, r, sigma, q=0.0, option="call"):
    """
    Black-Scholes price for a European call or put.

    Parameters
    ----------
    S : float - current spot price
    K : float - strike price
    T : float - time to expiry, in years
    r : float - risk-free rate (annualized, continuous)
    sigma : float - annualized volatility
    q : float - continuous dividend yield (default 0.0)
    option : str - 'call' or 'put'
    """
    if T <= 0 or sigma <= 0:
        raise ValueError("T and sigma must be positive.")

    d1 = (np.log(S / K) + (r - q + sigma**2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option == "call":
        return S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    elif option == "put":
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)
    else:
        raise ValueError("option must be 'call' or 'put'")


def calculate_greeks(S, K, T, r, sigma, q=0.0, option="call"):
    """Black-Scholes Greeks (Delta, Gamma, Theta, Vega, Rho) for a European option."""
    if T <= 0 or sigma <= 0:
        raise ValueError("T and sigma must be positive.")

    d1 = (np.log(S / K) + (r - q + sigma**2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    pdf_d1 = norm.pdf(d1)

    gamma = np.exp(-q * T) * pdf_d1 / (S * sigma * np.sqrt(T))
    vega = S * np.exp(-q * T) * np.sqrt(T) * pdf_d1 / 100  # per 1% change in vol

    if option == "call":
        delta = np.exp(-q * T) * norm.cdf(d1)
        theta = (
            -(S * np.exp(-q * T) * sigma * pdf_d1) / (2 * np.sqrt(T))
            - r * K * np.exp(-r * T) * norm.cdf(d2)
            + q * S * np.exp(-q * T) * norm.cdf(d1)
        ) / 365
        rho = (K * T * np.exp(-r * T) * norm.cdf(d2)) / 100
    elif option == "put":
        delta = np.exp(-q * T) * (norm.cdf(d1) - 1)
        theta = (
            -(S * np.exp(-q * T) * sigma * pdf_d1) / (2 * np.sqrt(T))
            + r * K * np.exp(-r * T) * norm.cdf(-d2)
            - q * S * np.exp(-q * T) * norm.cdf(-d1)
        ) / 365
        rho = (-K * T * np.exp(-r * T) * norm.cdf(-d2)) / 100
    else:
        raise ValueError("option must be 'call' or 'put'")

    return {"Delta": delta, "Gamma": gamma, "Theta": theta, "Vega": vega, "Rho": rho}

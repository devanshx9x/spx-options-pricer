"""Plotting helpers for theoretical-vs-actual prices and the Greeks dashboard."""

import matplotlib.pyplot as plt


def plot_theoretical_vs_actual(df, title, ylabel):
    ax = df.plot(figsize=(10, 6), marker="o", markersize=3)
    ax.set_title(title)
    ax.set_xlabel("Strike")
    ax.set_ylabel(ylabel)
    ax.grid(True)
    plt.tight_layout()
    plt.show()
    return ax


def plot_greeks_dashboard(greeks_df, symbol, spot, option_label="Call"):
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"{symbol} {option_label} Option Greeks Dashboard (Spot: {spot:.2f})", fontsize=16)

    panels = [
        ("Delta", "Directional Risk", "blue", axs[0, 0]),
        ("Gamma", "Delta Sensitivity", "purple", axs[0, 1]),
        ("Theta", "Time Decay - Daily", "red", axs[1, 0]),
        ("Vega", "Volatility Risk", "green", axs[1, 1]),
    ]

    for greek, subtitle, color, ax in panels:
        ax.plot(greeks_df.index, greeks_df[greek], color=color)
        ax.set_title(f"{greek} ({subtitle})")
        ax.axvline(spot, color="black", linestyle="--", label="Spot Price" if greek == "Delta" else None)
        ax.grid(True)

    axs[0, 0].legend()
    plt.tight_layout()
    plt.show()
    return fig

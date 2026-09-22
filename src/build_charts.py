"""Exhibits for the EPC earnings-quality screen. Three charts, no overlap:
accrual ranking, CFO-vs-PAT bridge, and the two-year balance-sheet growth
context that motivates why accruals matter here (a working-capital-heavy
sector scaling up fast)."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCREEN_CSV = ROOT / "data" / "final" / "accrual_screen.csv"
INPUTS_CSV = ROOT / "data" / "final" / "verified_inputs.csv"
OUT = ROOT / "outputs" / "charts"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "figure.dpi": 300,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.5,
})

NAVY = "#1a3a5c"
RUST = "#c0522d"
SAGE = "#5c7a5c"
GREY = "#6b6b6b"


def chart_accrual_ranking(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = [RUST if v > 0 else SAGE for v in df["accrual_ratio"]]
    bars = ax.barh(df["company"], df["accrual_ratio"] * 100, color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Total accrual ratio, FY26 = (PAT − CFO) / Avg. Total Assets, %")
    ax.set_title("FY26 Earnings Quality — Accrual Ratio Ranking\nWorst (most PAT, least cash) at top",
                  fontsize=11, loc="left", weight="bold")
    ax.margins(x=0.18)
    for bar, val in zip(bars, df["accrual_ratio"]):
        ax.text(bar.get_width() + (0.3 if val > 0 else -0.3), bar.get_y() + bar.get_height() / 2,
                 f"{val*100:+.1f}%", va="center", ha="left" if val > 0 else "right", fontsize=9)
    ax.text(0.99, 0.02, "Source: company FY26 annual reports/results filings, reconciled — see reports/methodology_memo.pdf",
             transform=ax.transAxes, fontsize=6.5, color=GREY, ha="right")
    fig.tight_layout()
    fig.savefig(OUT / "01_accrual_ratio_ranking.png", bbox_inches="tight")
    plt.close(fig)


def chart_cfo_vs_pat(df: pd.DataFrame) -> None:
    # L&T's absolute scale (~₹16,000 Cr) dwarfs the other three on one shared
    # axis and makes them unreadable — small multiples, one axis per company,
    # instead of forcing a shared scale that hides the smaller names.
    companies = list(df["company"])
    fig, axes = plt.subplots(1, len(companies), figsize=(10, 4.5), sharey=False)
    for ax, (_, row) in zip(axes, df.iterrows()):
        bars = ax.bar(["PAT", "CFO"], [row["pat"], row["cfo"]], color=[NAVY, SAGE], width=0.6)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_title(row["company"], fontsize=9.5)
        for bar, val in zip(bars, [row["pat"], row["cfo"]]):
            ax.text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + (abs(row["pat"]) * 0.03 if val >= 0 else -abs(row["pat"]) * 0.08),
                     f"{val:,.0f}", ha="center", va="bottom" if val >= 0 else "top", fontsize=7.5)
        ax.tick_params(axis="y", labelsize=7)
        ax.margins(y=0.2)
    axes[0].set_ylabel("₹ Crore, consolidated, FY26")
    fig.suptitle("FY26 Profit vs Operating Cash Flow, by company (independent scales)",
                  fontsize=11, x=0.02, ha="left", weight="bold", y=1.02)
    fig.text(0.99, -0.02, "Source: company FY26 annual reports/results filings, reconciled",
              fontsize=6.5, color=GREY, ha="right")
    fig.tight_layout()
    fig.savefig(OUT / "02_cfo_vs_pat_fy26.png", bbox_inches="tight")
    plt.close(fig)


def chart_balance_sheet_growth(inputs: pd.DataFrame) -> None:
    fy25 = inputs[inputs["fy"] == "FY25"].set_index("company")["total_assets"]
    fy26 = inputs[inputs["fy"] == "FY26"].set_index("company")["total_assets"]
    growth = ((fy26 / fy25 - 1) * 100).sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(growth.index, growth.values, color=NAVY)
    ax.set_ylabel("FY25 → FY26 total assets growth, %")
    ax.set_title("Balance Sheet Growth, FY25 → FY26\nContext: fast asset growth is where accrual quality matters most",
                  fontsize=11, loc="left", weight="bold")
    for bar, val in zip(bars, growth.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, f"{val:+.1f}%",
                 ha="center", fontsize=9)
    ax.text(0.99, 0.02, "Source: company FY25/FY26 balance sheets, reconciled",
             transform=ax.transAxes, fontsize=6.5, color=GREY, ha="right")
    fig.tight_layout()
    fig.savefig(OUT / "03_balance_sheet_growth.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    screen = pd.read_csv(SCREEN_CSV)
    inputs = pd.read_csv(INPUTS_CSV)

    chart_accrual_ranking(screen)
    chart_cfo_vs_pat(screen)
    chart_balance_sheet_growth(inputs)

    print("Charts written to", OUT)
    for f in sorted(OUT.glob("*.png")):
        print(" -", f.name)

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import FIGURES_DIR, bq_path, ensure_reports


sns.set_theme(style="whitegrid")


def plot_bq1_trend(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 4))
    if df.empty:
        ax.set_title("BQ1: No data")
        return fig
    x = df["month_name"].astype(str) + "-" + df["year_num"].astype(str)
    ax.plot(x, df["total_transactions"], marker="o", linewidth=2)
    ax.set_title("BQ1: EV Transaction Volume Over Time")
    ax.set_xlabel("Month")
    ax.set_ylabel("Distinct Transactions")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig


def plot_top_states(df: pd.DataFrame, top_n: int = 10):
    agg = (
        df.groupby("state", dropna=False)["total_transactions"]
        .sum()
        .reset_index()
        .sort_values("total_transactions", ascending=False)
        .head(top_n)
    )
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(data=agg, x="total_transactions", y="state", ax=ax)
    ax.set_title(f"BQ2: Top {top_n} States by EV Activity")
    ax.set_xlabel("Distinct Transactions")
    ax.set_ylabel("State")
    fig.tight_layout()
    return fig


def plot_top_manufacturers(df: pd.DataFrame, top_n: int = 10):
    top = df.head(top_n)
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(data=top, x="manufacturer_revenue", y="manufacturer_name", ax=ax)
    ax.set_title(f"BQ3: Top {top_n} Manufacturers by Revenue")
    ax.set_xlabel("Revenue")
    ax.set_ylabel("Manufacturer")
    fig.tight_layout()
    return fig


def plot_top_models(df: pd.DataFrame, top_n: int = 10):
    top = df.head(top_n)
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(data=top, x="total_transactions", y="model_name", ax=ax)
    ax.set_title(f"BQ4: Top {top_n} Models by Transaction Count")
    ax.set_xlabel("Distinct Transactions")
    ax.set_ylabel("Model")
    fig.tight_layout()
    return fig


def plot_activity_share(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(6, 6))
    if df.empty:
        ax.set_title("BQ5: No data")
        return fig
    ax.pie(
        df["total_transactions"],
        labels=df["activity_type"].fillna("<NULL>"),
        autopct="%1.1f%%",
        startangle=90,
    )
    ax.set_title("BQ5: Activity Share")
    fig.tight_layout()
    return fig


def main() -> None:
    # Create chart images from analysis output.
    bqs = {
        "BQ1": pd.read_csv(bq_path("BQ1")),
        "BQ2": pd.read_csv(bq_path("BQ2")),
        "BQ3": pd.read_csv(bq_path("BQ3")),
        "BQ4": pd.read_csv(bq_path("BQ4")),
        "BQ5": pd.read_csv(bq_path("BQ5")),
    }

    ensure_reports()
    fig1 = plot_bq1_trend(bqs["BQ1"])
    fig1.savefig(FIGURES_DIR / "09_bq1_trend.png", dpi=120, bbox_inches="tight")
    plt.close(fig1)

    fig2 = plot_top_states(bqs["BQ2"], top_n=10)
    fig2.savefig(FIGURES_DIR / "09_bq2_states.png", dpi=120, bbox_inches="tight")
    plt.close(fig2)

    fig3 = plot_top_manufacturers(bqs["BQ3"], top_n=10)
    fig3.savefig(FIGURES_DIR / "09_bq3_manufacturers.png", dpi=120, bbox_inches="tight")
    plt.close(fig3)

    fig4 = plot_top_models(bqs["BQ4"], top_n=10)
    fig4.savefig(FIGURES_DIR / "09_bq4_models.png", dpi=120, bbox_inches="tight")
    plt.close(fig4)

    fig5 = plot_activity_share(bqs["BQ5"])
    fig5.savefig(FIGURES_DIR / "09_bq5_activity_share.png", dpi=120, bbox_inches="tight")
    plt.close(fig5)

    print("Stage 09 complete: Data Visualization")
    print("  - reports/figures/*.png")


if __name__ == "__main__":
    main()

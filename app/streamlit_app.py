from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="IFRS 9 ECL Dashboard", layout="wide")


OUTPUT_DIR = Path("data/output")
ECL_FILE = OUTPUT_DIR / "portfolio_ecl.csv"
STAGE_DIST_FILE = OUTPUT_DIR / "stage_distribution.csv"
SUMMARY_FILE = OUTPUT_DIR / "portfolio_summary.csv"


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not ECL_FILE.exists():
        raise FileNotFoundError(f"Missing file: {ECL_FILE}")
    if not STAGE_DIST_FILE.exists():
        raise FileNotFoundError(f"Missing file: {STAGE_DIST_FILE}")
    if not SUMMARY_FILE.exists():
        raise FileNotFoundError(f"Missing file: {SUMMARY_FILE}")

    ecl = pd.read_csv(ECL_FILE)
    stage_dist = pd.read_csv(STAGE_DIST_FILE)
    summary = pd.read_csv(SUMMARY_FILE)
    return ecl, stage_dist, summary


def main() -> None:
    st.title("IFRS 9 Expected Credit Loss Engine")
    st.caption("Structured, auditable, and forward-looking ECL dashboard")

    ecl_df, stage_dist_df, summary_df = load_data()

    st.sidebar.header("Controls")
    scenario_scale = st.sidebar.slider(
        "Scenario sensitivity multiplier",
        min_value=0.70,
        max_value=1.30,
        value=1.00,
        step=0.01,
    )

    df = ecl_df.copy()
    df["ecl_sensitivity"] = (df["ecl_final"] * scenario_scale).round(2)

    total_ead = df["ead"].sum()
    total_ecl = df["ecl_sensitivity"].sum()
    coverage = total_ecl / total_ead if total_ead > 0 else 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total EAD", f"{total_ead:,.2f}")
    c2.metric("Total ECL (Sensitivity)", f"{total_ecl:,.2f}")
    c3.metric("Coverage Ratio", f"{coverage:.2%}")

    st.subheader("Stage Distribution")
    fig_stage = px.bar(
        stage_dist_df,
        x="stage",
        y="total_ecl",
        text="total_ecl",
        title="Allowance by Stage",
        labels={"stage": "Stage", "total_ecl": "Total ECL"},
    )
    st.plotly_chart(fig_stage, use_container_width=True)

    st.subheader("Top 20 Exposures by ECL")
    top20 = df.nlargest(20, "ecl_sensitivity")[
        ["loan_id", "segment", "product_type", "stage", "ead", "ecl_sensitivity"]
    ]
    fig_top20 = px.bar(
        top20.sort_values("ecl_sensitivity", ascending=True),
        x="ecl_sensitivity",
        y="loan_id",
        color="stage",
        orientation="h",
        title="Top 20 Loans by ECL",
        labels={"ecl_sensitivity": "ECL", "loan_id": "Loan ID"},
    )
    st.plotly_chart(fig_top20, use_container_width=True)

    st.subheader("Drill-down by Segment")
    seg_summary = (
        df.groupby("segment", as_index=False)
        .agg(
            n_loans=("loan_id", "count"),
            total_ead=("ead", "sum"),
            total_ecl=("ecl_sensitivity", "sum"),
        )
        .sort_values("total_ecl", ascending=False)
    )
    seg_summary["coverage_ratio"] = seg_summary["total_ecl"] / seg_summary["total_ead"]

    st.dataframe(seg_summary, use_container_width=True)

    fig_seg = px.pie(
        seg_summary,
        names="segment",
        values="total_ecl",
        title="ECL Share by Segment",
    )
    st.plotly_chart(fig_seg, use_container_width=True)

    st.subheader("Raw Portfolio Sample")
    st.dataframe(
        df[
            [
                "loan_id",
                "segment",
                "product_type",
                "stage",
                "ead",
                "lgd",
                "pd_effective",
                "ecl_final",
                "ecl_sensitivity",
            ]
        ].head(100),
        use_container_width=True,
    )


if __name__ == "__main__":
    main()

from __future__ import annotations

import pandas as pd


DEFAULT_OVERLAY_BY_STAGE = {
    1: 0.00,  # sem ajuste em stage 1
    2: 0.05,  # +5%
    3: 0.10,  # +10%
}


def apply_overlay(
    portfolio: pd.DataFrame,
    overlay_by_stage: dict[int, float] | None = None,
) -> pd.DataFrame:
    if "stage" not in portfolio.columns:
        raise ValueError("Missing required column: stage")
    if "ecl_base" not in portfolio.columns:
        raise ValueError("Missing required column: ecl_base")

    params = overlay_by_stage or DEFAULT_OVERLAY_BY_STAGE

    for stage, pct in params.items():
        if stage not in (1, 2, 3):
            raise ValueError(f"Invalid stage in overlay params: {stage}")
        if pct < -1:
            raise ValueError(f"Overlay percentage too low for stage {stage}: {pct}")

    df = portfolio.copy()
    df["overlay_pct"] = df["stage"].map(params).fillna(0.0)
    df["overlay_amount"] = df["ecl_base"] * df["overlay_pct"]
    df["ecl_final"] = df["ecl_base"] + df["overlay_amount"]

    df["overlay_pct"] = df["overlay_pct"].round(6)
    df["overlay_amount"] = df["overlay_amount"].round(2)
    df["ecl_final"] = df["ecl_final"].round(2)

    return df

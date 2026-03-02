from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


BASE_PD_12M_BY_RATING = {
    "AAA": 0.002,
    "AA": 0.004,
    "A": 0.008,
    "BBB": 0.015,
    "BB": 0.035,
    "B": 0.080,
    "CCC": 0.200,
}

SEGMENT_PD_MULTIPLIER = {
    "Retail": 1.00,
    "SME": 1.20,
    "Corporate": 0.90,
}

STAGE_PD_12M_FLOOR = {
    1: 0.000,
    2: 0.050,
    3: 0.200,
}


def _cap_probability(value: float) -> float:
    return float(min(max(value, 0.0), 1.0))


def _remaining_months(reporting_date: pd.Timestamp, maturity_date: pd.Timestamp) -> int:
    months = int(np.ceil((maturity_date - reporting_date).days / 30))
    return max(months, 1)


def _compute_pd_12m(rating_current: str, segment: str, stage: int) -> float:
    if rating_current not in BASE_PD_12M_BY_RATING:
        raise ValueError(f"Unknown rating_current: {rating_current}")
    if segment not in SEGMENT_PD_MULTIPLIER:
        raise ValueError(f"Unknown segment: {segment}")
    if stage not in STAGE_PD_12M_FLOOR:
        raise ValueError(f"Unknown stage: {stage}")

    pd_base = BASE_PD_12M_BY_RATING[rating_current]
    pd_segment_adj = pd_base * SEGMENT_PD_MULTIPLIER[segment]
    pd_with_floor = max(pd_segment_adj, STAGE_PD_12M_FLOOR[stage])

    return _cap_probability(pd_with_floor)


def _compute_pd_lifetime(pd_12m: float, remaining_months: int) -> float:
    # Aproximação com hazard constante:
    # PD_lifetime = 1 - (1 - PD_12m) ^ anos
    years = max(remaining_months / 12, 1 / 12)
    pd_life = 1.0 - (1.0 - pd_12m) ** years
    return _cap_probability(pd_life)


def apply_pd(portfolio: pd.DataFrame) -> pd.DataFrame:
    required_columns = [
        "rating_current",
        "segment",
        "stage",
        "reporting_date",
        "maturity_date",
    ]
    missing = [c for c in required_columns if c not in portfolio.columns]
    if missing:
        raise ValueError(f"Missing required columns for PD: {missing}")

    df = portfolio.copy()
    df["reporting_date"] = pd.to_datetime(df["reporting_date"])
    df["maturity_date"] = pd.to_datetime(df["maturity_date"])

    df["remaining_months"] = df.apply(
        lambda r: _remaining_months(r["reporting_date"], r["maturity_date"]),
        axis=1,
    )

    df["pd_12m"] = df.apply(
        lambda r: _compute_pd_12m(
            rating_current=str(r["rating_current"]),
            segment=str(r["segment"]),
            stage=int(r["stage"]),
        ),
        axis=1,
    )

    df["pd_lifetime"] = df.apply(
        lambda r: _compute_pd_lifetime(
            pd_12m=float(r["pd_12m"]),
            remaining_months=int(r["remaining_months"]),
        ),
        axis=1,
    )

    df["pd_12m"] = df["pd_12m"].round(6)
    df["pd_lifetime"] = df["pd_lifetime"].round(6)

    return df


def main() -> None:
    input_path = Path("data/output/portfolio_ead.csv")
    output_path = Path("data/output/portfolio_pd.csv")

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    portfolio = pd.read_csv(input_path)
    with_pd = apply_pd(portfolio)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with_pd.to_csv(output_path, index=False)

    print(f"PD portfolio saved to: {output_path}")
    print("PD summary by stage:")
    summary = with_pd.groupby("stage")[["pd_12m", "pd_lifetime"]].mean().round(6)
    print(summary.to_string())


if __name__ == "__main__":
    main()
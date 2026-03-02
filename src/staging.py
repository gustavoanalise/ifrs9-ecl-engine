from __future__ import annotations

from pathlib import Path

import pandas as pd


RATING_SCALE = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]
RATING_RANK = {rating: idx for idx, rating in enumerate(RATING_SCALE)}


def determine_stage(
    days_past_due: int,
    rating_current: str,
    rating_origination: str,
) -> int:
    """
    IFRS 9 staging rule:
    - Stage 1: Performing (12-month ECL)
    - Stage 2: SICR (Lifetime ECL)
    - Stage 3: Credit-impaired (Lifetime ECL + default perspective)
    """
    if days_past_due < 0:
        raise ValueError("days_past_due cannot be negative")

    if rating_current not in RATING_RANK:
        raise ValueError(f"Unknown current rating: {rating_current}")

    if rating_origination not in RATING_RANK:
        raise ValueError(f"Unknown origination rating: {rating_origination}")

    # Credit-impaired proxy: 90+ dpd (common prudential backstop)
    if days_past_due >= 90:
        return 3

    rating_deterioration_notches = RATING_RANK[rating_current] - RATING_RANK[rating_origination]

    # SICR proxy:
    # 1) 30+ dpd backstop, or
    # 2) material downgrade since origination (>= 2 notches)
    if days_past_due >= 30 or rating_deterioration_notches >= 2:
        return 2

    return 1


def apply_staging(portfolio: pd.DataFrame) -> pd.DataFrame:
    required_columns = ["days_past_due", "rating_current", "rating_origination"]
    missing = [col for col in required_columns if col not in portfolio.columns]
    if missing:
        raise ValueError(f"Missing required columns for staging: {missing}")

    staged = portfolio.copy()

    staged["stage"] = staged.apply(
        lambda row: determine_stage(
            days_past_due=int(row["days_past_due"]),
            rating_current=str(row["rating_current"]),
            rating_origination=str(row["rating_origination"]),
        ),
        axis=1,
    )

    staged["sicr_flag"] = (staged["stage"] == 2).astype(int)
    staged["credit_impaired_flag"] = (staged["stage"] == 3).astype(int)

    return staged


def main() -> None:
    input_path = Path("data/input/loan_portfolio.csv")
    output_path = Path("data/output/portfolio_staged.csv")

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    portfolio = pd.read_csv(input_path)
    staged = apply_staging(portfolio)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    staged.to_csv(output_path, index=False)

    stage_distribution = staged["stage"].value_counts().sort_index()
    print(f"Staged portfolio saved to: {output_path}")
    print("Stage distribution:")
    print(stage_distribution.to_string())


if __name__ == "__main__":
    main()
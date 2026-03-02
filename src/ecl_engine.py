from __future__ import annotations

from pathlib import Path

import pandas as pd

from overlay import apply_overlay


def calculate_ecl_base(portfolio: pd.DataFrame) -> pd.DataFrame:
    required = ["ead", "lgd", "pd_effective", "stage"]
    missing = [c for c in required if c not in portfolio.columns]
    if missing:
        raise ValueError(f"Missing required columns for ECL: {missing}")

    df = portfolio.copy()

    if (df["ead"] < 0).any():
        raise ValueError("EAD cannot be negative")
    if ((df["lgd"] < 0) | (df["lgd"] > 1)).any():
        raise ValueError("LGD must be between 0 and 1")
    if ((df["pd_effective"] < 0) | (df["pd_effective"] > 1)).any():
        raise ValueError("PD effective must be between 0 and 1")

    df["ecl_base"] = df["ead"] * df["lgd"] * df["pd_effective"]
    df["ecl_base"] = df["ecl_base"].round(2)

    return df


def main() -> None:
    input_path = Path("data/output/portfolio_scenario.csv")
    output_path = Path("data/output/portfolio_ecl.csv")

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    portfolio = pd.read_csv(input_path)

    with_ecl_base = calculate_ecl_base(portfolio)
    with_ecl_final = apply_overlay(with_ecl_base)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with_ecl_final.to_csv(output_path, index=False)

    total_ead = with_ecl_final["ead"].sum()
    total_ecl = with_ecl_final["ecl_final"].sum()
    coverage_ratio = total_ecl / total_ead if total_ead > 0 else 0.0

    print(f"ECL portfolio saved to: {output_path}")
    print(f"Total EAD: {total_ead:,.2f}")
    print(f"Total ECL (final): {total_ecl:,.2f}")
    print(f"Coverage ratio: {coverage_ratio:.4%}")
    print("ECL by stage:")
    print(with_ecl_final.groupby('stage')[['ecl_base', 'overlay_amount', 'ecl_final']].sum().round(2).to_string())


if __name__ == "__main__":
    main()

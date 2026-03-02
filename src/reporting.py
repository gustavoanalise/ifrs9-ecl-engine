from __future__ import annotations

from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path("data/output")


def generate_ecl_by_loan(portfolio_ecl: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "loan_id",
        "reporting_date",
        "product_type",
        "segment",
        "stage",
        "ead",
        "lgd",
        "pd_effective",
        "ecl_base",
        "overlay_pct",
        "overlay_amount",
        "ecl_final",
    ]
    missing = [c for c in cols if c not in portfolio_ecl.columns]
    if missing:
        raise ValueError(f"Missing columns for ecl_by_loan: {missing}")

    return portfolio_ecl[cols].copy()


def generate_portfolio_summary(portfolio_ecl: pd.DataFrame) -> pd.DataFrame:
    total_ead = portfolio_ecl["ead"].sum()
    total_ecl = portfolio_ecl["ecl_final"].sum()
    coverage_ratio = (total_ecl / total_ead) if total_ead > 0 else 0.0
    n_loans = len(portfolio_ecl)

    return pd.DataFrame(
        [
            {
                "reporting_date": portfolio_ecl["reporting_date"].iloc[0],
                "n_loans": n_loans,
                "total_ead": round(total_ead, 2),
                "total_ecl": round(total_ecl, 2),
                "coverage_ratio": round(coverage_ratio, 6),
            }
        ]
    )


def generate_stage_distribution(portfolio_ecl: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        portfolio_ecl.groupby("stage", as_index=False)
        .agg(
            n_loans=("loan_id", "count"),
            total_ead=("ead", "sum"),
            total_ecl=("ecl_final", "sum"),
        )
        .sort_values("stage")
    )

    total_loans = grouped["n_loans"].sum()
    grouped["share_loans"] = grouped["n_loans"] / total_loans
    grouped["coverage_ratio_stage"] = grouped["total_ecl"] / grouped["total_ead"]

    grouped["total_ead"] = grouped["total_ead"].round(2)
    grouped["total_ecl"] = grouped["total_ecl"].round(2)
    grouped["share_loans"] = grouped["share_loans"].round(6)
    grouped["coverage_ratio_stage"] = grouped["coverage_ratio_stage"].round(6)

    return grouped


def main() -> None:
    input_path = OUTPUT_DIR / "portfolio_ecl.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    portfolio_ecl = pd.read_csv(input_path)

    ecl_by_loan = generate_ecl_by_loan(portfolio_ecl)
    portfolio_summary = generate_portfolio_summary(portfolio_ecl)
    stage_distribution = generate_stage_distribution(portfolio_ecl)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ecl_by_loan_path = OUTPUT_DIR / "ecl_by_loan.csv"
    portfolio_summary_path = OUTPUT_DIR / "portfolio_summary.csv"
    stage_distribution_path = OUTPUT_DIR / "stage_distribution.csv"

    ecl_by_loan.to_csv(ecl_by_loan_path, index=False)
    portfolio_summary.to_csv(portfolio_summary_path, index=False)
    stage_distribution.to_csv(stage_distribution_path, index=False)

    print(f"Saved: {ecl_by_loan_path}")
    print(f"Saved: {portfolio_summary_path}")
    print(f"Saved: {stage_distribution_path}")
    print("Portfolio summary:")
    print(portfolio_summary.to_string(index=False))


if __name__ == "__main__":
    main()

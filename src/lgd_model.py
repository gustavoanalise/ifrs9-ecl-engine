from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_LGD_BY_PRODUCT = {
    "TermLoan": 0.45,
    "CreditCard": 0.85,
    "Overdraft": 0.75,
    "AutoLoan": 0.50,
    "Mortgage": 0.30,
}

COLLATERAL_ADJ = {
    "None": 0.10,
    "Vehicle": -0.10,
    "Property": -0.20,
    "Guarantee": -0.15,
}

SEGMENT_ADJ = {
    "Retail": 0.00,
    "SME": 0.05,
    "Corporate": -0.03,
}


def _normalize_collateral(value: object) -> str:
    """
    Corrige leitura de CSV onde 'None' pode virar NaN.
    """
    if pd.isna(value):
        return "None"
    text = str(value).strip()
    if text == "" or text.lower() == "nan":
        return "None"
    return text


def _cap_lgd(value: float) -> float:
    return float(min(max(value, 0.0), 1.0))


def compute_lgd(product_type: str, collateral_type: str, segment: str) -> float:
    if product_type not in BASE_LGD_BY_PRODUCT:
        raise ValueError(f"Unknown product_type: {product_type}")
    if collateral_type not in COLLATERAL_ADJ:
        raise ValueError(f"Unknown collateral_type: {collateral_type}")
    if segment not in SEGMENT_ADJ:
        raise ValueError(f"Unknown segment: {segment}")

    lgd = (
        BASE_LGD_BY_PRODUCT[product_type]
        + COLLATERAL_ADJ[collateral_type]
        + SEGMENT_ADJ[segment]
    )
    return _cap_lgd(lgd)


def apply_lgd(portfolio: pd.DataFrame) -> pd.DataFrame:
    required_columns = ["product_type", "collateral_type", "segment"]
    missing = [c for c in required_columns if c not in portfolio.columns]
    if missing:
        raise ValueError(f"Missing required columns for LGD: {missing}")

    df = portfolio.copy()
    df["collateral_type"] = df["collateral_type"].apply(_normalize_collateral)

    df["lgd"] = df.apply(
        lambda r: compute_lgd(
            product_type=str(r["product_type"]),
            collateral_type=str(r["collateral_type"]),
            segment=str(r["segment"]),
        ),
        axis=1,
    )

    df["lgd"] = df["lgd"].round(6)
    return df


def main() -> None:
    input_path = Path("data/output/portfolio_pd.csv")
    output_path = Path("data/output/portfolio_lgd.csv")

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    portfolio = pd.read_csv(input_path)
    with_lgd = apply_lgd(portfolio)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with_lgd.to_csv(output_path, index=False)

    print(f"LGD portfolio saved to: {output_path}")
    print("Average LGD by product:")
    print(with_lgd.groupby("product_type")["lgd"].mean().round(6).to_string())


if __name__ == "__main__":
    main()

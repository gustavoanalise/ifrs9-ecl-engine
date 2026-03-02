from __future__ import annotations

from pathlib import Path

import pandas as pd


# CCF por produto revolving (parametrizável)
DEFAULT_CCF_BY_PRODUCT = {
    "CreditCard": 0.75,
    "Overdraft": 0.60,
}


def get_ccf(product_type: str, is_revolving: int, ccf_by_product: dict[str, float]) -> float:
    """
    Retorna CCF aplicável.
    Para não-revolving, CCF = 0 por construção.
    """
    if is_revolving not in (0, 1):
        raise ValueError(f"is_revolving must be 0 or 1, got {is_revolving}")

    if is_revolving == 0:
        return 0.0

    if product_type not in ccf_by_product:
        raise ValueError(f"Missing CCF parameter for revolving product: {product_type}")

    ccf = float(ccf_by_product[product_type])
    if ccf < 0 or ccf > 1:
        raise ValueError(f"CCF must be between 0 and 1. Got {ccf} for {product_type}")

    return ccf


def calculate_ead(
    outstanding_balance: float,
    undrawn_limit: float,
    ccf: float,
) -> float:
    """
    EAD para revolving:
      EAD = outstanding_balance + CCF * undrawn_limit
    Para não-revolving, ccf=0 e undrawn_limit=0 => EAD = outstanding_balance
    """
    if outstanding_balance < 0:
        raise ValueError("outstanding_balance cannot be negative")
    if undrawn_limit < 0:
        raise ValueError("undrawn_limit cannot be negative")
    if ccf < 0 or ccf > 1:
        raise ValueError("ccf must be between 0 and 1")

    return outstanding_balance + (ccf * undrawn_limit)


def apply_ead(
    portfolio: pd.DataFrame,
    ccf_by_product: dict[str, float] | None = None,
) -> pd.DataFrame:
    required_columns = ["product_type", "is_revolving", "outstanding_balance", "undrawn_limit"]
    missing = [col for col in required_columns if col not in portfolio.columns]
    if missing:
        raise ValueError(f"Missing required columns for EAD: {missing}")

    params = ccf_by_product or DEFAULT_CCF_BY_PRODUCT
    result = portfolio.copy()

    result["ccf_applied"] = result.apply(
        lambda row: get_ccf(
            product_type=str(row["product_type"]),
            is_revolving=int(row["is_revolving"]),
            ccf_by_product=params,
        ),
        axis=1,
    )

    result["ead"] = result.apply(
        lambda row: calculate_ead(
            outstanding_balance=float(row["outstanding_balance"]),
            undrawn_limit=float(row["undrawn_limit"]),
            ccf=float(row["ccf_applied"]),
        ),
        axis=1,
    )

    result["ead"] = result["ead"].round(2)
    return result


def main() -> None:
    input_path = Path("data/output/portfolio_staged.csv")
    output_path = Path("data/output/portfolio_ead.csv")

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    portfolio = pd.read_csv(input_path)
    with_ead = apply_ead(portfolio)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with_ead.to_csv(output_path, index=False)

    print(f"EAD portfolio saved to: {output_path}")
    print(f"Total EAD: {with_ead['ead'].sum():,.2f}")
    print("Sample revolving exposures:")
    sample = with_ead[with_ead["is_revolving"] == 1][
        ["loan_id", "product_type", "outstanding_balance", "undrawn_limit", "ccf_applied", "ead"]
    ].head(10)
    print(sample.to_string(index=False))


if __name__ == "__main__":
    main()
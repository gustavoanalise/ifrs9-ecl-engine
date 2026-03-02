from __future__ import annotations

from pathlib import Path

import pandas as pd


def build_rollforward(portfolio_ecl: pd.DataFrame) -> pd.DataFrame:
    required = ["stage", "ecl_final"]
    missing = [c for c in required if c not in portfolio_ecl.columns]
    if missing:
        raise ValueError(f"Missing columns for rollforward: {missing}")

    # Closing allowance observada no período atual (modelo)
    closing_by_stage = portfolio_ecl.groupby("stage")["ecl_final"].sum().to_dict()

    # Suposições didáticas para decomposição de movimentos
    # Objetivo: criar estrutura auditável de ponte contábil.
    originations_pct = {1: 0.08, 2: 0.03, 3: 0.01}
    transfers_in_pct = {1: 0.01, 2: 0.06, 3: 0.08}
    transfers_out_pct = {1: 0.03, 2: 0.05, 3: 0.02}
    writeoff_pct = {1: 0.001, 2: 0.01, 3: 0.08}
    recoveries_pct = {1: 0.0002, 2: 0.002, 3: 0.01}

    rows = []
    for stage in [1, 2, 3]:
        closing = float(closing_by_stage.get(stage, 0.0))

        new_originations = closing * originations_pct[stage]
        transfers_in = closing * transfers_in_pct[stage]
        transfers_out = closing * transfers_out_pct[stage]
        writeoffs = closing * writeoff_pct[stage]
        recoveries = closing * recoveries_pct[stage]

        # Fórmula:
        # Closing = Opening + New originations + Transfers in - Transfers out - Write-offs + Recoveries
        opening = closing - new_originations - transfers_in + transfers_out + writeoffs - recoveries

        rows.append(
            {
                "stage": stage,
                "opening_allowance": round(opening, 2),
                "new_originations": round(new_originations, 2),
                "transfers_in": round(transfers_in, 2),
                "transfers_out": round(transfers_out, 2),
                "writeoffs": round(writeoffs, 2),
                "recoveries": round(recoveries, 2),
                "closing_allowance": round(closing, 2),
            }
        )

    rollforward = pd.DataFrame(rows)

    # Linha total
    total = {
        "stage": "Total",
        "opening_allowance": round(rollforward["opening_allowance"].sum(), 2),
        "new_originations": round(rollforward["new_originations"].sum(), 2),
        "transfers_in": round(rollforward["transfers_in"].sum(), 2),
        "transfers_out": round(rollforward["transfers_out"].sum(), 2),
        "writeoffs": round(rollforward["writeoffs"].sum(), 2),
        "recoveries": round(rollforward["recoveries"].sum(), 2),
        "closing_allowance": round(rollforward["closing_allowance"].sum(), 2),
    }

    rollforward = pd.concat([rollforward, pd.DataFrame([total])], ignore_index=True)

    return rollforward


def main() -> None:
    input_path = Path("data/output/portfolio_ecl.csv")
    output_path = Path("data/output/allowance_rollforward.csv")

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    portfolio_ecl = pd.read_csv(input_path)
    rollforward = build_rollforward(portfolio_ecl)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    rollforward.to_csv(output_path, index=False)

    print(f"Saved: {output_path}")
    print("Allowance rollforward:")
    print(rollforward.to_string(index=False))


if __name__ == "__main__":
    main()
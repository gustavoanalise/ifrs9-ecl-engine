from __future__ import annotations

from pathlib import Path

import pandas as pd


def _validate_scenarios(scenarios: pd.DataFrame) -> None:
    required = ["scenario", "weight", "pd_multiplier"]
    missing = [c for c in required if c not in scenarios.columns]
    if missing:
        raise ValueError(f"Missing scenario columns: {missing}")

    if len(scenarios) != 3:
        raise ValueError("Scenario table must contain exactly 3 scenarios")

    weight_sum = scenarios["weight"].sum()
    if abs(weight_sum - 1.0) > 1e-9:
        raise ValueError(f"Scenario weights must sum to 1.0. Got {weight_sum}")

    if (scenarios["weight"] < 0).any():
        raise ValueError("Scenario weights cannot be negative")

    if (scenarios["pd_multiplier"] <= 0).any():
        raise ValueError("pd_multiplier must be > 0")


def _cap_probability(series: pd.Series) -> pd.Series:
    return series.clip(lower=0.0, upper=1.0)


def apply_scenario_weighted_pd(
    portfolio: pd.DataFrame,
    scenarios: pd.DataFrame,
) -> pd.DataFrame:
    required_portfolio = ["stage", "pd_12m", "pd_lifetime"]
    missing = [c for c in required_portfolio if c not in portfolio.columns]
    if missing:
        raise ValueError(f"Missing portfolio columns: {missing}")

    _validate_scenarios(scenarios)

    df = portfolio.copy()

    scenario_pd_12m_cols: list[str] = []
    scenario_pd_life_cols: list[str] = []

    for _, row in scenarios.iterrows():
        scenario_name = str(row["scenario"])
        weight = float(row["weight"])
        multiplier = float(row["pd_multiplier"])

        pd12_col = f"pd_12m_{scenario_name.lower()}"
        pdlife_col = f"pd_lifetime_{scenario_name.lower()}"

        df[pd12_col] = _cap_probability(df["pd_12m"] * multiplier).round(6)
        df[pdlife_col] = _cap_probability(df["pd_lifetime"] * multiplier).round(6)

        scenario_pd_12m_cols.append((pd12_col, weight))
        scenario_pd_life_cols.append((pdlife_col, weight))

    # Stage 1 usa PD 12m ponderada; Stage 2/3 usam PD lifetime ponderada
    df["pd_weighted_12m"] = 0.0
    for col, w in scenario_pd_12m_cols:
        df["pd_weighted_12m"] = df["pd_weighted_12m"] + (df[col] * w)

    df["pd_weighted_lifetime"] = 0.0
    for col, w in scenario_pd_life_cols:
        df["pd_weighted_lifetime"] = df["pd_weighted_lifetime"] + (df[col] * w)

    df["pd_effective"] = df.apply(
        lambda r: r["pd_weighted_12m"] if int(r["stage"]) == 1 else r["pd_weighted_lifetime"],
        axis=1,
    )

    df["pd_weighted_12m"] = df["pd_weighted_12m"].round(6)
    df["pd_weighted_lifetime"] = df["pd_weighted_lifetime"].round(6)
    df["pd_effective"] = df["pd_effective"].round(6)

    return df


def main() -> None:
    portfolio_path = Path("data/output/portfolio_lgd.csv")
    scenarios_path = Path("data/input/macro_scenarios.csv")
    output_path = Path("data/output/portfolio_scenario.csv")

    if not portfolio_path.exists():
        raise FileNotFoundError(f"Portfolio file not found: {portfolio_path}")
    if not scenarios_path.exists():
        raise FileNotFoundError(f"Scenario file not found: {scenarios_path}")

    portfolio = pd.read_csv(portfolio_path)
    scenarios = pd.read_csv(scenarios_path)

    with_scenarios = apply_scenario_weighted_pd(portfolio, scenarios)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with_scenarios.to_csv(output_path, index=False)

    print(f"Scenario-adjusted portfolio saved to: {output_path}")
    print("Average effective PD by stage:")
    print(with_scenarios.groupby("stage")["pd_effective"].mean().round(6).to_string())


if __name__ == "__main__":
    main()

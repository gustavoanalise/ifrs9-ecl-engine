# IFRS 9 Expected Credit Loss Engine

Motor estruturado, auditavel e reproduzivel para calculo de Expected Credit Loss (ECL) conforme IFRS 9.

## 1. Objetivo

Este projeto implementa um fluxo completo de impairment IFRS 9 com:

- Staging (Stage 1, Stage 2/SICR, Stage 3/credit-impaired)
- EAD com CCF para produtos revolving
- PD 12m e PD Lifetime
- LGD por produto, colateral e segmento
- Cenarios macroeconomicos ponderados por probabilidade
- Overlay gerencial parametrico
- ECL por contrato e consolidado de carteira
- Rollforward de allowance
- Dashboard Streamlit para analise executiva e drill-down

## 2. Arquitetura do repositorio

```text
ifrs9-ecl-engine/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── input/
│   │   ├── loan_portfolio.csv
│   │   └── macro_scenarios.csv
│   └── output/
│       ├── portfolio_staged.csv
│       ├── portfolio_ead.csv
│       ├── portfolio_pd.csv
│       ├── portfolio_lgd.csv
│       ├── portfolio_scenario.csv
│       ├── portfolio_ecl.csv
│       ├── ecl_by_loan.csv
│       ├── portfolio_summary.csv
│       ├── stage_distribution.csv
│       └── allowance_rollforward.csv
├── src/
│   ├── data_generation.py
│   ├── staging.py
│   ├── ead.py
│   ├── pd_model.py
│   ├── lgd_model.py
│   ├── scenario_engine.py
│   ├── overlay.py
│   ├── ecl_engine.py
│   ├── reporting.py
│   └── rollforward.py
└── app/
    └── streamlit_app.py
```

## 3. Metodologia IFRS 9 (visao tecnica)

### 3.1 Staging

Funcao principal:

`determine_stage(days_past_due, rating_current, rating_origination) -> int`

Regras implementadas:

- Stage 3: `days_past_due >= 90`
- Stage 2 (SICR): `days_past_due >= 30` ou downgrade material (>= 2 notches)
- Stage 1: demais casos

Racional IFRS 9:

- Stage 1 usa perda esperada de 12 meses
- Stage 2 e Stage 3 usam perda esperada de vida inteira (Lifetime ECL)

### 3.2 EAD

Para revolving:

`EAD = outstanding_balance + CCF * undrawn_limit`

Para nao-revolving:

`EAD = outstanding_balance`

CCF e parametrizado por produto (`CreditCard`, `Overdraft`).

### 3.3 PD

- PD 12m baseada em rating atual, multiplicador por segmento e piso por stage
- PD Lifetime convertida a partir da PD 12m com aproximacao de hazard constante:

`PD_lifetime = 1 - (1 - PD_12m) ^ anos_remanescentes`

- Cap de probabilidade em 100% (`<= 1.0`)

### 3.4 LGD

LGD modelada por:

- produto
- tipo de colateral
- segmento

Com limites `[0%, 100%]` para robustez.

### 3.5 Cenarios macroeconomicos (forward-looking)

Tres cenarios:

- Optimistic
- Baseline
- Adverse

Cada um com:

- `weight` (pesos somam 1.0)
- `pd_multiplier`

PD efetiva:

- Stage 1: PD ponderada de 12m
- Stage 2/3: PD ponderada Lifetime

### 3.6 Overlay gerencial

Ajuste adicional por stage aplicado sobre `ecl_base`:

- Stage 1: 0%
- Stage 2: 5%
- Stage 3: 10%

Formula:

`ECL_final = ECL_base + overlay_amount`

### 3.7 ECL

Formula central:

`ECL_base = EAD * LGD * PD_effective`

Com overlay:

`ECL_final = ECL_base + overlay_amount`

### 3.8 Rollforward de allowance

Estrutura de conciliacao:

`Opening + New originations + Transfers in - Transfers out - Write-offs + Recoveries = Closing`

Objetivo: suportar disclosure e rastreabilidade da variacao de provisao.

## 4. Pipeline de execucao

No ambiente virtual ativo (`.venv`), execute nesta ordem:

```powershell
python src/data_generation.py
python src/staging.py
python src/ead.py
python src/pd_model.py
python src/lgd_model.py
python src/scenario_engine.py
python src/ecl_engine.py
python src/reporting.py
python src/rollforward.py
```

Dashboard:

```powershell
streamlit run app/streamlit_app.py
```

## 5. Outputs obrigatorios

Gerados em `data/output`:

- `ecl_by_loan.csv`: trilha auditavel por contrato
- `portfolio_summary.csv`: KPIs consolidados (EAD, ECL, coverage ratio)
- `stage_distribution.csv`: distribuicao de contratos, EAD e ECL por stage
- `allowance_rollforward.csv`: conciliacao de abertura para fechamento

## 6. Leitura gerencial

- Aumento de exposicao em Stage 2/3 tende a elevar coverage ratio
- Aumento de CCF eleva EAD de produtos revolving e pressiona allowance
- Cenario adverse aumenta PD ponderada e eleva ECL
- Overlay aumenta conservadorismo de provisao com governanca explicita

## 7. Governanca e auditabilidade

- Regras de negocio segregadas por modulo
- Validacoes de colunas e faixas de parametros
- Formula explicita em codigo e documentacao
- Fluxo reproduzivel fim a fim
- Commits incrementais por etapa

## 8. Limitacoes atuais 

Limitacoes:

- Dataset sintetico
- Staging simplificado (sem cure logic e sem watchlist)
- PD/LGD sem calibracao estatistica real
- Rollforward com decomposicao didatica

## 9. Dependencias

Instalacao:

```powershell
pip install -r requirements.txt
```

Principais bibliotecas:

- `pandas`
- `numpy`
- `streamlit`
- `plotly`

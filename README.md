# IFRS 9 ECL Engine

Structured, auditable, and professional implementation of an IFRS 9 Expected Credit Loss (ECL) engine.

## Current status

- Stage 0 completed: environment setup, local Git repository, GitHub remote, first push.
- Stage 1 completed: mandatory repository structure and module scaffolding.

## Mandatory repository structure

```text
ifrs9-ecl-engine/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── input/
│   └── output/
├── src/
│   ├── config.py
│   ├── data_generation.py
│   ├── parameters.py
│   ├── staging.py
│   ├── ead.py
│   ├── pd_model.py
│   ├── lgd_model.py
│   ├── scenario_engine.py
│   ├── overlay.py
│   ├── ecl_engine.py
│   ├── rollforward.py
│   └── reporting.py
└── app/
    └── streamlit_app.py
```

## Next stage

- Stage 2: synthetic portfolio data generation with controlled assumptions for staging, EAD, PD, LGD, scenarios, and rollforward.

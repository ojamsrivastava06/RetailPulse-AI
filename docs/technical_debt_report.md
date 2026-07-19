# Technical Debt Report

## Open Debt

- `forecasting_enhanced.py` is still a monolithic module with forecasting, tuning, reporting, explainability, and artifact persistence in one file.
- `inventory_optimization.py` is similarly broad and would benefit from separate data-prep, modeling, reporting, and notebook-generation modules.
- The repository remains a flat `src/` module layout rather than a namespaced package layout.
- Notebook outputs and generated figures dominate the working tree and make code review harder.
- There is no CI pipeline yet for tests, formatting, or notebook smoke checks.

## Recommended Next Steps

1. Split forecasting and inventory into subpackages with dedicated `artifacts`, `reports`, `models`, and `features` modules.
2. Add CI for `pytest`, Black, and import smoke checks.
3. Add lightweight integration tests for the Streamlit and FastAPI entry points.
4. Archive historical report backups outside the repository.


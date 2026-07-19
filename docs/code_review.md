# Code Review

## Highest-Priority Findings

1. Artifact overwrite risk was present in Phase 1, customer-intelligence outputs, and the legacy reporting pipeline. This was addressed by introducing shared backup-aware write helpers.
2. The legacy `retailpulse_pipeline.py` reimplemented cleaning and feature engineering instead of reusing the modular pipeline. This was refactored to call the shared preprocessing and feature modules.
3. Phase 2 output persistence mixed up customer metrics and cluster metrics. The output writer now persists `rfm_table.csv`, `customer_metrics.csv`, `segment_summary.csv`, and `cluster_metrics.csv` distinctly.
4. Test modules relied on repeated `sys.path.append(...)` bootstrap code. This was consolidated in `tests/conftest.py`.

## Additional Findings

- Repeated constants such as `random_state=42`, profit margin, and season mappings were partially centralized.
- Path configuration was inconsistent between modules. Shared settings now define the project roots and artifact locations.
- Large generated backup files create review noise and should remain ignored by Git.

## Residual Risk

- Enhanced forecasting and inventory modules still contain substantial surface area and would benefit from smaller internal components.
- Optional dependency paths are intentionally permissive and should be covered by additional integration tests when those libraries are installed.


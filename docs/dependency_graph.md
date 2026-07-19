# Dependency Graph

## Internal Module Graph

```text
settings -> constants
config -> settings
retail_rules -> constants
features -> constants, retail_rules
pipeline -> config, preprocessing, features, quality_report, io_utils, logger, utils
retailpulse_pipeline -> config, constants, preprocessing, features, io_utils
customer_intelligence -> constants, io_utils, logger
forecasting -> constants, io_utils, logger, metrics_utils, retail_rules
inventory_optimization -> config, constants, io_utils, logger, report_utils, retail_rules
```

## Runtime Surfaces

- `app/Home.py` and `app/pages/Sales_Dashboard.py` consume processed data for Streamlit views.
- `service/main.py` exposes the lightweight FastAPI surface.
- `tests/` targets customer intelligence, enhanced forecasting, inventory optimization, and legacy pipeline compatibility.

## External Dependencies

- Core data stack: `pandas`, `numpy`, `scipy`, `openpyxl`
- Visualization: `matplotlib`, `seaborn`, `streamlit`
- ML: `scikit-learn`, `statsmodels`
- Service: `fastapi`, `uvicorn`
- Optional forecasting: `xgboost`, `lightgbm`, `catboost`, `prophet`, `pmdarima`, `tensorflow`, `shap`


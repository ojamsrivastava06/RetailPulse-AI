# RetailPulse

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Architecture](https://img.shields.io/badge/status-architecture%20freeze-success)
![Tests](https://img.shields.io/badge/tests-regression%20coverage-brightgreen)

RetailPulse is a multi-phase retail analytics repository built on the Online Retail II dataset. The business workflows for data engineering, customer intelligence, forecasting, and inventory optimization were preserved as-is during this refactor; the work in this repository is focused on production hardening, artifact safety, documentation, and testability.

## Project Overview

- Phase 1: transactional data cleaning, validation, and feature engineering
- Phase 2: RFM analysis, customer segmentation, and CLV estimation
- Phase 3: baseline and enhanced demand forecasting workflows
- Phase 4: inventory planning, risk modeling, and recommendation generation
- Phase 5: customer churn scoring, retention intelligence, and action recommendations
- Phase 6: Power BI design, implementation documentation, and executive reporting guidance
- Interactive Streamlit Dashboard: unified AI analytics application over the completed phase artifacts

## Architecture

The repository now has a clearer separation between source code, generated artifacts, and engineering documentation.

```text
RetailPulse/
api/                  Enterprise FastAPI backend
├── app/                  Streamlit user interface
├── data/                 Source and curated datasets
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── external/
├── docs/                 Architecture and audit reports
├── models/               Serialized model artifacts
├── notebooks/            Analyst and business notebooks
├── processed/            Forecast and inventory output tables
├── reports/              Markdown reports and generated figures
├── service/              FastAPI service entry point
├── src/                  Shared Python modules and pipelines
├── tests/                Regression and architecture tests
├── .github/              GitHub collaboration templates
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── pyproject.toml
└── requirements.txt
```

## Folder Structure

- `src/config.py`, `src/settings.py`, `src/constants.py`, and `src/logger.py` centralize paths, reusable constants, and logging.
- `src/io_utils.py`, `src/report_utils.py`, and `src/retail_rules.py` provide shared write-safety, reporting, and normalization helpers.
- `api/` exposes the completed AI capabilities through authenticated read-only FastAPI endpoints.
- `docs/` contains the architecture audit, code review, dependency notes, and technical debt register created during the production-hardening pass.
- `processed/`, `reports/`, and `models/` remain backward-compatible output locations for the existing business workflows.

## Execution Order

1. `python src/run_phase_one.py`
2. `python -c "from customer_intelligence import run_phase_two; run_phase_two()"`
3. `python src/run_phase_three.py` or `python src/run_phase_three_enhanced.py`
4. `python src/run_phase_four.py`
5. `python src/run_phase_five.py`

## Pipeline Diagram

```text
Raw Excel
  -> preprocessing.clean_transaction_data
  -> features.engineer_features
  -> data/processed/final_processed_dataset.csv
  -> customer_intelligence.run_phase_two
  -> forecasting.run_phase_three / forecasting_enhanced.run_enhanced_forecasting
  -> inventory_optimization.run_inventory_optimization
  -> customer_churn.run_phase_five
  -> reports/, processed/, models/
```

## Model Zoo

- Customer intelligence: `KMeans`, `PCA`
- Forecasting baseline: Naive, Moving Average, Linear Regression, Random Forest
- Forecasting optional: XGBoost, LightGBM, Prophet, TensorFlow sequence models
- Inventory risk: Logistic Regression, Decision Tree, Random Forest
- Inventory optional: XGBoost, LightGBM
- Churn intelligence: Logistic Regression, Decision Tree, Random Forest, SVM, KNN, Naive Bayes, MLP, plus optional XGBoost, LightGBM, and CatBoost

## Outputs

- Phase 1 writes curated datasets to `data/processed/`
- Phase 2 writes segmentation tables, figures, models, and markdown reports
- Phase 3 writes forecast results to `processed/`, `reports/`, and `models/`
- Phase 4 writes inventory datasets, dashboards, recommendations, notebooks, and reports
- Phase 5 writes churn predictions, customer health scores, probability tables, recommendations, model artifacts, notebooks, figures, and markdown reports
- Shared write helpers now create timestamped backups before replacing existing artifacts

## Phase 5 Churn Intelligence

`src/customer_churn.py` implements the enterprise customer churn and retention engine. It reuses the shared retail normalization, logging, report, notebook, figure, and safe artifact-writing utilities.

- Label generation supports configurable churn windows, with 30, 60, 90, and 180 days enabled by default.
- Feature engineering builds recency, frequency, revenue, rolling-window, diversity, momentum, purchase timing, engagement, health, and lifetime-value signals.
- The model zoo benchmarks Logistic Regression, Decision Tree, Random Forest, Extra Trees, Gradient Boosting, AdaBoost, SVM, KNN, Naive Bayes, MLP, and optional XGBoost, LightGBM, and CatBoost when installed.
- Optimization includes randomized search, grid search, cross-validation, class-weight search, RFE feature selection, threshold optimization, probability calibration, permutation importance, and SHAP/LIME-compatible explainability tables.
- Business outputs include churn probability, retention probability, health score, risk category, next purchase probability, expected lifetime value, recommended action, and action reasoning for every customer.
- The default run creates an 80-figure executive visual package; tests and lightweight smoke runs can lower this with `target_visual_count` and `figure_dpi` without changing production defaults.

## Installation

Install the core stack:

```bash
pip install -r requirements.txt
```

Install the optional forecasting dependencies when you want the full model zoo:

```bash
pip install -r requirements-forecasting-optional.txt
```

## Launch the Streamlit Platform

The enterprise Streamlit app is located in `app/` and reuses the existing processed datasets, saved models, markdown reports, and generated figures. It does not retrain models, rewrite source datasets, or run the pipeline phases.

Start the application from the repository root:

```bash
streamlit run app/Home.py
```

Then open the local URL Streamlit prints in the terminal, usually:

```text
http://localhost:8501
```

The app includes:

- Home overview with navigation cards, KPI summary, model status, recent reports, and health checks
- Executive, Sales, Customer Intelligence, Demand Forecasting, Inventory Optimization, and Churn dashboards
- AI Insights page with deterministic cross-phase summaries and recommendations
- Report Center downloads for processed CSVs, markdown reports, generated figures, and model artifacts
- Settings page for light/dark theme selection and cached data refresh

## Launch the Enterprise API

The Enterprise FastAPI backend is located in `api/` and reads the same completed artifacts used by Streamlit. It does not retrain models, overwrite datasets, or rerun ML pipelines.

Start the API from the repository root:

```bash
uvicorn api.main:app --reload
```

The previous service entry point also delegates to the new backend:

```bash
uvicorn service.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/openapi.json
http://127.0.0.1:8000/redoc
```

### API Endpoint Groups

- Health: `/health`, `/version`, `/status`
- Forecast: `/forecast`, `/forecast/leaderboard`, `/forecast/metrics`, `/forecast/future`
- Inventory: `/inventory`, `/inventory/recommendations`, `/inventory/risk`, `/inventory/abc`, `/inventory/xyz`
- Customer: `/customer/segments`, `/customer/rfm`, `/customer/clv`, `/customer/health`
- Churn: `/churn`, `/churn/predictions`, `/churn/actions`, `/churn/probabilities`
- Decision Intelligence: `/decision`, `/decision/alerts`, `/decision/scenarios`, `/decision/recommendations`, `/decision/executive`
- Analytics: `/analytics/overview`, `/analytics/kpis`, `/analytics/summary`
- Reports: `/reports`, `/reports/download/{filename}`

Standard JSON endpoints return `status`, `message`, `timestamp`, `data`, and `metadata`.

Example:

```bash
curl -H "X-API-Key: retailpulse-dev-api-key" \
  "http://127.0.0.1:8000/forecast/future?horizon_days=30&limit=5"
```

More details:

- [API Guide](docs/API_GUIDE.md)
- [Endpoint Catalog](docs/ENDPOINTS.md)
- [Authentication](docs/AUTHENTICATION.md)
- [Launch Notes](docs/DEPLOYMENT_NOTES.md)

## Quality Guardrails

- `pyproject.toml` configures Black and pytest defaults
- `tests/` contains regression coverage for customer intelligence, forecasting, inventory, and pipeline compatibility
- Generated artifacts are backed up before writes in the refactored modules
- Phase 5 adds a new customer retention workflow while preserving the existing architecture and shared utilities

## MLflow Experiment Tracking

The project includes built-in experiment tracking with MLflow to capture model training runs, hyperparameters, metrics, and generated artifacts.

### Configuration
- Tracking is configured to use a local filesystem URI (`mlruns/` directory in the project root).
- If MLflow is not installed or unavailable in the execution environment, the pipelines fall back gracefully to standard execution without experiment tracking, showing a warning without crashing.

### Logged Experiments
- **RetailPulse Customer Intelligence**: Captures customer segmentation clustering (KMeans parameters, segment summaries, and silhouette metrics).
- **RetailPulse Forecasting**: Tracks both baseline and enhanced time-series forecasting (leaderboard comparisons, best model selection, backtest metrics, and forecast charts).
- **RetailPulse Inventory Optimization**: Tracks safety stock risk classification models (F1-score, accuracy, precision, recall, and inventory dashboards).
- **RetailPulse Customer Churn**: Tracks user churn prediction models (leaderboard AUC, accuracy, F1 metrics, retention funnels, and confusion matrices).

### Configuration
- Validation is run automatically at the start of Phase 1 preprocessing (`src/pipeline.py` and `src/retailpulse_pipeline.py`).
- Expectations verify critical properties of the raw dataset:
  - **Column Existence**: Verifies that required fields (`Invoice`, `Customer ID`, `Price`, `Quantity`, `InvoiceDate`, `Country`) are present.
  - **Null/Missing Values**: Asserts acceptable null thresholds (e.g., maximum null rates for `Invoice`, `Customer ID`, and `Price`).
  - **Data Types**: Validates that numeric columns are correctly typed (`Quantity` is an integer, `Price` is a float, `InvoiceDate` is a timestamp).
  - **Value Ranges**: Checks for logical bounds (e.g. non-negative prices and quantities).
  - **Format Consistency**: Verifies date format parses and conforms to standard formats.
  - **Duplicate Values**: Flags duplicate transactions.

### Reports
All validation runs generate three artifacts under `reports/data_validation/`:
1. `validation_report.html`: A beautiful, responsive visual summary dashboard.
2. `validation_report.json`: Full detailed serialization of the Great Expectations results.
3. `validation_summary.csv`: A tabular summary of all checks, their statuses, parameters, and observed values.

## Hyperparameter Optimization (Optuna)

The platform features automated hyperparameter tuning using Optuna to search parameter spaces and optimize classifier performance across multiple algorithms (Random Forest, Extra Trees, Gradient Boosting, XGBoost, and LightGBM).

### Workflow & Parameters
- Tuning is run via `src/hyperparameter_optimization.py` with 5-fold Stratified Cross-Validation on the processed churn features.
- Optuna maximizes the CV accuracy score over a default of 30 trials per model.
- Seed is set to 42 for complete reproducibility.
- Parameter spaces tuned:
  - **Random Forest**: `n_estimators`, `max_depth`, `min_samples_split`, `min_samples_leaf`
  - **XGBoost**: `learning_rate`, `max_depth`, `n_estimators`, `subsample`, `colsample_bytree`
  - **Gradient Boosting**: `learning_rate`, `n_estimators`, `max_depth`
  - **Extra Trees**: `n_estimators`, `max_depth`
  - **LightGBM**: `n_estimators`, `max_depth`, `learning_rate`, `num_leaves` (if installed)

### MLflow Integration
- All trials are logged under the experiment `RetailPulse Hyperparameter Optimization`.
- Each trial logs: parameters, validation metrics, execution time, and best trial model parameters as nested runs under the parent study run.

### Reports
Tuning execution automatically compiles and saves five reporting artifacts under `reports/optimization/`:
1. `best_parameters.json`: Best parameter sets for each tuned classifier architecture.
2. `optimization_history.csv`: Chronological trial value progression records.
3. `optimization_summary.csv`: Aggregated tuning performance and time statistics per model.
4. `leaderboard.csv`: Table sorting all classifiers by their highest achieved CV score.
5. `feature_importance.csv`: Feature importances computed from the overall best classifier.

## Documentation

- [Architecture Review](docs/architecture_review.md)
- [Code Review](docs/code_review.md)
- [Project Tree](docs/project_tree.md)
- [Dependency Graph](docs/dependency_graph.md)
- [Performance Report](docs/performance_report.md)
- [Technical Debt Report](docs/technical_debt_report.md)
- [Refactoring Summary](docs/refactoring_summary.md)

## Future Work

- Break down the monolithic enhanced forecasting and inventory modules into subpackages
- Add CI for formatting, tests, and notebook smoke checks
- Introduce coverage reporting and typed static analysis
- Archive or externalize old generated report backups to reduce repository noise

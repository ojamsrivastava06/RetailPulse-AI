# RetailPulse – AI-Powered Retail Demand Forecasting & Inventory Intelligence

RetailPulse is a machine learning and data analytics application built to analyze retail transaction data, segment customers, forecast demand, optimize inventory stock levels, and predict customer churn risk.

## Project Overview

RetailPulse helps retail businesses make data-driven decisions. The system processes raw transaction invoices, groups customers based on buying behavior, estimates future sales volumes, calculates safe inventory stock levels, and identifies customers who are at risk of leaving.

The project includes an interactive multi-page Streamlit web dashboard for visualization, a FastAPI REST service to expose data endpoints, and background machine learning pipelines for data validation, experiment tracking, and model hyperparameter tuning.

## Dataset

The project uses the **Online Retail II** dataset from the **UCI Machine Learning Repository**, containing transaction records from a UK-based online retailer.

- **Raw Dataset**: `data/raw/online_retail_II.xlsx`
- **Final Processed Dataset**: `data/processed/final_processed_dataset.csv`

The raw dataset is cleaned, transformed, and feature-engineered to produce `final_processed_dataset.csv`, which is used across all machine learning and analytics modules.

## Features

- **Customer Segmentation**: Calculates Recency, Frequency, and Monetary (RFM) metrics and groups customers into behavioral segments.
- **Demand Forecasting**: Estimates future sales volumes and demand trends across different time horizons.
- **Inventory Optimization**: Calculates Safety Stock, Reorder Points (ROP), Economic Order Quantity (EOQ), and ABC/XYZ product classifications.
- **Customer Churn Risk Prediction**: Calculates customer health scores and predicts churn probability to support retention efforts.

## Machine Learning Modules

- **Customer Segmentation**: KMeans clustering optimized with Principal Component Analysis (PCA) and t-SNE for dimensionality reduction.
- **Demand Forecasting**: Linear Regression, Random Forest, and XGBoost models for sales volume estimation.
- **Customer Churn Prediction**: Random Forest, Extra Trees, Gradient Boosting, LightGBM, and XGBoost classifiers for churn probability prediction.

## Streamlit Dashboard

The Streamlit web application (`app/Home.py`) provides an interactive multi-page interface. The dashboard focuses on business analytics, forecasting, customer intelligence, inventory optimization, and churn prediction.

The pages in `app/pages/` are:

- **Home (`app/Home.py`)**: Landing page with system overview, key metrics, and navigation links.
- **Executive Dashboard (`app/pages/01_Executive_Dashboard.py`)**: High-level overview of total revenue, customer counts, sales trends, and key performance metrics.
- **Sales Analytics (`app/pages/02_Sales_Analytics.py`)**: Interactive charts showing sales patterns, monthly revenue, and product performance.
- **Customer Intelligence (`app/pages/03_Customer_Intelligence.py`)**: Visualizations of customer RFM clusters, segment breakdowns, and Customer Lifetime Value (CLV).
- **Demand Forecasting (`app/pages/04_Demand_Forecasting.py`)**: Comparison charts of historical sales versus predicted values with model evaluation metrics.
- **Inventory Optimization (`app/pages/05_Inventory_Optimization.py`)**: Stock health tracking, ABC/XYZ matrix, safety stock recommendations, and reorder point alerts.
- **Customer Churn (`app/pages/06_Customer_Churn.py`)**: Distribution of customer health scores, high-risk churn lists, and suggested retention actions.
- **Settings (`app/pages/09_Settings.py`)**: Configuration page to adjust thresholds, model options, and file paths.

## FastAPI

A backend REST API is built using FastAPI (`api/main.py`) to serve project artifacts and predictions through RESTful endpoints.

- **Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc).
- **Endpoints**: Provides read-only API endpoints for service health (`/health`), demand forecasts (`/forecast`), inventory optimization (`/inventory`), customer intelligence (`/customer`), churn predictions (`/churn`), analytics summaries (`/analytics`), and reports (`/reports`).

## MLflow

MLflow (`src/mlflow_utils.py`) is used for machine learning experiment tracking and logging.

- Logs model parameters, evaluation metrics (cross-validation accuracy, execution time), and model artifacts.
- Stores experiment runs locally in the `mlruns/` directory.

## Evidently AI

Evidently AI (`src/data_monitoring.py`) is implemented for automated data monitoring and drift detection.

- Evaluates data quality and tracks statistical drift between reference and current datasets.
- Generates interactive HTML reports (`data_drift_report.html`, `data_quality_report.html`) and summary JSON/CSV files in `reports/evidently/`.

## Great Expectations

Great Expectations (`src/validation.py`) is used for dataset validation and quality checks.

- Checks column existence, data types, null value percentages, numeric value ranges, and duplicate records.
- Generates HTML and JSON validation reports stored in `reports/data_validation/`.

## Optuna

Optuna (`src/hyperparameter_optimization.py`) performs automated hyperparameter optimization for machine learning models.

- Uses 5-fold cross-validation and Tree-structured Parzen Estimator (TPE) sampling to tune Random Forest, Extra Trees, Gradient Boosting, XGBoost, and LightGBM classifiers.
- Generates leaderboard CSVs, optimization history, and best parameter JSON files in `reports/optimization/`.

## Power BI Dashboard

A separate Power BI dashboard has been created for business analytics.

Location:
powerbi/RetailPulse_Dashboard.pbix

## Folder Structure

```text
retailpulse-main/
├── api/                      # FastAPI REST API endpoints, routers, and schemas
├── app/                      # Streamlit web application
│   ├── components/           # UI layout components and helpers
│   ├── pages/                # Multi-page Streamlit dashboard modules
│   └── styles/               # CSS styling files
├── data/                     # Dataset storage
│   ├── processed/            # Cleaned final dataset (final_processed_dataset.csv)
│   └── raw/                  # Source transaction dataset (online_retail_II.xlsx)
├── models/                   
├── notebooks/               
├── powerbi/                  # Power BI dashboard file (RetailPulse_Dashboard.pbix)
├── processed/                # Computed batch predictions and analytical output CSVs
├── reports/                  
│   ├── evidently/            # Evidently AI data drift and quality reports
│   └── optimization/         # Optuna hyperparameter tuning outputs
├── src/                     
├── tests/                    # Pytest test suite for API, models, and pipelines
├── .gitattributes            # Git LFS tracking configuration
├── .gitignore                # Git ignore rules
├── LICENSE                   # License file
├── pyproject.toml            # Formatter and test configurations
├── requirements.txt          # Main runtime dependencies
└── README.md                 # Project documentation
```

## Technology Stack

- **Languages**: Python
- **Frontend Dashboard**: Streamlit, Plotly, HTML/CSS
- **REST API**: FastAPI, Uvicorn, Pydantic
- **Machine Learning & Data Science**: Scikit-learn, Pandas, NumPy, SciPy, Statsmodels
- **Data Validation & Monitoring**: Great Expectations, Evidently AI, MLflow
- **Hyperparameter Optimization**: Optuna
- **Business Intelligence**: Power BI (`powerbi/RetailPulse_Dashboard.pbix`)
- **Testing & Code Quality**: Pytest, Black, Joblib

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ojamsrivastava06/RetailPulse-AI.git
   cd RetailPulse-AI
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # On Windows
   # source .venv/bin/activate  # On Linux/Mac
   ```

3. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## How to Run

- **Launch the Streamlit Dashboard**:
  ```bash
  streamlit run app/Home.py
  ```
  Access the web interface at `http://localhost:8501`.

- **Launch the FastAPI REST Server**:
  ```bash
  uvicorn api.main:app --reload
  ```
  Access API documentation at `http://localhost:8000/docs`.

- **Run Automated Tests**:
  ```bash
  pytest
  ```

- **Run Core Pipeline Execution Script**:
  ```bash
  python src/retailpulse_pipeline.py
  ```

## Project Outputs

- **Cleaned Transaction Dataset**: `data/processed/final_processed_dataset.csv`
- **Batch Analytical CSVs**: `processed/*.csv` (forecast outcomes, segment groups, safety stock metrics, churn probabilities)
- **Trained Model Binaries**: `models/*.pkl` (best forecast model, best churn model, customer health model, scalers, PCA, KMeans)
- **Data Drift & Quality Reports**: `reports/evidently/` (HTML & JSON drift/quality reports)
- **Hyperparameter Optimization Artifacts**: `reports/optimization/` (leaderboard, best parameters, feature importances)
- **Project Outputs (Generated after pipeline execution)**: `reports/figures/*.png` and markdown reports in `reports/`
- **Power BI Report File**: `powerbi/RetailPulse_Dashboard.pbix`

## Future Improvements

1. Support real-time streaming data ingestion for live sales tracking.
2. Automate model retraining and evaluation pipelines using CI/CD workflows.
3. Containerize the application using Docker for easy deployment.
4. Expand deep learning time-series models for multi-store demand forecasting.

## Author

Ojam Srivastava  
Email: ojamsrivastava06@gmail.com  
GitHub: [ojamsrivastava06](https://github.com/ojamsrivastava06)

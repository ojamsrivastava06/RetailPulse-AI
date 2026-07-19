# RetailPulse – AI-Powered Retail Demand Forecasting & Customer Intelligence Platform

An interactive analytics application built to process retail transactions, segment customers, forecast demand, optimize inventory, and predict customer churn risks.

## Project Overview
RetailPulse processes historical transactional invoices, performs customer segmentation, estimates future sales volumes, calculates safety stocking thresholds, and scores churn risk levels. The project provides a multi-page Streamlit dashboard for visualization and machine learning insights, with modular backend components for analytics and prediction services.

## Technology Stack
* **Frontend UI:** Streamlit, Plotly, HTML/CSS
* **Backend REST API:** FastAPI, Uvicorn, Pydantic
* **Analytics & Machine Learning:** Scikit-learn, Pandas, NumPy
* **Run Monitoring:** MLflow, Evidently AI
* **Tool Configuration:** Pytest, Pathlib

## Project Phases

### Phase 1 – Data Exploration & Preparation
Processes raw transaction logs, normalizes numeric values, parses invoices, and performs initial feature engineering.

### Phase 2 – Customer Intelligence
Calculates RFM metrics (Recency, Frequency, Monetary value) and clusters customers into behavioral groups using KMeans.

### Phase 3 – Demand Forecasting
Benchmarks and trains regression models to forecast transaction demand across multiple business horizons.

### Phase 4 – Inventory Optimization
Calculates Safety Stocks, Economic Order Quantity (EOQ), and Reorder Points (ROP) with ABC/XYZ classifications.

### Phase 5 – Customer Churn Prediction
Computes customer health scores and scores individual churn probability rankings.

## System Architecture
The application runs on a batch-inference data flow:
1. Offline python pipeline scripts (`src/`) process raw transaction records, run model training, and save prediction outputs.
2. The pipeline writes batch output datasets to local CSV tables in the `processed/` directory.
3. The Streamlit web server and FastAPI REST service load these cached output tables directly from the disk.

## Folder Structure
```text
RetailPulse-AI/
├── api/                      # FastAPI endpoint routes, services, and schemas
├── app/                      # Streamlit application source files
│   ├── components/           # UI components, layout styles, and loaders
│   ├── pages/                # Streamlit multi-page dashboards
│   └── styles/               # CSS stylesheets
├── data/                     # Data folder          
│   ├── processed/            # Location of cleaned transaction dataset
│   └── raw/                  # Source raw data files
├── models/                   # Serialized ML model binaries (.pkl)
├── notebooks/                # Jupyter notebooks for data analysis prototyping
├── processed/                # Pre-computed batch inference output CSVs
├── reports/                  # Generated reports, visualizations, and validation outputs
│   ├── data_validation/      # Data validation results
│   ├── evidently/            # Data quality monitoring reports
│   ├── figures/              # Charts and visualizations
│   └── optimization/         # Hyperparameter optimization outputs
├── src/                      # ML pipeline training and data processing code
├── tests/                    # Unit and regression testing suite
├── .gitattributes            # Git LFS tracking configuration
├── .gitignore                # Excluded files and folders config
├── LICENSE                   # Project LICENSE
├── pyproject.toml            # Formatter and test configurations
├── requirements.txt          # Main runtime dependencies
└── README.md
```

## Dataset
The application uses the **Online Retail II** dataset from the UCI Machine Learning Repository, containing transactional history for a UK-based online retail store.

## Machine Learning Models
* **Clustering (Phase 2):** KMeans (optimized with Principal Component Analysis and t-SNE)
* **Forecasting (Phase 3):** Linear Regression, Random Forest, XGBoost
* **Churn Classifier (Phase 5):** Random Forest, Extra Trees, Gradient Boosting, AdaBoost

## Outputs
* **Cleaned dataset:** `data/processed/final_processed_dataset.csv`
* **Prediction tables:** `processed/*.csv` (forecast outcomes, segment groups, safety stock metrics, churn probabilities)
* **Pre-rendered charts:** `reports/figures/*.png`
* **Model binaries:** `models/*.pkl`

## Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/ojamsrivastava06/RetailPulse-AI.git
   cd RetailPulse-AI
   ```
2. **Setup virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Run Streamlit
Launch the multi-page Streamlit dashboard from the project root:
```bash
streamlit run app/Home.py
```
Access the UI at: `http://localhost:8501`

## Run FastAPI
Expose REST endpoints using the Uvicorn server:
```bash
uvicorn api.main:app --reload
```
Access API documentation at: `http://localhost:8000/docs`

## Deployment
* **GitHub:** Hosted under Git version control. Large dataset files (`data/processed/final_processed_dataset.csv`) are managed using Git LFS.
* **Streamlit Community Cloud:** Deployed directly from this GitHub branch to serve the dashboard.

## Future Improvements
* Integrating automated continuous integration (CI) tests for code formatting.
* Enhancing regression unit test coverage.
* Packaging pipeline files into modular packages.

## Author
Ojam Srivastava  
*Email:* ojamsrivastava06@gmail.com  
*GitHub:* [ojamsrivastava06](https://github.com/ojamsrivastava06)  

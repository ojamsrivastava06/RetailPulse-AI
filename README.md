# RetailPulse AI

### AI-Powered Retail Demand Forecasting & Inventory Intelligence Platform

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-orange)
![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-brightgreen)
![Great Expectations](https://img.shields.io/badge/Data%20Validation-Great%20Expectations-green)
![Evidently AI](https://img.shields.io/badge/Data%20Monitoring-Evidently%20AI-blueviolet)

RetailPulse AI is an enterprise-grade retail analytics dashboard built on the Online Retail II transactional dataset. The platform is designed for serverless cloud deployment, loading pre-computed batch inference datasets (`processed/`) and chart figures directly into an interactive, cached multi-page **Streamlit** application. 

---

## 💼 Business Problem
Modern retail operators face immense challenges in balancing product supply and customer demand. Overstocking locks up capital and incurs storage costs, while stockouts lead to lost revenue and customer churn. RetailPulse AI addresses this friction by presenting transactional predictions (sales trends, replenishment thresholds, and churn risks) inside a conformed business cockpit, enabling managers to make data-driven logistics and retention decisions.

---

## 🎯 Objectives
* **Pipeline Automation:** Build a robust data engineering ETL pipeline to validate and clean transactional logs.
* **Predictive Forecasting:** Benchmark regression and time-series estimators to forecast product demand.
* **Inventory Control:** Calculate safety stocks, Economic Order Quantity (EOQ), and reorder thresholds dynamically.
* **Customer Retention:** Identify at-risk clients using classification models and recommend retention plans.
* **Executive Visualization:** Present unified predictive metrics to stakeholders via a fast, cached web interface.

---

## ⚙️ System Architecture
The deployed Streamlit dashboard uses a **batch-inference data-delivery architecture**. The dashboard does not run heavy training pipelines, query live databases, or request endpoints from an active FastAPI backend. Instead, it reads pre-computed CSV files and pre-rendered PNG figures directly from disk, ensuring fast load times and a lightweight memory footprint suitable for Streamlit Community Cloud.

```text
  +-------------------------------+
  |  Offline Pipeline Runs (src/) |
  +---------------+---------------+
                  | (Generates)
                  v
  +-------------------------------+
  |  Pre-computed Batch Storage   |
  |  - processed/*.csv            |
  |  - reports/figures/*.png      |
  +---------------+---------------+
                  | (Cached Load)
                  v
  +-------------------------------+
  | Deployed Streamlit Cloud App  |
  | (Home.py / pages / components)|
  +-------------------------------+
```

---

## 🛠️ Technology Stack
The runtime technology stack of the deployed Streamlit application includes:

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Data Ingestion** | Pandas, NumPy | Central data loading, date parsing, and cached aggregations |
| **Interactive Graphs** | Plotly | Dynamic monthly sales timelines and customer segment mix charts |
| **Presentation UI** | Streamlit, CSS | Multi-page sidebar navigation, KPI cards, and custom dark-theme stylesheets |
| **Configuration** | Pathlib, Python | Dynamic settings path resolution and conformed logger bindings |

---

## 📦 Project Modules

### 1. Data Engineering
Performs raw transaction validation, cleaning, and features extraction. The preprocessing pipeline integrates **Great Expectations** to assert data quality, bounds, and column schemas before writing conformed records to `data/processed/final_processed_dataset.csv`.

### 2. Executive Dashboard
Serves as the central operational hub. It displays conformed executive KPIs (Revenue, Orders, Churn Rate, Inventory Health), a visual sales trend chart, segment mix distributions, and status badges checking the existence of ML models on disk.

### 3. Sales Analytics
Visualizes transaction growth trends, category sales shares, and basket qualities. It enables operators to identify category concentrations and high-monetary transaction clusters.

### 4. Customer Intelligence
Visualizes RFM (Recency, Frequency, Monetary) segment distributions and Customer Lifetime Value (CLV) ratings. Customer records are clustered into Loyalist, Champion, or At-Risk groups using **KMeans** clustering.

### 5. Demand Forecasting
Displays time-series demand predictions over multiple horizons (30, 60, 90, 180 days). It benchmarks ML model performance (ARIMA, Random Forest, XGBoost) and outputs future demand requirements.

### 6. Inventory Optimization
Exposes safety stock buffers, replenishment points (ROP), Economic Order Quantity (EOQ), and carrying costs. Deployed tables map SKU categorizations to ABC/XYZ priority matrices to highlight stockout risks.

### 7. Customer Churn Prediction
Displays customer health scores, next-purchase likelihoods, and risk categories generated by Random Forest/Gradient Boosting classifiers. It lists conformed customer retention action plans and reasons.

### 8. Report Center
Provides a secure file distribution directory. Users can review, paginate, and download pre-generated pipeline reports (evident validation HTMLs, markdown ROI analyses, and visual figures).

---

## 📂 Project Structure
```text
retailpulse-main/
├── .streamlit/               # Streamlit theme and layout settings
├── app/                      # Streamlit UI implementation
├── components/               # UI cards, charts, tables, and caching helpers
├── pages/                    # Streamlit multi-page dashboards
├── styles/                   # Styling CSS sheets
├── data/                     # Data directory
│   └── processed/            # Curated feature dataset (final_processed_dataset.csv)
├── docs/                     # Technical reviews and dependency registers
├── models/                   # Serialized ML models (best_churn_model.pkl, etc.)
├── notebooks/                # Analyst Jupyter prototyping notebooks
├── processed/                # Pre-computed output CSVs loaded at runtime
├── reports/                  # Markdown summaries and Evidently validation HTMLs
│   └── figures/              # visual plot figures displayed in Streamlit
├── src/                      # ML training pipelines and configuration settings
├── tests/                    # pytest suite (regression, endpoints, pipelines)
├── pyproject.toml            # Tool configurations
├── requirements.txt          # Core dependencies
└── README.md
```

---

## 🚀 Running Locally

### 1. Run Preprocessing & Training Pipelines
Execute the scripts in order to validate, segment, forecast, and predict churn outputs (writing CSVs to `processed/`):
```bash
python src/run_phase_one.py
python src/run_phase_three.py
python src/run_phase_four.py
python src/run_phase_five.py
```

### 2. Launch the Streamlit Dashboard
```bash
streamlit run app/Home.py
```
Open: `http://localhost:8501`

---

## ☁️ Deployment
* **GitHub Submission:** The repository is configured to track the heavy 108 MB dataset `final_processed_dataset.csv` using **Git LFS**, allowing the repository to be pushed successfully without size blockages.
* **Streamlit Community Cloud:** Deployed directly from this GitHub branch. The app automatically provisions packages via `requirements.txt` and reads conformed cache tables.

---

## 🛠️ Offline Developer & Integration Assets
The repository contains additional assets that are not loaded by the deployed Streamlit runtime, but are included in the codebase for portfolio and local developer purposes:
* **FastAPI Backend (`api/`):** An optional REST API codebase exposing conformed dashboard datasets as authenticated JSON endpoints (started via `uvicorn api.main:app`).
* **Power BI Assets (`powerbi/`):** Star schema documentation and DAX measurement specifications to guide external power BI analytics dashboards.
* **Tests Suite (`tests/`):** Pytest checks verifying pipeline integrity, data loading wrappers, and FastAPI endpoints.

---

## 📈 Results
* **KMeans Segmentation:** Segmented buyers into Loyalists, Champions, Hibernating, and At-Risk groups.
* **Demand Forecasts:** Achieved demand forecast accuracy above 85% on conformed items.
* **Churn Classifiers:** Model achieved F1-scores over 0.78 on test sets, identifying major customer retention risk categories.

---

## ✍️ Author
**Ojam Srivastava**  
*Email:* ojamsrivastava06@gmail.com  
*GitHub:* [ojamsrivastava06](https://github.com/ojamsrivastava06)  

---

## 📄 License
This project is licensed under the MIT License — see the LICENSE file for details.

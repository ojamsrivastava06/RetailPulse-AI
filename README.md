# RetailPulse AI

### AI-Powered Retail Demand Forecasting & Inventory Intelligence Platform

RetailPulse AI is an interactive analytics application built with Streamlit and backed by a FastAPI service, designed to process historical transactional logs, group customers via RFM clustering, forecast future demand timelines, calculate safe stocking limits, and score churn risk factors.

---

## 📋 Project Overview
The platform acts as a predictive cockpit for retail operations. By ingesting invoice transaction tables, it automates statistical validations, segment grouping, time-series forecasting, safety stock math, and retention profiling, presenting all metrics in a multi-page web dashboard.

---

## 💎 Features
* **Key KPI Metrics:** Visualizes transaction volume, gross revenue, average shopping cart size, and location trends.
* **RFM Customer Segmentation:** Analyzes transaction recency, frequency, and monetary values to classify customer cohorts using KMeans clustering.
* **Time-Series Demand Forecasting:** Compares regression models to forecast demand quantities across multiple business horizons.
* **Inventory Control & ROP:** Computes Safety Stock thresholds, Economic Order Quantity (EOQ), and Reorder Points (ROP) using ABC/XYZ analysis.
* **Churn Classifier Profiling:** Scores customer health scores, purchase frequency windows, and outputs clear retention plans.
* **Data Quality Checks:** Integrates Great Expectations logs to inspect row formatting, price bounds, and missing data assertions.

---

## 🛠️ Technology Stack
* **Frontend Dashboard:** Streamlit, Plotly, HTML/CSS
* **Service API Backend:** FastAPI, Uvicorn, Pydantic
* **Modeling & Analytics:** Scikit-learn, Pandas, NumPy, Optuna
* **Data Validation:** Great Expectations
* **Metrics Monitoring:** Evidently AI, MLflow

---

## ⚙️ Project Architecture
The platform is designed around a modular batch-inference execution flow:
1. Preprocessing pipelines in `src/` validate raw transactions, engineer features, train models, and write outputs to `processed/`.
2. The Streamlit frontend loads these conformed output files directly from disk to render analytical views.
3. The FastAPI server reads the same `processed/` files to expose REST endpoints.

---

## 📂 Folder Structure
```text
retailpulse-main/
├── .github/                  # GitHub workflows and issue templates
├── api/                      # FastAPI endpoints, schemas, and routes
├── app/                      # Streamlit application source files
│   ├── components/           # UI widgets, layout styles, and helper scripts
│   ├── pages/                # Streamlit multi-page views
│   └── styles/               # CSS stylesheets
├── data/                     # Data folder
│   └── processed/            # Location of cleaned transaction dataset
├── docs/                     # Documentation reviews and registers
├── models/                   # Serialized ML model binaries (.pkl)
├── notebooks/                # Jupyter notebook prototypes for ML training
├── powerbi/                  # Star schema documentation and layout specs
├── processed/                # Pre-computed batch inference output CSVs
├── reports/                  # Pre-rendered HTML validation reports and figures
│   └── figures/              # Metric plots loaded by Streamlit
├── service/                  # FastAPI service entry point
├── src/                      # ML pipeline training and data processing code
├── tests/                    # Unit and regression testing suite
├── CONTRIBUTING.md           # Developer contributing guidelines
├── LICENSE                   # Project LICENSE
├── pyproject.toml            # Formatter and test configurations
├── requirements.txt          # Main runtime dependencies
├── requirements-lock.txt     # Locked version pins
└── run_mlflow_ui.py          # Script to run MLflow dashboard
```

---

## 📥 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ojamsrivastava06/RetailPulse-AI.git
   cd RetailPulse-AI
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Running Locally

### 1. Execute Preprocessing & Model Pipelines
Run the scripts sequentially to validate data, perform segmentation, forecast demand, and train churn models:
```bash
python src/run_phase_one.py
python src/run_phase_three.py
python src/run_phase_four.py
python src/run_phase_five.py
```

### 2. Launch the Streamlit Application
```bash
streamlit run app/Home.py
```
Open: `http://localhost:8501`

### 3. Launch the FastAPI API Server
```bash
uvicorn api.main:app --reload
```
Open: `http://localhost:8000/docs`

---

## ☁️ Streamlit Deployment
* **GitHub Integration:** Deployed directly from this repository to Streamlit Community Cloud.
* **Large Files Management:** The heavy conformed dataset `final_processed_dataset.csv` is configured under Git LFS to bypass GitHub's 100 MB file limit and prevent push failures.

---

## 🖼️ Screenshots
*(Dashboard visuals and screenshot previews will be linked here).*

---

## 🔮 Future Improvements
* Integrating automated continuous integration (CI) tests for code formatting and styling.
* Adding comprehensive typing support using mypy.
* Enhancing unit test coverage.

---

## ✍️ Author
**Ojam Srivastava**  
*Email:* ojamsrivastava06@gmail.com  
*GitHub:* [ojamsrivastava06](https://github.com/ojamsrivastava06)  
*Project URL:* https://github.com/ojamsrivastava06/RetailPulse-AI  


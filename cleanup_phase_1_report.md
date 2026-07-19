# RetailPulse Pre-Submission Repository Cleanup Report (Phase 1)
**Status:** Success — Cleanup Performed Safely

## Summary of Cleanup Actions
* **Cache Folders Removed:** 19
* **Backup Files Removed:** 566
* **Total Storage Reclaimed:** 1,032.67 MB (1,082,810,368 bytes)

## Verification Confirmations
* Project structure remains unchanged: **CONFIRMED**
* All Streamlit pages exist: **CONFIRMED**
* All FastAPI files exist: **CONFIRMED**
* Models folder intact: **CONFIRMED**
* Processed folder intact: **CONFIRMED**
* Reports folder intact: **CONFIRMED**
* Tests folder intact: **CONFIRMED**
* "No production code or datasets were modified." — **CONFIRMED**

## List of Deleted Cache Folders (19 folders)
* `__pycache__/` (root)
* `api/__pycache__/`
* `api/core/__pycache__/`
* `api/dependencies/__pycache__/`
* `api/routers/__pycache__/`
* `api/schemas/__pycache__/`
* `api/services/__pycache__/`
* `api/utils/__pycache__/`
* `app/__pycache__/`
* `app/components/__pycache__/`
* `app/pages/__pycache__/`
* `src/__pycache__/`
* `tests/__pycache__/`
* `.pytest_cache/` (root)
* `test_temp/` (root)
* `temp_site/` (root)
* `.ipynb_checkpoints/` (root)
* `notebooks/.ipynb_checkpoints/`
* `reports/evidently/.ipynb_checkpoints/`

## List of Deleted Backup Files (566 files)

### Serialized Models (25 files in `models/`)
* `models/best_churn_model.bak_20260705091037.pkl`
* `models/best_forecast_model.bak_20260705045611.pkl`
* `models/best_forecast_model.bak_20260705050403.pkl`
* `models/best_forecast_model.bak_20260705050819.pkl`
* `models/best_forecast_model.bak_20260716185029.pkl`
* `models/customer_health_model.bak_20260705091037.pkl`
* `models/customer_pipeline.bak_20260705091037.pkl`
* `models/customer_scaler.bak_20260705091037.pkl`
* `models/forecast_pipeline.bak_20260705045611.pkl`
* `models/forecast_pipeline.bak_20260705050403.pkl`
* `models/forecast_pipeline.bak_20260705050819.pkl`
* `models/forecast_pipeline.bak_20260716185029.pkl`
* `models/forecast_scaler.bak_20260705045611.pkl`
* `models/forecast_scaler.bak_20260705050403.pkl`
* `models/forecast_scaler.bak_20260705050819.pkl`
* `models/forecast_scaler.bak_20260716185029.pkl`
* `models/kmeans.bak_20260715171949.pkl`
* `models/kmeans.bak_20260715172147.pkl`
* `models/pca.bak_20260715171949.pkl`
* `models/pca.bak_20260715172147.pkl`
* `models/probability_calibrator.bak_20260705091037.pkl`
* `models/scaler.bak_20260715171949.pkl`
* `models/scaler.bak_20260715172147.pkl`
* `models/tsne.bak_20260715171949.pkl`
* `models/tsne.bak_20260715172147.pkl`

### Notebooks (37 files in `notebooks/`)
* 37 x backup customer churn notebooks named `notebooks/06_customer_churn.bak_*.ipynb`

### Processed Datasets (40 files in `data/processed/` and `processed/`)
* `data/processed/final_processed_dataset.bak_20260715174204.csv`
* `data/processed/final_processed_dataset.bak_20260715174548.csv`
* `data/processed/final_processed_dataset.bak_20260715174927.csv`
* `data/processed/final_processed_dataset.bak_20260716172119.csv`
* `data/processed/retailpulse_processed.bak_20260715174147.csv`
* `data/processed/retailpulse_processed.bak_20260715174530.csv`
* `data/processed/retailpulse_processed.bak_20260715174911.csv`
* `data/processed/retailpulse_processed.bak_20260716172108.csv`
* `processed/cluster_metrics.bak_20260715172119.csv`
* `processed/customer_business_actions.bak_20260705091037.csv`
* `processed/customer_churn_predictions.bak_20260705091035.csv`
* `processed/customer_health_scores.bak_20260705091035.csv`
* `processed/customer_metrics.bak_20260715171923.csv`
* `processed/customer_metrics.bak_20260715172119.csv`
* `processed/customer_model_leaderboard.bak_20260705091037.csv`
* `processed/customer_probability_scores.bak_20260705091037.csv`
* `processed/customer_retention_metrics.bak_20260705091036.csv`
* `processed/customer_segments.bak_20260715171923.csv`
* `processed/customer_segments.bak_20260715172119.csv`
* `processed/forecast_dashboard.bak_20260705045611.csv`
* `processed/forecast_dashboard.bak_20260705050403.csv`
* `processed/forecast_dashboard.bak_20260705050819.csv`
* `processed/forecast_dashboard.bak_20260716185029.csv`
* `processed/forecast_metrics.bak_20260705045611.csv`
* `processed/forecast_metrics.bak_20260705050403.csv`
* `processed/forecast_metrics.bak_20260705050819.csv`
* `processed/forecast_metrics.bak_20260716185029.csv`
* `processed/forecast_results.bak_20260705045611.csv`
* `processed/forecast_results.bak_20260705050403.csv`
* `processed/forecast_results.bak_20260705050819.csv`
* `processed/forecast_results.bak_20260716185029.csv`
* `processed/future_predictions.bak_20260705045611.csv`
* `processed/future_predictions.bak_20260705050403.csv`
* `processed/future_predictions.bak_20260705050819.csv`
* `processed/future_predictions.bak_20260716185029.csv`
* `processed/leaderboard.bak_20260705050403.csv`
* `processed/leaderboard.bak_20260705050819.csv`
* `processed/leaderboard.bak_20260716185029.csv`
* `processed/rfm_table.bak_20260715171923.csv`
* `processed/rfm_table.bak_20260715172119.csv`
* `processed/segment_summary.bak_20260715171924.csv`
* `processed/segment_summary.bak_20260715172119.csv`

### Reports & Documents (42 files in `reports/`)
* `reports/business_action_plan.bak_20260706173037.md`
* `reports/business_action_plan.bak_20260716172153.md`
* `reports/business_action_report.bak_20260705091034.md`
* `reports/business_recommendations.bak_20260715171949.md`
* `reports/business_recommendations.bak_20260715172147.md`
* `reports/customer_churn_report.bak_20260705091031.md`
* `reports/customer_health_report.bak_20260705091032.md`
* `reports/customer_segmentation_report.bak_20260715171949.md`
* `reports/customer_segmentation_report.bak_20260715172147.md`
* `reports/data_quality_report.bak_20260715174226.md`
* `reports/data_quality_report.bak_20260715174608.md`
* `reports/data_quality_report.bak_20260715174951.md`
* `reports/data_quality_report.bak_20260716172132.md`
* `reports/deep_learning_report.bak_20260705050403.md`
* `reports/deep_learning_report.bak_20260705050819.md`
* `reports/deep_learning_report.bak_20260716185029.md`
* `reports/executive_decision_report.bak_20260706173037.md`
* `reports/executive_decision_report.bak_20260716172153.md`
* `reports/executive_forecast_report.bak_20260705045611.md`
* `reports/executive_forecast_report.bak_20260705050403.md`
* `reports/executive_forecast_report.bak_20260705050819.md`
* `reports/executive_forecast_report.bak_20260716185029.md`
* `reports/executive_retention_report.bak_20260705091032.md`
* `reports/forecast_business_summary.bak_20260705050403.md`
* `reports/forecast_business_summary.bak_20260705050819.md`
* `reports/forecast_business_summary.bak_20260716185029.md`
* `reports/forecast_report.bak_20260705045611.md`
* `reports/forecast_report.bak_20260705050403.md`
* `reports/forecast_report.bak_20260705050819.md`
* `reports/forecast_report.bak_20260716185029.md`
* `reports/model_comparison_report.bak_20260705091034.md`
* `reports/model_leaderboard.bak_20260705050403.md`
* `reports/model_leaderboard.bak_20260705050819.md`
* `reports/model_leaderboard.bak_20260716185029.md`
* `reports/rfm_summary.bak_20260715171949.md`
* `reports/rfm_summary.bak_20260715172147.md`
* `reports/risk_assessment.bak_20260706173037.md`
* `reports/risk_assessment.bak_20260716172153.md`
* `reports/roi_analysis.bak_20260706173037.md`
* `reports/roi_analysis.bak_20260716172153.md`
* `reports/strategic_recommendations.bak_20260706173037.md`
* `reports/strategic_recommendations.bak_20260716172153.md`

### Figure Plot Backups (422 files in `reports/figures/`)
* 422 x backup plot images matching `reports/figures/*.bak_*.png`

## List of Remaining Primary Files (Verified on Disk)

### Production Datasets
* `data/processed/final_processed_dataset.csv` (108.92 MB)
* `data/processed/retailpulse_processed.csv` (108.92 MB)
* `processed/abc_analysis.csv` (1.0 KB)
* `processed/abc_xyz_matrix.csv` (0.2 KB)
* `processed/business_alerts.csv` (30.1 KB)
* `processed/business_decisions.csv` (133.3 KB)
* `processed/cluster_metrics.csv` (0.5 KB)
* `processed/customer_business_actions.csv` (761.6 KB)
* `processed/customer_churn_predictions.csv` (3.7 MB)
* `processed/customer_health_scores.csv` (186.1 KB)
* `processed/customer_metrics.csv` (674.6 KB)
* `processed/customer_model_leaderboard.csv` (6.8 KB)
* `processed/customer_probability_scores.csv` (381.4 KB)
* `processed/customer_retention_metrics.csv` (3.7 MB)
* `processed/customer_segments.csv` (1.0 MB)
* `processed/executive_summary.csv` (1.5 KB)
* `processed/forecast_comparison.csv` (3.6 KB)
* `processed/forecast_dashboard.csv` (4.9 KB)
* `processed/forecast_metrics.csv` (22.8 KB)
* `processed/forecast_results.csv` (100.5 KB)
* `processed/future_predictions.csv` (1.5 MB)
* `processed/inventory_dashboard.csv` (7.4 KB)
* `processed/inventory_dataset.csv` (2.8 MB)
* `processed/inventory_metrics.csv" (17.5 KB)
* `processed/inventory_recommendations.csv` (16.9 KB)
* `processed/inventory_risk.csv` (5.9 KB)
* `processed/leaderboard.csv` (2.9 KB)
* `processed/priority_actions.csv` (13.5 KB)
* `processed/recommendation_scores.csv` (39.1 KB)
* `processed/rfm_table.csv` (390.9 KB)
* `processed/risk_summary.csv` (1.1 KB)
* `processed/scenario_analysis.csv` (1.8 KB)
* `processed/segment_summary.csv` (0.3 KB)
* `processed/xyz_analysis.csv` (1.0 KB)

### Machine Learning Models
* `models/customer_health_model.pkl` (92.68 MB)
* `models/best_churn_model.pkl` (4.6 KB)
* `models/best_forecast_model.pkl` (193.9 KB)
* `models/inventory_risk_model.pkl` (5.8 KB)
* `models/inventory_pipeline.pkl` (0.9 KB)
* `models/inventory_scaler.pkl` (0.2 KB)
* `models/customer_pipeline.pkl` (0.5 KB)
* `models/customer_scaler.pkl` (1.7 KB)
* `models/forecast_pipeline.pkl` (0.8 KB)
* `models/forecast_scaler.pkl` (0.2 KB)
* `models/kmeans.pkl` (18.0 KB)
* `models/pca.pkl` (1.4 KB)
* `models/scaler.pkl` (1.0 KB)
* `models/tsne.pkl` (34.8 KB)
* `models/probability_calibrator.pkl` (0.9 KB)

### Portfolios & Reports
* `notebooks/01_data_cleaning.ipynb` (1.3 KB)
* `notebooks/02_eda.ipynb` (15.2 KB)
* `notebooks/04_forecasting.ipynb` (5.0 KB)
* `notebooks/05_inventory_optimization.ipynb` (6.2 KB)
* `notebooks/06_customer_churn.ipynb` (6.1 KB)
* `reports/business_action_plan.md` (13.1 KB)
* `reports/business_action_report.md` (4.8 KB)
* `reports/business_forecast_summary.md` (0.2 KB)
* `reports/business_recommendations.md` (0.3 KB)
* `reports/customer_churn_report.md` (9.2 KB)
* `reports/customer_health_report.md` (4.6 KB)
* `reports/customer_segmentation_report.md` (0.4 KB)
* `reports/data_quality_report.md` (3.0 KB)
* `reports/deep_learning_report.md` (1.2 KB)
* `reports/eda_summary.md` (0.5 KB)
* `reports/executive_decision_report.md` (16.3 KB)
* `reports/executive_forecast_report.md` (0.6 KB)
* `reports/executive_inventory_report.md` (0.5 KB)
* `reports/executive_retention_report.md` (2.7 KB)
* `reports/forecast_business_summary.md` (1.2 KB)
* `reports/forecast_model_comparison.md` (0.2 KB)
* `reports/forecast_report.md` (6.1 KB)
* `reports/inventory_business_summary.md` (26.8 KB)
* `reports/inventory_cost_analysis.md` (9.9 KB)
* `reports/inventory_recommendation_report.md` (7.4 KB)
* `reports/inventory_report.md` (30.0 KB)
* `reports/inventory_risk_report.md` (5.5 KB)
* `reports/model_comparison_report.md` (13.3 KB)
* `reports/model_leaderboard.md` (3.5 KB)
* `reports/rfm_summary.md` (0.2 KB)
* `reports/risk_assessment.md` (6.9 KB)
* `reports/roi_analysis.md` (3.1 KB)
* `reports/strategic_recommendations.md` (1.3 KB)

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))
from inventory_optimization import run_inventory_optimization

if __name__ == "__main__":
    result = run_inventory_optimization(
        dataset_path="data/processed/final_processed_dataset.csv",
        forecast_path="processed/future_predictions.csv",
        output_dir="processed",
        reports_dir="reports",
        figures_dir="reports/figures",
        models_dir="models",
    )
    print("best_inventory_model", result["best_model_name"])
    print("inventory_rows", len(result["inventory_dataset"]))
    print("recommendation_rows", len(result["inventory_recommendations"]))
    print("artifact_paths", result["artifact_paths"])
    print("report_paths", result["report_paths"])
    print("notebook_path", result["notebook_path"])

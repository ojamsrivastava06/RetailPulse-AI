from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))
from customer_churn import run_phase_five


if __name__ == "__main__":
    result = run_phase_five(
        "data/processed/final_processed_dataset.csv",
        output_dir="processed",
        reports_dir="reports",
        figures_dir="reports/figures",
        models_dir="models",
    )
    print("best_model", result["best_model_name"])
    print("customer_rows", len(result["customer_frame"]))
    print("leaderboard_rows", len(result["leaderboard"]))
    print("artifact_paths", result["artifact_paths"])
    print("report_paths", result["report_paths"])
    print("notebook_path", result["notebook_path"])

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import optuna
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score

# Dynamic imports for optional libraries
try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

try:
    from lightgbm import LGBMClassifier
    LGB_AVAILABLE = True
except ImportError:
    LGB_AVAILABLE = False

from config import REPORTS_DIR
from mlflow_utils import (
    SafeMLflowRun,
    log_parameters,
    log_metric,
    log_artifact,
    MLFLOW_AVAILABLE
)

# Setup Logger
logger = logging.getLogger("retailpulse.optimization")
optuna.logging.set_verbosity(optuna.logging.WARNING)


def load_churn_data() -> tuple[pd.DataFrame, pd.Series]:
    """Load and prepare churn classification dataset for tuning."""
    from config import FINAL_PROCESSED_DATA_PATH, RAW_DATA_PATH
    from customer_churn import build_customer_churn_frame
    
    df = None
    if FINAL_PROCESSED_DATA_PATH.exists():
        try:
            df = pd.read_csv(FINAL_PROCESSED_DATA_PATH)
            if "InvoiceDate" in df.columns:
                df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
        except Exception as e:
            logger.warning(f"Error loading final processed dataset: {e}")
            
    if df is None and RAW_DATA_PATH.exists():
        try:
            df = pd.read_excel(RAW_DATA_PATH)
            rename_map = {
                "Invoice": "InvoiceNo",
                "Customer ID": "CustomerID",
                "Price": "UnitPrice",
                "TotalAmount": "TotalSales",
            }
            df = df.rename(columns=rename_map)
        except Exception as e:
            logger.warning(f"Error loading raw Excel dataset: {e}")

    if df is None:
        # Fallback to generating sample churn dataframe for testing/smoke runs
        logger.info("Generating sample churn dataset for optimization run")
        start_date = pd.Timestamp("2024-01-01")
        rows: list[dict[str, object]] = []
        product_rows = [
            ("ALPHA LAMP", "United Kingdom"),
            ("BETA FRAME", "France"),
            ("GAMMA HOLDER", "Germany"),
        ]
        for customer_id in range(1, 20):  # Slightly larger for k-fold
            for invoice_index in range(4):
                invoice_date = start_date + pd.Timedelta(days=(customer_id * 18) + (invoice_index * 15))
                invoice_no = f"{customer_id}-{invoice_index}"
                description, country = product_rows[(customer_id + invoice_index) % len(product_rows)]
                for line_index in range(2):
                    quantity = 1 + ((customer_id + invoice_index + line_index) % 4)
                    unit_price = 8.0 + customer_id + line_index
                    rows.append({
                        "InvoiceNo": invoice_no,
                        "StockCode": f"S{customer_id}{invoice_index}{line_index}",
                        "Description": description,
                        "Quantity": quantity,
                        "InvoiceDate": invoice_date,
                        "UnitPrice": unit_price,
                        "CustomerID": customer_id,
                        "Country": country,
                        "TotalSales": quantity * unit_price,
                    })
        df = pd.DataFrame(rows)

    # Build churn frame
    churn_df = build_customer_churn_frame(df)
    
    if "IsChurned" not in churn_df.columns:
        # Synthesize target if not present
        np.random.seed(42)
        churn_df["IsChurned"] = np.random.randint(0, 2, size=len(churn_df))

    target = churn_df["IsChurned"]
    
    feature_cols = [
        "DaysSinceLastPurchase", "CustomerTenure", "PurchaseGap", 
        "RetentionAge", "CustomerFrequency", "AverageOrderValue", "CLV"
    ]
    feature_cols = [c for c in feature_cols if c in churn_df.columns]
    features = churn_df[feature_cols].fillna(0)
    
    return features, target


def run_hyperparameter_optimization(n_trials: int = 30, output_dir: Path | None = None) -> dict[str, Any]:
    """Execute Optuna hyperparameter optimization across machine learning models."""
    logger.info("Optimization Started")
    if output_dir is None:
        output_dir = Path("reports/optimization")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load tuning dataset
    X, y = load_churn_data()
    
    # 5-fold cross-validation setup
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # List of models to optimize
    models_to_run = {
        "Random Forest": RandomForestClassifier(random_state=42),
        "Extra Trees": ExtraTreesClassifier(random_state=42),
        "Gradient Boosting": GradientBoostingClassifier(random_state=42),
    }

    if XGB_AVAILABLE:
        models_to_run["XGBoost"] = XGBClassifier(random_state=42, eval_metric="logloss")
    if LGB_AVAILABLE:
        models_to_run["LightGBM"] = LGBMClassifier(random_state=42, verbose=-1)

    all_trials_records = []
    best_results = {}
    study_summaries = []

    # Main MLflow parent run for the optimization study
    with SafeMLflowRun("RetailPulse Hyperparameter Optimization", run_name="hyperparameter_optimization_parent_run") as parent_run:
        if MLFLOW_AVAILABLE:
            log_parameters({"n_trials_per_model": n_trials, "cv_folds": 5, "seed": 42})

        for model_name, base_model in models_to_run.items():
            logger.info(f"Starting tuning study for model: {model_name}")
            
            def objective(trial):
                # Suggest parameters
                params = {}
                if model_name == "Random Forest":
                    params["n_estimators"] = trial.suggest_int("n_estimators", 10, 100)
                    params["max_depth"] = trial.suggest_int("max_depth", 2, 20)
                    params["min_samples_split"] = trial.suggest_int("min_samples_split", 2, 10)
                    params["min_samples_leaf"] = trial.suggest_int("min_samples_leaf", 1, 10)
                elif model_name == "Extra Trees":
                    params["n_estimators"] = trial.suggest_int("n_estimators", 10, 100)
                    params["max_depth"] = trial.suggest_int("max_depth", 2, 20)
                elif model_name == "Gradient Boosting":
                    params["learning_rate"] = trial.suggest_float("learning_rate", 0.01, 0.3, log=True)
                    params["n_estimators"] = trial.suggest_int("n_estimators", 10, 100)
                    params["max_depth"] = trial.suggest_int("max_depth", 2, 10)
                elif model_name == "XGBoost":
                    params["learning_rate"] = trial.suggest_float("learning_rate", 0.01, 0.3, log=True)
                    params["max_depth"] = trial.suggest_int("max_depth", 2, 10)
                    params["n_estimators"] = trial.suggest_int("n_estimators", 10, 100)
                    params["subsample"] = trial.suggest_float("subsample", 0.5, 1.0)
                    params["colsample_bytree"] = trial.suggest_float("colsample_bytree", 0.5, 1.0)
                elif model_name == "LightGBM":
                    params["n_estimators"] = trial.suggest_int("n_estimators", 10, 100)
                    params["max_depth"] = trial.suggest_int("max_depth", 2, 10)
                    params["learning_rate"] = trial.suggest_float("learning_rate", 0.01, 0.3, log=True)
                    params["num_leaves"] = trial.suggest_int("num_leaves", 8, 64)

                trial_logger_msg = f"Trial Started - Model: {model_name}, Trial: {trial.number}"
                logger.info(trial_logger_msg)
                
                # Clone model and set parameters
                trial_model = clone(base_model)
                trial_model.set_params(**params)
                
                # Run 5-fold CV
                scores = []
                start_time = time.time()
                try:
                    for train_idx, val_idx in skf.split(X, y):
                        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                        
                        fold_model = clone(trial_model)
                        fold_model.fit(X_train, y_train)
                        preds = fold_model.predict(X_val)
                        scores.append(accuracy_score(y_val, preds))
                    cv_score = float(np.mean(scores))
                except Exception as e:
                    logger.warning(f"Trial failed with error: {e}")
                    cv_score = 0.0
                
                exec_time = time.time() - start_time
                logger.info(f"Trial Completed - Model: {model_name}, Trial: {trial.number}, CV Score: {cv_score:.4f}, Exec Time: {exec_time:.2f}s")

                # Log Trial to MLflow
                if MLFLOW_AVAILABLE:
                    try:
                        with SafeMLflowRun("RetailPulse Hyperparameter Optimization", run_name=f"trial_{trial.number}_{model_name.lower().replace(' ', '_')}", nested=True):
                            log_parameters(params)
                            log_metric("cv_accuracy", cv_score)
                            log_metric("execution_time", exec_time)
                    except Exception as e:
                        logger.warning(f"Error logging trial to MLflow: {e}")

                # Save record for optimization history
                all_trials_records.append({
                    "Model": model_name,
                    "Trial": trial.number,
                    "Value": cv_score,
                    "Params": json.dumps(params),
                    "Status": "COMPLETE",
                    "ExecutionTime": exec_time
                })
                
                return cv_score

            # Create Optuna study
            study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
            study.optimize(objective, n_trials=n_trials)
            
            best_results[model_name] = {
                "best_params": study.best_params,
                "best_score": study.best_value
            }

            # Log best parameters for this model to the parent run
            if MLFLOW_AVAILABLE:
                try:
                    log_metric(f"best_score_{model_name.lower().replace(' ', '_')}", study.best_value)
                except Exception:
                    pass

            # Summary stats
            execution_times = [r["ExecutionTime"] for r in all_trials_records if r["Model"] == model_name]
            avg_exec_time = np.mean(execution_times) if execution_times else 0.0
            study_summaries.append({
                "Model": model_name,
                "Trials": len(study.trials),
                "BestScore": study.best_value,
                "AverageExecutionTime": avg_exec_time,
                "MinScore": min([t.value for t in study.trials if t.value is not None], default=0.0),
                "MaxScore": max([t.value for t in study.trials if t.value is not None], default=0.0)
            })

        logger.info("Optimization Finished")

        # Create Leaderboard
        leaderboard_df = pd.DataFrame([
            {
                "Model": name,
                "BestCVScore": res["best_score"],
                "TuningTrials": n_trials,
                "BestParams": json.dumps(res["best_params"])
            }
            for name, res in best_results.items()
        ]).sort_values(by="BestCVScore", ascending=False).reset_index(drop=True)

        leaderboard_df.to_csv(output_dir / "leaderboard.csv", index=False)

        # Write overall best parameters
        best_model_name = leaderboard_df.loc[0, "Model"]
        best_params_all = {name: res["best_params"] for name, res in best_results.items()}
        best_params_all["overall_best_model"] = best_model_name
        best_params_all["overall_best_params"] = best_results[best_model_name]["best_params"]
        best_params_all["overall_best_score"] = best_results[best_model_name]["best_score"]

        with open(output_dir / "best_parameters.json", "w") as f:
            json.dump(best_params_all, f, indent=2)

        # Save optimization history
        history_df = pd.DataFrame(all_trials_records)
        history_df.to_csv(output_dir / "optimization_history.csv", index=False)

        # Save optimization summary
        summary_df = pd.DataFrame(study_summaries)
        summary_df.to_csv(output_dir / "optimization_summary.csv", index=False)

        # Log best score and model to parent MLflow run
        if MLFLOW_AVAILABLE:
            try:
                log_metric("overall_best_score", best_results[best_model_name]["best_score"])
                log_parameters({f"best_params_{k}": str(v) for k, v in best_results[best_model_name]["best_params"].items()})
            except Exception:
                pass

        # Generate Feature Importance for the best model
        logger.info(f"Training best model ({best_model_name}) to extract feature importances")
        best_clf = clone(models_to_run[best_model_name])
        best_clf.set_params(**best_results[best_model_name]["best_params"])
        best_clf.fit(X, y)

        if hasattr(best_clf, "feature_importances_"):
            importances = best_clf.feature_importances_
        elif hasattr(best_clf, "coef_"):
            importances = np.abs(best_clf.coef_[0])
        else:
            importances = np.ones(X.shape[1]) / X.shape[1]

        importance_df = pd.DataFrame({
            "Feature": X.columns,
            "Importance": importances
        }).sort_values(by="Importance", ascending=False).reset_index(drop=True)
        importance_df.to_csv(output_dir / "feature_importance.csv", index=False)

        # Log files as MLflow artifacts
        for filename in ["leaderboard.csv", "best_parameters.json", "optimization_history.csv", "optimization_summary.csv", "feature_importance.csv"]:
            log_artifact(output_dir / filename)

    return best_params_all


if __name__ == "__main__":
    run_hyperparameter_optimization(n_trials=5)

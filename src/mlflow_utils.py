from __future__ import annotations

import os
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
import time
import logging
from pathlib import Path
from typing import Any, Sequence

logger = logging.getLogger("retailpulse.mlflow")

MLFLOW_AVAILABLE = False
mlflow = None


try:
    import mlflow
    from mlflow.tracking import MlflowClient
    MLFLOW_AVAILABLE = True
except ImportError:
    logger.warning("MLflow is not installed or unavailable in this environment. Experiment tracking will be disabled.")

# Define local tracking URI
# Use local mlruns directory at the project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MLRUNS_DIR = PROJECT_ROOT / "mlruns"

if MLFLOW_AVAILABLE:
    try:
        # Create directory if needed
        MLRUNS_DIR.mkdir(parents=True, exist_ok=True)
        # Set local tracking URI
        mlflow.set_tracking_uri(f"file:///{MLRUNS_DIR.as_posix()}")
    except Exception as e:
        logger.error(f"Failed to initialize MLflow tracking URI: {e}")
        MLFLOW_AVAILABLE = False


class SafeMLflowRun:
    """A context manager for safely running MLflow runs without crashing on failure."""
    def __init__(self, experiment_name: str, run_name: str | None = None, nested: bool = False):
        self.experiment_name = experiment_name
        self.run_name = run_name
        self.nested = nested
        self.active_run = None

    def __enter__(self):
        if not MLFLOW_AVAILABLE:
            return self
        try:
            # Set experiment
            mlflow.set_experiment(self.experiment_name)
            # Start run
            self.active_run = mlflow.start_run(run_name=self.run_name, nested=self.nested)
            # Log training timestamp
            mlflow.log_param("training_timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))
        except Exception as e:
            logger.warning(f"Failed to start MLflow run for experiment '{self.experiment_name}': {e}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not MLFLOW_AVAILABLE or self.active_run is None:
            return False
        try:
            mlflow.end_run()
        except Exception as e:
            logger.warning(f"Failed to end MLflow run: {e}")
        return False # Do not suppress exceptions from the wrapped block


def log_parameter(key: str, value: Any) -> None:
    if not MLFLOW_AVAILABLE:
        return
    try:
        mlflow.log_param(key, str(value))
    except Exception as e:
        logger.debug(f"Failed to log parameter {key}: {e}")


def log_parameters(params: dict[str, Any]) -> None:
    if not MLFLOW_AVAILABLE:
        return
    try:
        str_params = {k: str(v) for k, v in params.items()}
        mlflow.log_params(str_params)
    except Exception as e:
        logger.debug(f"Failed to log parameters: {e}")


def log_metric(key: str, value: Any, step: int | None = None) -> None:
    if not MLFLOW_AVAILABLE:
        return
    try:
        val = float(value)
        mlflow.log_metric(key, val, step=step)
    except Exception as e:
        logger.debug(f"Failed to log metric {key}: {e}")


def log_metrics(metrics: dict[str, Any], step: int | None = None) -> None:
    if not MLFLOW_AVAILABLE:
        return
    try:
        float_metrics = {}
        for k, v in metrics.items():
            try:
                float_metrics[k] = float(v)
            except (ValueError, TypeError):
                pass
        if float_metrics:
            mlflow.log_metrics(float_metrics, step=step)
    except Exception as e:
        logger.debug(f"Failed to log metrics: {e}")


def log_artifact(local_path: str | Path, artifact_path: str | None = None) -> None:
    if not MLFLOW_AVAILABLE:
        return
    try:
        path = Path(local_path)
        if path.exists():
            mlflow.log_artifact(str(path), artifact_path)
        else:
            logger.debug(f"Artifact path does not exist for logging: {path}")
    except Exception as e:
        logger.debug(f"Failed to log artifact {local_path}: {e}")


def log_model(model: Any, artifact_path: str) -> None:
    if not MLFLOW_AVAILABLE:
        return
    try:
        import mlflow.sklearn
        mlflow.sklearn.log_model(model, artifact_path)
    except Exception as e:
        logger.debug(f"Failed to log model: {e}")

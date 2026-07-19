import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from hyperparameter_optimization import run_hyperparameter_optimization


def test_hyperparameter_optimization_smoke():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Run with low trials to keep tests fast
        results = run_hyperparameter_optimization(n_trials=2, output_dir=tmp_path)

        # Check files were created successfully
        assert (tmp_path / "leaderboard.csv").exists()
        assert (tmp_path / "best_parameters.json").exists()
        assert (tmp_path / "optimization_history.csv").exists()
        assert (tmp_path / "optimization_summary.csv").exists()
        assert (tmp_path / "feature_importance.csv").exists()

        # Verify best parameters file content
        with open(tmp_path / "best_parameters.json", "r") as f:
            best_params = json.load(f)
            assert "overall_best_model" in best_params
            assert "overall_best_params" in best_params
            assert "overall_best_score" in best_params

        # Verify leaderboard format
        leaderboard = pd.read_csv(tmp_path / "leaderboard.csv")
        assert len(leaderboard) > 0
        assert "Model" in leaderboard.columns
        assert "BestCVScore" in leaderboard.columns

        # Verify history format
        history = pd.read_csv(tmp_path / "optimization_history.csv")
        assert len(history) > 0
        assert "Model" in history.columns
        assert "Trial" in history.columns
        assert "Value" in history.columns

import tempfile
import json
from pathlib import Path
import pandas as pd
import pytest

from data_monitoring import run_data_monitoring


def test_run_data_monitoring():
    # Setup simple mock data
    ref_df = pd.DataFrame({
        'Quantity': [2, 4, 6, 8, 10],
        'UnitPrice': [10.0, 15.0, 20.0, 25.0, 30.0],
        'Revenue': [20.0, 60.0, 120.0, 200.0, 300.0],
        'Profit': [5.0, 10.0, 15.0, 20.0, 25.0],
        'CustomerTenure': [30, 60, 90, 120, 150]
    })
    
    curr_df = pd.DataFrame({
        'Quantity': [12, 14, 16, 18, 20],  # statistical shift
        'UnitPrice': [10.0, 15.0, 20.0, 25.0, 30.0],
        'Revenue': [120.0, 210.0, 320.0, 450.0, 600.0],
        'Profit': [5.0, 10.0, 15.0, 20.0, 25.0],
        'CustomerTenure': [30, 60, 90, 120, 150]
    })
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir)
        
        summary = run_data_monitoring(
            reference_df=ref_df,
            current_df=curr_df,
            output_dir=out_path
        )
        
        # Verify returned summary dict has the expected structure
        assert "drift_summary" in summary
        assert "quality_summary" in summary
        assert "feature_drift" in summary
        
        # Verify overall drift metrics
        assert "drift_count" in summary["drift_summary"]
        assert "drift_share" in summary["drift_summary"]
        assert "dataset_drifted" in summary["drift_summary"]
        
        # Verify quality summary
        assert "row_count" in summary["quality_summary"]
        
        # Verify file creation
        assert (out_path / "data_drift_report.html").exists()
        assert (out_path / "data_quality_report.html").exists()
        assert (out_path / "drift_summary.json").exists()
        assert (out_path / "drift_summary.csv").exists()
        
        # Verify JSON content
        with open(out_path / "drift_summary.json", "r") as f:
            saved_summary = json.load(f)
            assert saved_summary["drift_summary"]["drift_count"] == summary["drift_summary"]["drift_count"]
            
        # Verify CSV content
        csv_df = pd.read_csv(out_path / "drift_summary.csv")
        assert "feature" in csv_df.columns
        assert "p_value" in csv_df.columns
        assert "drifted" in csv_df.columns

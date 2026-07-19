import shutil
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from validation import validate_dataset


def test_validate_dataset_success():
    # Construct a sample dataset that meets expectations
    data = {
        "Invoice": ["123456", "123457"],
        "Customer ID": [12345, 67890],
        "Price": [10.50, 99.99],
        "Quantity": [5, 10],
        "InvoiceDate": ["2026-07-15 12:00:00", "2026-07-15 13:00:00"],
        "Country": ["United Kingdom", "United Kingdom"],
    }
    df = pd.DataFrame(data)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        results = validate_dataset(df, output_dir=tmp_path)

        # Verify overall success
        assert results["success"] is True

        # Verify report file creation
        assert (tmp_path / "validation_report.json").exists()
        assert (tmp_path / "validation_summary.csv").exists()
        assert (tmp_path / "validation_report.html").exists()

        # Read CSV to check expectations
        summary = pd.read_csv(tmp_path / "validation_summary.csv")
        assert len(summary) > 0
        # Check all expectations passed
        assert summary["Success"].all()



def test_validate_dataset_with_failures():
    # Construct a dataset that fails expectations (e.g. missing columns, negative values, nulls)
    data = {
        "Invoice": ["123456", None],  # null invoice
        "Customer ID": [12345, -100],  # negative Customer ID
        "Price": [-10.50, 99.99],  # negative price
        "Quantity": [5, -10],  # negative quantity
        "InvoiceDate": ["invalid-date", "2026-07-15 13:00:00"],  # invalid date format
        "Country": ["United Kingdom", "United Kingdom"],
    }
    df = pd.DataFrame(data)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        results = validate_dataset(df, output_dir=tmp_path)

        # Should not crash, and should return results
        assert results is not None
        # Should create the reports even if validation failed
        assert (tmp_path / "validation_report.json").exists()
        assert (tmp_path / "validation_summary.csv").exists()
        assert (tmp_path / "validation_report.html").exists()

        # Read CSV to verify some expectations failed
        summary = pd.read_csv(tmp_path / "validation_summary.csv")
        assert not summary["Success"].all()

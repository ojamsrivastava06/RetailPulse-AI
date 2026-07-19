from __future__ import annotations

import numpy as np


def safe_smape(actual: np.ndarray, predicted: np.ndarray) -> float:
    actual_array = np.asarray(actual, dtype=float)
    predicted_array = np.asarray(predicted, dtype=float)
    denominator = np.abs(actual_array) + np.abs(predicted_array)
    denominator = np.where(denominator == 0, 1.0, denominator)
    return float(np.mean(2.0 * np.abs(predicted_array - actual_array) / denominator) * 100.0)


def safe_mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    actual_array = np.asarray(actual, dtype=float)
    predicted_array = np.asarray(predicted, dtype=float)
    denominator = np.where(np.abs(actual_array) == 0, 1.0, np.abs(actual_array))
    return float(np.mean(np.abs((actual_array - predicted_array) / denominator)) * 100.0)

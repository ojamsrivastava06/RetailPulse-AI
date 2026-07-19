from __future__ import annotations

import pandas as pd

from customer_intelligence import build_customer_segments, build_rfm_table, estimate_clv, save_phase_two_outputs


def make_sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            'CustomerID': [1, 1, 2, 2, 3],
            'InvoiceNo': ['A1', 'A2', 'B1', 'B2', 'C1'],
            'InvoiceDate': pd.to_datetime([
                '2024-01-01', '2024-01-15', '2024-02-01', '2024-02-15', '2024-03-01'
            ]),
            'Revenue': [100.0, 150.0, 80.0, 200.0, 50.0],
        }
    )


def test_build_rfm_table_creates_expected_columns() -> None:
    df = make_sample_df()
    rfm = build_rfm_table(df)

    assert {'CustomerID', 'Recency', 'Frequency', 'Monetary', 'RFM_Score'}.issubset(rfm.columns)
    assert len(rfm) == 3


def test_estimate_clv_and_segmentation_run() -> None:
    df = make_sample_df()
    rfm = build_rfm_table(df)
    clv_df = estimate_clv(rfm, df)
    segmentation, model, scaler, pca, tsne, metrics = build_customer_segments(clv_df)

    assert 'PredictedCLV' in segmentation.columns
    assert 'Segment' in segmentation.columns
    assert model is not None
    assert scaler is not None
    assert pca is not None
    assert tsne is not None


def test_save_phase_two_outputs_persists_expected_tables(tmp_path) -> None:
    df = make_sample_df()
    rfm = build_rfm_table(df)
    customer_metrics = estimate_clv(rfm, df)
    segmentation, _, _, _, _, cluster_metrics = build_customer_segments(customer_metrics)
    segment_summary = segmentation.groupby("Segment", as_index=False).agg(Customers=("CustomerID", "nunique"))

    paths = save_phase_two_outputs(segmentation, rfm, customer_metrics, cluster_metrics, segment_summary, tmp_path)

    assert set(paths) == {"rfm_table", "customer_segments", "customer_metrics", "segment_summary", "cluster_metrics"}
    assert "PredictedCLV" in pd.read_csv(paths["customer_metrics"]).columns
    assert "Silhouette" in pd.read_csv(paths["cluster_metrics"]).columns

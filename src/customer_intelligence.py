from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from constants import DEFAULT_PROFIT_MARGIN, DEFAULT_RANDOM_STATE
from io_utils import save_figure as persist_figure, write_dataframe, write_joblib, write_text
from logger import get_logger

logger = get_logger(__name__)


def build_rfm_table(df: pd.DataFrame) -> pd.DataFrame:
    logger.info('Building RFM table')
    if 'InvoiceDate' not in df.columns:
        raise KeyError('InvoiceDate is required for RFM analysis')
    if 'CustomerID' not in df.columns:
        raise KeyError('CustomerID is required for RFM analysis')

    snapshot_date = df['InvoiceDate'].max() + pd.Timedelta(days=1)
    rfm = (
        df.groupby('CustomerID')
        .agg(
            Recency=('InvoiceDate', lambda s: (snapshot_date - s.max()).days),
            Frequency=('InvoiceNo', 'nunique'),
            Monetary=('Revenue', 'sum'),
            Orders=('InvoiceNo', 'nunique'),
            Revenue=('Revenue', 'sum'),
            LastPurchase=('InvoiceDate', 'max'),
            FirstPurchase=('InvoiceDate', 'min'),
        )
        .reset_index()
    )

    rfm['Recency'] = pd.to_numeric(rfm['Recency'], errors='coerce').fillna(0)
    rfm['Frequency'] = pd.to_numeric(rfm['Frequency'], errors='coerce').fillna(0)
    rfm['Monetary'] = pd.to_numeric(rfm['Monetary'], errors='coerce').fillna(0)

    rfm['R_score'] = pd.qcut(rfm['Recency'].rank(method='first'), q=4, labels=['4', '3', '2', '1'])
    rfm['F_score'] = pd.qcut(rfm['Frequency'].rank(method='first'), q=4, labels=['1', '2', '3', '4'])
    rfm['M_score'] = pd.qcut(rfm['Monetary'].rank(method='first'), q=4, labels=['1', '2', '3', '4'])
    rfm['RFM_Score'] = rfm['R_score'].astype(str) + rfm['F_score'].astype(str) + rfm['M_score'].astype(str)
    rfm['CustomerRank'] = rfm['Monetary'].rank(method='dense', ascending=False).astype(int)
    rfm['CustomerTier'] = pd.qcut(rfm['CustomerRank'], q=4, labels=['Lower', 'Mid', 'High', 'Top'])
    return rfm.sort_values('CustomerRank').reset_index(drop=True)


def estimate_clv(rfm: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    logger.info('Estimating customer lifetime value')
    if 'CustomerID' not in rfm.columns:
        raise KeyError('CustomerID is required for CLV estimation')

    customer_metrics = rfm.copy()
    customer_metrics['HistoricalCLV'] = customer_metrics['Monetary'].fillna(0)
    customer_metrics['CustomerRevenue'] = customer_metrics['Monetary'].fillna(0)
    customer_metrics['CustomerProfit'] = (customer_metrics['Monetary'] * DEFAULT_PROFIT_MARGIN).round(2)
    customer_metrics['CustomerMargin'] = (customer_metrics['CustomerProfit'] / customer_metrics['Monetary'].replace(0, np.nan)).fillna(0)
    customer_metrics['LifetimeDays'] = ((customer_metrics['LastPurchase'] - customer_metrics['FirstPurchase']).dt.days + 1).fillna(1)
    customer_metrics['PurchaseIntervalDays'] = (customer_metrics['LifetimeDays'] / customer_metrics['Frequency'].replace(0, np.nan)).replace([np.inf, -np.inf], np.nan).fillna(0)
    customer_metrics['AverageCLV'] = customer_metrics['HistoricalCLV']
    customer_metrics['PredictedCLV'] = (customer_metrics['HistoricalCLV'] * 1.1).round(2)
    return customer_metrics


def prepare_clustering_features(rfm: pd.DataFrame) -> tuple[pd.DataFrame, StandardScaler]:
    logger.info('Preparing clustering features')
    feature_columns = ['Recency', 'Frequency', 'Monetary', 'CustomerProfit', 'CustomerMargin', 'PredictedCLV']
    features = rfm[feature_columns].copy()
    features = features.fillna(0)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)
    return pd.DataFrame(scaled, index=rfm.index, columns=feature_columns), scaler


def select_kmeans_model(features: pd.DataFrame) -> tuple[int, pd.DataFrame]:
    logger.info('Selecting KMeans cluster count')
    metrics = []
    max_k = min(7, len(features) - 1)
    if max_k < 2:
        return 2, pd.DataFrame([{'K': 2, 'Inertia': 0.0, 'Silhouette': 0.0, 'DaviesBouldin': 0.0, 'CalinskiHarabasz': 0.0}])

    for k in range(2, max_k + 1):
        model = KMeans(n_clusters=k, random_state=DEFAULT_RANDOM_STATE, n_init=20)
        labels = model.fit_predict(features)
        try:
            silhouette = silhouette_score(features, labels)
        except ValueError:
            silhouette = float('-inf')
        try:
            davies_bouldin = davies_bouldin_score(features, labels)
        except ValueError:
            davies_bouldin = float('inf')
        try:
            calinski_harabasz = calinski_harabasz_score(features, labels)
        except ValueError:
            calinski_harabasz = float('-inf')
        metrics.append(
            {
                'K': k,
                'Inertia': model.inertia_,
                'Silhouette': silhouette,
                'DaviesBouldin': davies_bouldin,
                'CalinskiHarabasz': calinski_harabasz,
            }
        )
    metrics_df = pd.DataFrame(metrics)
    best_k = int(metrics_df.loc[metrics_df['Silhouette'].idxmax(), 'K']) if not metrics_df.empty else 2
    return best_k, metrics_df


def assign_segment_labels(segmentation: pd.DataFrame) -> pd.Series:
    cluster_stats = (
        segmentation.groupby('Cluster')
        .agg(
            AvgRecency=('Recency', 'mean'),
            AvgFrequency=('Frequency', 'mean'),
            AvgMonetary=('Monetary', 'mean'),
        )
        .reset_index()
    )
    label_map: dict[int, str] = {}
    for _, row in cluster_stats.iterrows():
        if row['AvgFrequency'] >= 3 and row['AvgMonetary'] >= 1500 and row['AvgRecency'] <= 60:
            label_map[int(row['Cluster'])] = 'Champions'
        elif row['AvgFrequency'] >= 2 and row['AvgMonetary'] >= 800:
            label_map[int(row['Cluster'])] = 'Loyal Customers'
        elif row['AvgFrequency'] >= 2:
            label_map[int(row['Cluster'])] = 'Potential Loyalists'
        elif row['AvgRecency'] > 180:
            label_map[int(row['Cluster'])] = 'At Risk'
        else:
            label_map[int(row['Cluster'])] = 'Needs Attention'
    return segmentation['Cluster'].map(label_map).fillna('Needs Attention')


def build_customer_segments(rfm: pd.DataFrame) -> tuple[pd.DataFrame, Any, Any, Any, Any, pd.DataFrame]:
    logger.info('Building customer segments')
    features, scaler = prepare_clustering_features(rfm)
    k, metrics = select_kmeans_model(features)
    model = KMeans(n_clusters=k, random_state=DEFAULT_RANDOM_STATE, n_init=20)
    labels = model.fit_predict(features)
    pca = PCA(n_components=2, random_state=DEFAULT_RANDOM_STATE)
    pca_features = pca.fit_transform(features)
    if len(features) <= 3:
        tsne = TSNE(n_components=2, random_state=DEFAULT_RANDOM_STATE, perplexity=2)
        tsne_features = np.array([[0.0, 0.0] for _ in range(len(features))])
    else:
        tsne = TSNE(n_components=2, random_state=DEFAULT_RANDOM_STATE, perplexity=min(30, max(5, len(features) // 10)))
        tsne_features = tsne.fit_transform(features)
    segmentation = rfm.copy()
    segmentation['Cluster'] = labels
    segmentation['Segment'] = assign_segment_labels(segmentation)
    segmentation['PCA1'] = pca_features[:, 0]
    segmentation['PCA2'] = pca_features[:, 1]
    segmentation['TSNE1'] = tsne_features[:, 0]
    segmentation['TSNE2'] = tsne_features[:, 1]
    segmentation['ClusterSize'] = segmentation.groupby('Cluster')['CustomerID'].transform('count')
    return segmentation, model, scaler, pca, tsne, metrics


def build_segment_summary(segmentation: pd.DataFrame) -> pd.DataFrame:
    logger.info('Building segment summary')
    summary = (
        segmentation.groupby('Segment')
        .agg(
            Customers=('CustomerID', 'nunique'),
            Revenue=('Revenue', 'sum'),
            Orders=('Orders', 'sum'),
            Profit=('CustomerProfit', 'sum'),
            AverageCLV=('PredictedCLV', 'mean'),
            RepeatRate=('Orders', lambda s: (s.gt(1).sum() / len(s)).round(4)),
            RetentionRate=('Orders', lambda s: (s.gt(1).sum() / len(s)).round(4)),
        )
        .reset_index()
    )
    summary['AverageBasketValue'] = (summary['Revenue'] / summary['Orders'].replace(0, np.nan)).fillna(0)
    summary['ContributionPercent'] = (summary['Revenue'] / segmentation['Revenue'].sum() * 100).round(2)
    summary['ProfitMarginPercent'] = (summary['Profit'] / summary['Revenue'].replace(0, np.nan) * 100).fillna(0).round(2)
    return summary.sort_values('Revenue', ascending=False).reset_index(drop=True)


def save_phase_two_outputs(
    segmentation: pd.DataFrame,
    rfm: pd.DataFrame,
    customer_metrics: pd.DataFrame,
    cluster_metrics: pd.DataFrame,
    segment_summary: pd.DataFrame,
    output_dir: str | Path | None = None,
) -> dict[str, Path]:
    logger.info('Saving Phase 2 outputs')
    output_dir = Path(output_dir) if output_dir is not None else Path('processed')
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        'rfm_table': output_dir / 'rfm_table.csv',
        'customer_segments': output_dir / 'customer_segments.csv',
        'customer_metrics': output_dir / 'customer_metrics.csv',
        'segment_summary': output_dir / 'segment_summary.csv',
        'cluster_metrics': output_dir / 'cluster_metrics.csv',
    }
    write_dataframe(rfm, paths['rfm_table'])
    write_dataframe(segmentation, paths['customer_segments'])
    write_dataframe(customer_metrics, paths['customer_metrics'])
    write_dataframe(segment_summary, paths['segment_summary'])
    write_dataframe(cluster_metrics, paths['cluster_metrics'])
    return paths


def save_figure(fig: plt.Figure, filename: str, output_dir: str | Path) -> Path:
    output_dir = Path(output_dir)
    return persist_figure(fig, output_dir / filename)


def generate_customer_visualizations(segmentation: pd.DataFrame, metrics_df: pd.DataFrame, output_dir: str | Path) -> list[Path]:
    logger.info('Generating customer intelligence visuals')
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    sns.set_theme(style='whitegrid')

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(segmentation['Recency'], bins=20, kde=True, ax=ax, color='#4C78A8')
    ax.set_title('Customer Recency Distribution')
    paths.append(save_figure(fig, '01_recency_distribution.png', output_dir))

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(segmentation['Frequency'], bins=20, kde=True, ax=ax, color='#F58518')
    ax.set_title('Customer Frequency Distribution')
    paths.append(save_figure(fig, '02_frequency_distribution.png', output_dir))

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(segmentation['Monetary'], bins=20, kde=True, ax=ax, color='#54A24B')
    ax.set_title('Customer Monetary Distribution')
    paths.append(save_figure(fig, '03_monetary_distribution.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(data=segmentation, x='Recency', y='Frequency', hue='Segment', ax=ax, s=70)
    ax.set_title('Recency vs Frequency')
    paths.append(save_figure(fig, '04_recency_vs_frequency.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(data=segmentation, x='Frequency', y='Monetary', hue='Segment', ax=ax, s=70)
    ax.set_title('Frequency vs Monetary')
    paths.append(save_figure(fig, '05_frequency_vs_monetary.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(data=segmentation, x='Recency', y='Monetary', hue='Segment', ax=ax, s=70)
    ax.set_title('Recency vs Monetary')
    paths.append(save_figure(fig, '06_recency_vs_monetary.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.countplot(data=segmentation, x='CustomerTier', order=['Lower', 'Mid', 'High', 'Top'], ax=ax)
    ax.set_title('Customer Tier Distribution')
    paths.append(save_figure(fig, '07_customer_tier.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.countplot(data=segmentation, x='Segment', ax=ax)
    ax.set_title('Segment Count')
    ax.tick_params(axis='x', rotation=30)
    paths.append(save_figure(fig, '08_segment_count.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 5))
    segment_revenue = segmentation.groupby('Segment')['Revenue'].sum().sort_values(ascending=False)
    sns.barplot(x=segment_revenue.index, y=segment_revenue.values, ax=ax)
    ax.set_title('Revenue by Segment')
    ax.tick_params(axis='x', rotation=30)
    paths.append(save_figure(fig, '09_segment_revenue.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 5))
    segment_profit = segmentation.groupby('Segment')['CustomerProfit'].sum().sort_values(ascending=False)
    sns.barplot(x=segment_profit.index, y=segment_profit.values, ax=ax)
    ax.set_title('Profit by Segment')
    ax.tick_params(axis='x', rotation=30)
    paths.append(save_figure(fig, '10_segment_profit.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 5))
    segment_clv = segmentation.groupby('Segment')['PredictedCLV'].mean().sort_values(ascending=False)
    sns.barplot(x=segment_clv.index, y=segment_clv.values, ax=ax)
    ax.set_title('Average CLV by Segment')
    ax.tick_params(axis='x', rotation=30)
    paths.append(save_figure(fig, '11_segment_clv.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.countplot(data=segmentation, x='Cluster', palette='viridis', ax=ax)
    ax.set_title('Cluster Distribution')
    paths.append(save_figure(fig, '12_cluster_distribution.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=segmentation, x='Cluster', y='Monetary', palette='viridis', ax=ax)
    ax.set_title('Monetary Distribution by Cluster')
    paths.append(save_figure(fig, '13_cluster_monetary_boxplot.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=segmentation, x='Cluster', y='PredictedCLV', palette='mako', ax=ax)
    ax.set_title('CLV Distribution by Cluster')
    paths.append(save_figure(fig, '14_cluster_clv_boxplot.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(segmentation['PredictedCLV'], bins=20, kde=True, ax=ax, color='#B279A2')
    ax.set_title('Predicted CLV Distribution')
    paths.append(save_figure(fig, '15_predicted_clv_distribution.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(segmentation['LifetimeDays'], bins=20, kde=True, ax=ax, color='#72B7B2')
    ax.set_title('Customer Lifetime Days Distribution')
    paths.append(save_figure(fig, '16_lifetime_days_distribution.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(segmentation['PurchaseIntervalDays'], bins=20, kde=True, ax=ax, color='#E45756')
    ax.set_title('Purchase Interval Distribution')
    paths.append(save_figure(fig, '17_purchase_interval_distribution.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(data=segmentation, x='PCA1', y='PCA2', hue='Segment', style='Cluster', ax=ax, s=70)
    ax.set_title('PCA Projection of Customer Segments')
    paths.append(save_figure(fig, '18_pca_projection.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(data=segmentation, x='TSNE1', y='TSNE2', hue='Segment', style='Cluster', ax=ax, s=70)
    ax.set_title('t-SNE Projection of Customer Segments')
    paths.append(save_figure(fig, '19_tsne_projection.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.lineplot(x=metrics_df['K'], y=metrics_df['Silhouette'], marker='o', ax=ax)
    ax.set_title('Silhouette Score by Cluster Count')
    ax.set_xlabel('K')
    ax.set_ylabel('Silhouette')
    paths.append(save_figure(fig, '20_silhouette_scores.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.lineplot(x=metrics_df['K'], y=metrics_df['Inertia'], marker='o', ax=ax)
    ax.set_title('K-Means Inertia by Cluster Count')
    ax.set_xlabel('K')
    ax.set_ylabel('Inertia')
    paths.append(save_figure(fig, '21_inertia_curve.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.lineplot(x=metrics_df['K'], y=metrics_df['DaviesBouldin'], marker='o', ax=ax)
    ax.set_title('Davies-Bouldin Score by Cluster Count')
    ax.set_xlabel('K')
    ax.set_ylabel('Davies-Bouldin')
    paths.append(save_figure(fig, '22_davies_bouldin.png', output_dir))

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.lineplot(x=metrics_df['K'], y=metrics_df['CalinskiHarabasz'], marker='o', ax=ax)
    ax.set_title('Calinski-Harabasz Score by Cluster Count')
    ax.set_xlabel('K')
    ax.set_ylabel('Calinski-Harabasz')
    paths.append(save_figure(fig, '23_calinski_harabasz.png', output_dir))

    fig, ax = plt.subplots(figsize=(10, 6))
    top_customers = segmentation.sort_values('Revenue', ascending=False).head(10)
    sns.barplot(data=top_customers, x='CustomerID', y='Revenue', ax=ax)
    ax.set_title('Top Customers by Revenue')
    ax.tick_params(axis='x', rotation=45)
    paths.append(save_figure(fig, '24_top_customers_revenue.png', output_dir))

    fig, ax = plt.subplots(figsize=(10, 6))
    heatmap_data = segmentation.pivot_table(index='Segment', columns='Cluster', values='Revenue', aggfunc='sum').fillna(0)
    sns.heatmap(heatmap_data, annot=True, fmt='.0f', cmap='viridis', ax=ax)
    ax.set_title('Segment x Cluster Revenue Heatmap')
    paths.append(save_figure(fig, '25_segment_cluster_heatmap.png', output_dir))
    return paths


def write_phase_two_reports(segmentation: pd.DataFrame, segment_summary: pd.DataFrame, metrics_df: pd.DataFrame, output_dir: str | Path, figures_dir: str | Path) -> dict[str, Path]:
    logger.info('Writing Phase 2 reports')
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = Path(figures_dir)

    segmentation_summary = segmentation.groupby('Segment').agg(Customers=('CustomerID', 'nunique'), Revenue=('Revenue', 'sum'), Profit=('CustomerProfit', 'sum')).reset_index()
    top_segment = segmentation_summary.sort_values('Revenue', ascending=False).iloc[0]['Segment'] if not segmentation_summary.empty else 'N/A'
    recommended_action = 'Prioritize high-value customers with retention offers and bundle promotions.'
    if top_segment != 'N/A':
        recommended_action = f'Prioritize {top_segment} customers with retention offers and bundle promotions.'

    report_paths = {
        'customer_segmentation_report': output_dir / 'customer_segmentation_report.md',
        'rfm_summary': output_dir / 'rfm_summary.md',
        'business_recommendations': output_dir / 'business_recommendations.md',
    }

    write_text(
        f"""# Customer Segmentation Report

## Overview
RetailPulse Phase 2 customer intelligence identified {len(segmentation)} customers and grouped them into {segmentation['Cluster'].nunique()} clusters.

## Segment Summary
- Top segment by revenue: {top_segment}
- Total revenue captured: {segmentation['Revenue'].sum():,.2f}
- Average CLV: {segmentation['PredictedCLV'].mean():,.2f}
- Cluster evaluation metrics: silhouette {metrics_df['Silhouette'].max():.3f}, davies-bouldin {metrics_df['DaviesBouldin'].min():.3f}

## Visual Assets
The report is supported by 25 professional figures saved in {figures_dir}.
""",
        report_paths['customer_segmentation_report'],
    )

    write_text(
        """# RFM Summary

- Recency captures how recently customers purchased.
- Frequency measures how often they transact.
- Monetary measures their revenue contribution.
- RFM scores help prioritize retention and reactivation actions.
""",
        report_paths['rfm_summary'],
    )

    write_text(
        f"""# Business Recommendations

{recommended_action}

- Use personalized lifecycle campaigns for high-value segments.
- Re-engage dormant customers with win-back offers.
- Expand cross-sell opportunities for loyal cohorts.
""",
        report_paths['business_recommendations'],
    )
    return report_paths


def save_phase_two_models(model: Any, scaler: Any, pca: Any, tsne: Any, output_dir: str | Path) -> dict[str, Path]:
    logger.info('Saving Phase 2 models')
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        'kmeans': output_dir / 'kmeans.pkl',
        'scaler': output_dir / 'scaler.pkl',
        'pca': output_dir / 'pca.pkl',
        'tsne': output_dir / 'tsne.pkl',
    }
    write_joblib(model, paths['kmeans'])
    write_joblib(scaler, paths['scaler'])
    write_joblib(pca, paths['pca'])
    write_joblib(tsne, paths['tsne'])
    return paths


def run_phase_two(input_path: str | Path | None = None, output_dir: str | Path | None = None, reports_dir: str | Path | None = None, figures_dir: str | Path | None = None, models_dir: str | Path | None = None) -> dict[str, Any]:
    logger.info('Running Phase 2 customer intelligence workflow')
    base_dir = Path(input_path) if input_path is not None else Path('data/processed/final_processed_dataset.csv')
    if not base_dir.exists():
        base_dir = Path(__file__).resolve().parents[1] / 'data' / 'processed' / 'final_processed_dataset.csv'
    if not base_dir.exists():
        raise FileNotFoundError('Processed dataset not found; run Phase 1 first.')

    df = pd.read_csv(base_dir, parse_dates=['InvoiceDate'])
    rfm = build_rfm_table(df)
    customer_metrics = estimate_clv(rfm, df)
    segmentation, model, scaler, pca, tsne, metrics_df = build_customer_segments(customer_metrics)
    segment_summary = build_segment_summary(segmentation)

    output_dir = Path(output_dir) if output_dir is not None else Path('processed')
    reports_dir = Path(reports_dir) if reports_dir is not None else Path('reports')
    figures_dir = Path(figures_dir) if figures_dir is not None else reports_dir / 'figures'
    models_dir = Path(models_dir) if models_dir is not None else Path('models')

    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    csv_paths = save_phase_two_outputs(segmentation, rfm, customer_metrics, metrics_df, segment_summary, output_dir)
    visuals = generate_customer_visualizations(segmentation, metrics_df, figures_dir)
    report_paths = write_phase_two_reports(segmentation, segment_summary, metrics_df, reports_dir, figures_dir)
    model_paths = save_phase_two_models(model, scaler, pca, tsne, models_dir)

    try:
        from mlflow_utils import SafeMLflowRun, log_parameter, log_metric, log_artifact
        with SafeMLflowRun("RetailPulse Customer Intelligence", "customer_segmentation_run"):
            log_parameter("model_name", "KMeans Clustering")
            log_parameter("n_clusters", getattr(model, "n_clusters", 4))
            log_parameter("random_state", getattr(model, "random_state", 42))
            
            if segment_summary is not None and not segment_summary.empty:
                for _, row in segment_summary.iterrows():
                    seg_name = str(row["Segment"]).replace(" ", "_")
                    log_metric(f"segment_{seg_name}_customers", row["Customers"])
                    log_metric(f"segment_{seg_name}_revenue", row["Revenue"])
                    log_metric(f"segment_{seg_name}_profit", row["Profit"])
                    
            for path in csv_paths.values():
                log_artifact(path, "csv_outputs")
            for path in visuals:
                log_artifact(path, "plots")
            for path in report_paths.values():
                log_artifact(path, "reports")
            for path in model_paths.values():
                log_artifact(path, "model_files")
    except Exception as e:
        logger.warning(f"Failed to log Phase 2 run to MLflow: {e}")

    return {
        'dataframe': segmentation,
        'segment_summary': segment_summary,
        'csv_paths': csv_paths,
        'visual_paths': visuals,
        'report_paths': report_paths,
        'model_paths': model_paths,
    }

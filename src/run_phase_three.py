from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))
from forecasting import run_phase_three

if __name__ == '__main__':
    result = run_phase_three('data/processed/final_processed_dataset.csv', 'processed', 'reports', 'reports/figures', 'models')
    print('forecast_rows', len(result['results']))
    print('future_rows', len(result['future_predictions']))
    print('artifact_paths', result['artifact_paths'])
    print('report_paths', result['report_paths'])

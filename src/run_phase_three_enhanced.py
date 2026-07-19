from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))
from forecasting_enhanced import run_enhanced_forecasting

if __name__ == '__main__':
    result = run_enhanced_forecasting('data/processed/final_processed_dataset.csv', 'processed', 'reports', 'reports/figures', 'models')
    print('best_model', result['best_model'])
    print('leaderboard_rows', len(result['leaderboard']))
    print('future_rows', len(result['future_predictions']))
    print('artifact_paths', result['artifact_paths'])
    print('report_paths', result['report_paths'])

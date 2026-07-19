from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))
from pipeline import run_phase_one

if __name__ == '__main__':
    df, path = run_phase_one()
    print('rows', len(df))
    print('path', path)
    print('columns', df.columns.tolist())

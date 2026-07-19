# Contributing

RetailPulse is currently in architecture-freeze mode. Contributions should improve reliability, maintainability, documentation, or test coverage without changing business behavior.

## Local Setup

1. Create or activate a virtual environment.
2. Install the project dependencies with `pip install -r requirements.txt`.
3. Install optional forecasting dependencies only when you need the extended model zoo.

## Development Rules

- Preserve backward-compatible entry points in `src/run_phase_*.py`.
- Do not overwrite working datasets, reports, or models without keeping a backup.
- Prefer shared helpers in `src/` over copy-pasting logic into notebooks or services.
- Add regression tests for changes that affect outputs or file-writing behavior.

## Validation

- Run `python -m pytest`
- If you change notebooks, confirm that the corresponding pipeline module still runs cleanly
- If you change artifact writing, confirm backup files are created as expected


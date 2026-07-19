import sys
import os

# Enable local file store backend for MLflow 3.0+
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"

# Patch importlib.abc.Traversable for Python 3.14 compatibility
import importlib.abc
try:
    import importlib.resources.abc
    importlib.abc.Traversable = importlib.resources.abc.Traversable
except Exception:
    pass

from mlflow.cli import cli

if __name__ == '__main__':
    # Default to launching the UI on localhost:5000 if no args are specified
    if len(sys.argv) == 1:
        sys.argv.extend(["ui", "--host", "127.0.0.1", "--port", "5000"])
    cli()

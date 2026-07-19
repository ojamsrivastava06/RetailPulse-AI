import os
import sys

# Enable local file store backend for MLflow 3.0+
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"

# Patch importlib.abc.Traversable for Python 3.14 compatibility
try:
    import importlib.abc
    import importlib.resources.abc
    importlib.abc.Traversable = importlib.resources.abc.Traversable
    sys.modules['importlib.abc'].Traversable = importlib.resources.abc.Traversable
except Exception:
    pass

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


def _csv_env(name: str, default: str) -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class APISettings:
    """Runtime settings for the artifact-backed RetailPulse API."""

    app_name: str = "RetailPulse Enterprise API"
    version: str = "1.0.0"
    environment: str = field(default_factory=lambda: os.getenv("RETAILPULSE_ENV", "local"))
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2])
    api_key_header_name: str = "X-API-Key"
    api_keys: tuple[str, ...] = field(
        default_factory=lambda: tuple(_csv_env("RETAILPULSE_API_KEYS", "retailpulse-dev-api-key"))
    )
    jwt_secret_key: str | None = field(default_factory=lambda: os.getenv("RETAILPULSE_JWT_SECRET"))
    jwt_algorithm: str = field(default_factory=lambda: os.getenv("RETAILPULSE_JWT_ALGORITHM", "HS256"))
    default_page_size: int = field(default_factory=lambda: int(os.getenv("RETAILPULSE_DEFAULT_PAGE_SIZE", "100")))
    max_page_size: int = field(default_factory=lambda: int(os.getenv("RETAILPULSE_MAX_PAGE_SIZE", "1000")))
    rate_limit_requests: int = field(default_factory=lambda: int(os.getenv("RETAILPULSE_RATE_LIMIT_REQUESTS", "120")))
    rate_limit_window_seconds: int = field(
        default_factory=lambda: int(os.getenv("RETAILPULSE_RATE_LIMIT_WINDOW_SECONDS", "60"))
    )
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            _csv_env(
                "RETAILPULSE_CORS_ORIGINS",
                "http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000,http://127.0.0.1:3000",
            )
        )
    )

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def processed_data_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def processed_output_dir(self) -> Path:
        return self.project_root / "processed"

    @property
    def reports_dir(self) -> Path:
        return self.project_root / "reports"

    @property
    def figures_dir(self) -> Path:
        return self.reports_dir / "figures"

    @property
    def models_dir(self) -> Path:
        return self.project_root / "models"


@lru_cache(maxsize=1)
def get_settings() -> APISettings:
    return APISettings()


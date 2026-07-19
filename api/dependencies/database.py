from __future__ import annotations

from dataclasses import dataclass

from api.core.config import APISettings, get_settings


@dataclass(frozen=True)
class ArtifactDataSource:
    """Read-only data source descriptor for the generated RetailPulse artifacts."""

    settings: APISettings

    @property
    def status(self) -> dict[str, object]:
        return {
            "processed": self.settings.processed_output_dir.exists(),
            "data_processed": self.settings.processed_data_dir.exists(),
            "reports": self.settings.reports_dir.exists(),
            "models": self.settings.models_dir.exists(),
        }


def get_data_source() -> ArtifactDataSource:
    return ArtifactDataSource(settings=get_settings())


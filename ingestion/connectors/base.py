"""Base connector interface and shared utilities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterator, Optional

from ingestion.models import IngestResult
from ingestion.service import IngestionService


@dataclass
class ConnectorConfig:
    connector_id: str
    version: str
    source_system: str
    enabled: bool = True


class BaseConnector(ABC):
    """Pull or receive events from one source system and pass to IngestionService."""

    def __init__(self, config: ConnectorConfig, ingestion: IngestionService) -> None:
        self.config = config
        self.ingestion = ingestion

    @abstractmethod
    def fetch_events(
        self,
        user_id: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> Iterator[dict[str, Any]]:
        """Yield raw event dicts matching envelope + payload schema."""
        ...

    def run_sync(
        self,
        user_id: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> list[IngestResult]:
        results: list[IngestResult] = []
        for event in self.fetch_events(user_id=user_id, since=since):
            event.setdefault("source_system", self.config.source_system)
            event.setdefault("connector_version", self.config.version)
            results.append(self.ingestion.ingest(event))
        return results

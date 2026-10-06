from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class TelemetryPayload:
    device_id: str
    timestamp: str
    temperature: float | None = None
    humidity: float | None = None
    pressure: float | None = None
    motion: bool | None = None
    battery: float | None = None
    status: str = "online"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}


class BaseDevice(ABC):
    """Contrato común para cualquier sensor/dispositivo simulado."""

    def __init__(self, device_id: str, name: str, location: str) -> None:
        self.device_id = device_id
        self.name = name
        self.location = location
        self.status = "online"

    @property
    def telemetry_topic(self) -> str:
        return f"iot/devices/{self.device_id}/telemetry"

    @property
    def status_topic(self) -> str:
        return f"iot/devices/{self.device_id}/status"

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    @abstractmethod
    def read(self, force_anomaly: bool = False) -> TelemetryPayload:
        """Genera una lectura de telemetría."""

    def status_payload(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "location": self.location,
            "status": self.status,
            "timestamp": self._now_iso(),
        }

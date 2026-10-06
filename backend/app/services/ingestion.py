from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.alert import AlertSeverity, AlertType
from app.models.device import DeviceStatus
from app.repositories.alert import AlertRepository
from app.repositories.device import DeviceRepository
from app.repositories.measurement import MeasurementRepository
from app.services.anomaly_detection import AnomalyDetectionService
from app.services.events import MqttEventPublisher

logger = logging.getLogger(__name__)


class IngestionService:
    """Valida telemetría MQTT, persiste mediciones, ML + umbral fallback."""

    def __init__(self, db: Session, events: MqttEventPublisher | None = None) -> None:
        self.db = db
        self.devices = DeviceRepository(db)
        self.measurements = MeasurementRepository(db)
        self.alerts = AlertRepository(db)
        self.settings = get_settings()
        self.events = events
        self.anomaly_ml = AnomalyDetectionService(db, events=events)

    def handle_status(self, payload: dict[str, Any]) -> None:
        device_code = payload.get("device_id")
        if not device_code:
            logger.warning("Status sin device_id: %s", payload)
            return

        status_raw = str(payload.get("status", "online")).lower()
        status = DeviceStatus.online if status_raw == "online" else DeviceStatus.offline
        device = self.devices.upsert_from_telemetry(
            device_code=device_code,
            name=payload.get("name"),
            location=payload.get("location"),
            status=status,
        )
        logger.info("Status actualizado: %s → %s", device_code, status.value)
        self._emit(
            "device_status",
            {
                "id": device.id,
                "device_code": device.device_code,
                "name": device.name,
                "location": device.location,
                "status": device.status.value,
                "last_seen_at": device.last_seen_at,
            },
        )

    def handle_telemetry(self, payload: dict[str, Any]) -> None:
        device_code = payload.get("device_id")
        if not device_code:
            logger.warning("Telemetría sin device_id: %s", payload)
            return

        device = self.devices.upsert_from_telemetry(
            device_code=device_code,
            status=DeviceStatus.online,
        )

        timestamp = self._parse_timestamp(payload.get("timestamp"))
        measurement = self.measurements.create(
            device_id=device.id,
            timestamp=timestamp,
            temperature=_as_float(payload.get("temperature")),
            humidity=_as_float(payload.get("humidity")),
            pressure=_as_float(payload.get("pressure")),
            motion=_as_bool(payload.get("motion")),
            battery=_as_float(payload.get("battery")),
        )

        logger.info(
            "Medición guardada id=%s device=%s T=%s",
            measurement.id,
            device_code,
            measurement.temperature,
        )
        self._emit(
            "measurement",
            {
                "id": measurement.id,
                "device_id": device.id,
                "device_code": device_code,
                "timestamp": measurement.timestamp,
                "temperature": measurement.temperature,
                "humidity": measurement.humidity,
                "pressure": measurement.pressure,
                "motion": measurement.motion,
                "battery": measurement.battery,
            },
        )

        ml_ready = self.anomaly_ml.process_measurement(
            device_id=device.id,
            device_code=device_code,
            measurement=measurement,
        )
        # V1 umbral solo si ML aún no está listo para este dispositivo
        if not ml_ready:
            self._check_temperature_threshold(device.id, device_code, measurement.temperature)

    def _check_temperature_threshold(
        self,
        device_id: int,
        device_code: str,
        temperature: float | None,
    ) -> None:
        if temperature is None:
            return
        threshold = self.settings.temp_alert_threshold
        if temperature < threshold:
            return
        if self.alerts.has_open_of_type(device_id, AlertType.temperature_threshold):
            return

        severity = AlertSeverity.critical if temperature >= threshold + 8 else AlertSeverity.high
        message = (
            f"Temperatura anómala en {device_code}: {temperature:.1f}°C "
            f"(umbral {threshold:.1f}°C)"
        )
        alert = self.alerts.create(
            device_id=device_id,
            alert_type=AlertType.temperature_threshold,
            severity=severity,
            message=message,
        )
        logger.warning("⚠ Alerta #%s creada: %s", alert.id, message)
        self._emit(
            "alert",
            {
                "id": alert.id,
                "device_id": device_id,
                "device_code": device_code,
                "type": alert.type.value,
                "severity": alert.severity.value,
                "message": alert.message,
                "created_at": alert.created_at,
                "resolved_at": alert.resolved_at,
            },
        )

    def _emit(self, event_type: str, data: dict[str, Any]) -> None:
        if self.events is None:
            return
        self.events.publish(event_type, data)

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, str) and value:
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        return datetime.now(timezone.utc)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return bool(value)

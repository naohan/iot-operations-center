from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.alert import AlertSeverity, AlertType
from app.models.measurement import Measurement
from app.repositories.alert import AlertRepository
from app.repositories.anomaly import AnomalyRepository
from app.repositories.measurement import MeasurementRepository
from app.services.events import MqttEventPublisher
from ml.detector import detector
from ml.features import measurement_to_features, measurements_to_matrix

logger = logging.getLogger(__name__)


class AnomalyDetectionService:
    """Entrena Isolation Forest por dispositivo y puntúa nuevas mediciones."""

    def __init__(self, db: Session, events: MqttEventPublisher | None = None) -> None:
        self.db = db
        self.events = events
        self.settings = get_settings()
        self.measurements = MeasurementRepository(db)
        self.anomalies = AnomalyRepository(db)
        self.alerts = AlertRepository(db)

    def process_measurement(
        self,
        device_id: int,
        device_code: str,
        measurement: Measurement,
    ) -> bool:
        """
        Retorna True si el modelo ML está listo (aunque no haya anomalía).
        Así ingestion puede decidir si aplicar umbral V1 como fallback.
        """
        if not self.settings.ml_enabled:
            return False

        features = measurement_to_features(measurement)
        if features is None:
            return detector.is_ready(device_id)

        history = self.measurements.list_recent(
            limit=self.settings.ml_train_window,
            device_id=device_id,
        )
        # Excluir la medición actual del entrenamiento (está al inicio por orden desc)
        train_rows = [m for m in history if m.id != measurement.id]
        matrix = measurements_to_matrix(train_rows)

        detector.contamination = self.settings.ml_contamination
        detector.min_samples = self.settings.ml_min_samples
        did_train = detector.maybe_train(device_id, matrix)
        if did_train:
            logger.info(
                "ML modelo entrenado device_id=%s samples=%s",
                device_id,
                matrix.shape[0],
            )

        result = detector.evaluate(device_id, features)
        if not result.model_ready:
            return False

        if not result.is_anomaly:
            return True

        if self.anomalies.exists_for_measurement(measurement.id):
            return True

        anomaly = self.anomalies.create(
            device_id=device_id,
            measurement_id=measurement.id,
            score=result.score,
        )
        logger.warning(
            "⚠ ML ANOMALÍA device=%s score=%.3f reason=%s T=%s",
            device_code,
            result.score,
            result.reason,
            measurement.temperature,
        )

        self._emit(
            "anomaly",
            {
                "id": anomaly.id,
                "device_id": device_id,
                "device_code": device_code,
                "measurement_id": measurement.id,
                "score": anomaly.score,
                "reason": result.reason,
                "temperature": measurement.temperature,
                "detected_at": anomaly.detected_at,
            },
        )

        if not self.alerts.has_open_of_type(device_id, AlertType.anomaly):
            severity = (
                AlertSeverity.critical if result.score >= 0.85 else AlertSeverity.high
            )
            message = (
                f"Anomalía ML en {device_code}: score={result.score:.2f} "
                f"via {result.reason} (T={measurement.temperature}°C)"
            )
            alert = self.alerts.create(
                device_id=device_id,
                alert_type=AlertType.anomaly,
                severity=severity,
                message=message,
            )
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
                    "anomaly_score": result.score,
                },
            )

        return True

    def _emit(self, event_type: str, data: dict) -> None:
        if self.events is None:
            return
        self.events.publish(event_type, data)

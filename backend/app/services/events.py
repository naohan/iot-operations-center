from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Protocol

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class SupportsPublish(Protocol):
    def publish(self, topic: str, payload: str, qos: int = 1) -> None: ...


class MqttEventPublisher:
    """Publica eventos de dominio para el puente WebSocket (iot/events/*)."""

    def __init__(self, client: mqtt.Client) -> None:
        self._client = client

    def publish(self, event_type: str, data: dict[str, Any]) -> None:
        topic = f"iot/events/{event_type}"
        body = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        result = self._client.publish(topic, json.dumps(body, default=str), qos=1)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.error("No se pudo publicar evento %s (rc=%s)", topic, result.rc)
        else:
            logger.debug("Evento → %s", topic)

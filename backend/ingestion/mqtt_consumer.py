"""
MQTT Consumer — Etapa 2/3

Escucha telemetría/status, valida y persiste en PostgreSQL.
Publica eventos en iot/events/* para el puente WebSocket de FastAPI.
También genera alertas por umbral de temperatura (detección V1).

Uso:
    python -m ingestion.mqtt_consumer
"""

from __future__ import annotations

import json
import logging
import signal
import sys
import time
from typing import Any

import paho.mqtt.client as mqtt

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.services.events import MqttEventPublisher
from app.services.ingestion import IngestionService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ingestion")


class MqttConsumer:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._running = True
        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id="iot-ingestion",
            protocol=mqtt.MQTTv311,
        )
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect
        self._events = MqttEventPublisher(self._client)

    def start(self) -> None:
        init_db()
        host = self.settings.mqtt_host
        port = self.settings.mqtt_port
        logger.info("Conectando MQTT %s:%s ...", host, port)
        self._client.connect(host, port, keepalive=60)
        self._client.loop_start()

        signal.signal(signal.SIGINT, self._stop)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, self._stop)

        logger.info("Consumer activo — Ctrl+C para detener")
        try:
            while self._running:
                time.sleep(0.2)
        finally:
            self._client.loop_stop()
            self._client.disconnect()
            logger.info("Consumer detenido")

    def _stop(self, signum: int, frame: object) -> None:
        logger.info("Señal %s — deteniendo...", signum)
        self._running = False

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None = None,
    ) -> None:
        if reason_code.is_failure:
            logger.error("Fallo MQTT connect: %s", reason_code)
            return
        topics = [
            (self.settings.mqtt_telemetry_topic, 1),
            (self.settings.mqtt_status_topic, 1),
        ]
        client.subscribe(topics)
        logger.info("Suscrito a %s", [t for t, _ in topics])

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: mqtt.DisconnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None = None,
    ) -> None:
        logger.warning("Desconectado MQTT: %s", reason_code)

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        # Evitar bucles si algún día nos suscribimos a events
        if msg.topic.startswith("iot/events/"):
            return

        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            logger.error("Payload inválido en %s", msg.topic)
            return

        db = SessionLocal()
        try:
            service = IngestionService(db, events=self._events)
            if msg.topic.endswith("/status"):
                service.handle_status(payload)
            else:
                service.handle_telemetry(payload)
        except Exception:
            logger.exception("Error procesando %s", msg.topic)
            db.rollback()
        finally:
            db.close()


def main() -> int:
    MqttConsumer().start()
    return 0


if __name__ == "__main__":
    sys.exit(main())

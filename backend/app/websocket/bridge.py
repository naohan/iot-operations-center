from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import paho.mqtt.client as mqtt

from app.config import get_settings
from app.websocket.manager import ConnectionManager

logger = logging.getLogger(__name__)


class MqttWsBridge:
    """
    Escucha eventos internos MQTT (iot/events/#) publicados por ingestion
    y los reenvía a todos los clientes WebSocket.
    """

    def __init__(self, manager: ConnectionManager) -> None:
        self.manager = manager
        self.settings = get_settings()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"iot-api-ws-{os.getpid()}",
            protocol=mqtt.MQTTv311,
        )
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

    async def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        host = self.settings.mqtt_host
        port = self.settings.mqtt_port
        logger.info("WS bridge conectando MQTT %s:%s ...", host, port)
        await asyncio.to_thread(self._client.connect, host, port, 60)
        self._client.loop_start()

    async def stop(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
        logger.info("WS bridge detenido")

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None = None,
    ) -> None:
        if reason_code.is_failure:
            logger.error("WS bridge MQTT connect falló: %s", reason_code)
            return
        topic = self.settings.mqtt_events_topic
        client.subscribe(topic, qos=1)
        logger.info("WS bridge suscrito a %s", topic)

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: mqtt.DisconnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None = None,
    ) -> None:
        logger.warning("WS bridge desconectado: %s", reason_code)

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        if self._loop is None:
            return
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            logger.error("Evento inválido en %s", msg.topic)
            return

        if "type" not in payload:
            # Inferir tipo desde el topic: iot/events/measurement → measurement
            parts = msg.topic.split("/")
            payload = {
                "type": parts[-1] if parts else "event",
                "data": payload,
            }

        asyncio.run_coroutine_threadsafe(self.manager.broadcast(payload), self._loop)

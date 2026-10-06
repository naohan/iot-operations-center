from __future__ import annotations

import json
import logging
from typing import Any, Callable

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MqttPublisher:
    """Cliente MQTT para publicar telemetría y estado de dispositivos."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 1883,
        client_id: str = "iot-simulator",
        keepalive: int = 60,
    ) -> None:
        self.host = host
        self.port = port
        self._connected = False

        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
            protocol=mqtt.MQTTv311,
        )
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        logger.info("Conectando a MQTT %s:%s ...", self.host, self.port)
        self._client.connect(self.host, self.port, keepalive=60)
        self._client.loop_start()

    def disconnect(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
        self._connected = False
        logger.info("Desconectado de MQTT")

    def publish(self, topic: str, payload: dict[str, Any], qos: int = 1, retain: bool = False) -> None:
        body = json.dumps(payload, ensure_ascii=False)
        result = self._client.publish(topic, body, qos=qos, retain=retain)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.error("Error publicando en %s (rc=%s)", topic, result.rc)
        else:
            logger.debug("→ %s  %s", topic, body)

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None = None,
    ) -> None:
        if reason_code.is_failure:
            self._connected = False
            logger.error("Fallo al conectar MQTT: %s", reason_code)
        else:
            self._connected = True
            logger.info("Conectado a MQTT broker")

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: mqtt.DisconnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None = None,
    ) -> None:
        self._connected = False
        logger.warning("Desconectado de MQTT: %s", reason_code)


def create_subscriber(
    host: str,
    port: int,
    topic: str,
    on_message: Callable[[str, dict[str, Any]], None],
    client_id: str = "iot-subscriber",
) -> mqtt.Client:
    """
    Helper de depuración: suscribirse a un topic y recibir mensajes.
    Útil para verificar la Etapa 1 sin Angular todavía.
    """

    def _on_connect(
        client: mqtt.Client,
        userdata: Any,
        flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None = None,
    ) -> None:
        if not reason_code.is_failure:
            client.subscribe(topic, qos=1)
            logger.info("Suscrito a %s", topic)

    def _on_message(
        client: mqtt.Client,
        userdata: Any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except json.JSONDecodeError:
            logger.error("Payload inválido en %s", msg.topic)
            return
        on_message(msg.topic, payload)

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
        protocol=mqtt.MQTTv311,
    )
    client.on_connect = _on_connect
    client.on_message = _on_message
    client.connect(host, port, keepalive=60)
    return client

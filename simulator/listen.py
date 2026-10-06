"""
Suscriptor de prueba para la Etapa 1.

Uso (con Mosquitto y el simulador corriendo):
    python listen.py
    python listen.py --topic "iot/devices/SENSOR-001/telemetry"
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import time
from typing import Any

from dotenv import load_dotenv

from mqtt_client import create_subscriber

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("listen")


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Escucha telemetría MQTT (debug Etapa 1)")
    parser.add_argument("--host", default=os.getenv("MQTT_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MQTT_PORT", "1883")))
    parser.add_argument("--topic", default="iot/devices/+/telemetry")
    args = parser.parse_args()

    def on_message(topic: str, payload: dict[str, Any]) -> None:
        device = payload.get("device_id", "?")
        temp = payload.get("temperature")
        hum = payload.get("humidity")
        press = payload.get("pressure")
        logger.info(
            "← %s | %s | T=%s H=%s P=%s",
            topic,
            device,
            temp,
            hum,
            press,
        )

    client = create_subscriber(
        host=args.host,
        port=args.port,
        topic=args.topic,
        on_message=on_message,
        client_id="iot-listen",
    )
    client.loop_start()

    running = True

    def _stop(signum: int, frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _stop)
    logger.info("Escuchando %s en %s:%s  (Ctrl+C para salir)", args.topic, args.host, args.port)

    try:
        while running:
            time.sleep(0.2)
    finally:
        client.loop_stop()
        client.disconnect()

    return 0


if __name__ == "__main__":
    sys.exit(main())

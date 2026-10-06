from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from devices import MultiSensorDevice
from devices.multi_sensor import SensorBaseline
from mqtt_client import MqttPublisher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("simulator")

LOCATIONS = [
    ("Sala de servidores", SensorBaseline(temperature=22.5, humidity=45.0, pressure=1013.0)),
    ("Almacén A", SensorBaseline(temperature=18.0, humidity=60.0, pressure=1012.5)),
    ("Oficina Norte", SensorBaseline(temperature=24.0, humidity=50.0, pressure=1013.2)),
    ("Taller", SensorBaseline(temperature=26.0, humidity=40.0, pressure=1011.8)),
    ("Laboratorio", SensorBaseline(temperature=21.0, humidity=55.0, pressure=1013.5)),
    ("Pasillo B", SensorBaseline(temperature=23.0, humidity=52.0, pressure=1012.9)),
    ("Cuarto frío", SensorBaseline(temperature=8.0, humidity=70.0, pressure=1014.0)),
    ("Roof / Exterior", SensorBaseline(temperature=30.0, humidity=35.0, pressure=1009.5)),
]


def build_devices(count: int, anomaly_chance: float) -> list[MultiSensorDevice]:
    devices: list[MultiSensorDevice] = []
    for i in range(count):
        location, baseline = LOCATIONS[i % len(LOCATIONS)]
        device_id = f"SENSOR-{i + 1:03d}"
        devices.append(
            MultiSensorDevice(
                device_id=device_id,
                name=f"Sensor {i + 1:03d}",
                location=location,
                baseline=SensorBaseline(
                    temperature=baseline.temperature,
                    humidity=baseline.humidity,
                    pressure=baseline.pressure,
                    battery=100.0 - i * 1.5,
                ),
                anomaly_chance=anomaly_chance,
            )
        )
    return devices


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulador IoT — publica telemetría a Mosquitto (Etapa 1)",
    )
    parser.add_argument("--host", default=os.getenv("MQTT_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MQTT_PORT", "1883")))
    parser.add_argument(
        "--interval",
        type=float,
        default=float(os.getenv("PUBLISH_INTERVAL_SEC", "2")),
        help="Segundos entre lecturas",
    )
    parser.add_argument(
        "--devices",
        type=int,
        default=int(os.getenv("DEVICE_COUNT", "5")),
        help="Cantidad de dispositivos simulados",
    )
    parser.add_argument(
        "--anomaly-chance",
        type=float,
        default=float(os.getenv("ANOMALY_CHANCE", "0.02")),
        help="Probabilidad de anomalía por lectura (0–1)",
    )
    parser.add_argument(
        "--force-anomaly",
        metavar="DEVICE_ID",
        help="Fuerza una anomalía en un dispositivo (ej: SENSOR-001) y sale",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Publica una sola ronda de telemetría y termina",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=0,
        help="Publica N rondas rápidas (útil para entrenar el ML) y termina",
    )
    return parser.parse_args()


def main() -> int:
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)

    args = parse_args()
    devices = build_devices(args.devices, args.anomaly_chance)
    publisher = MqttPublisher(host=args.host, port=args.port, client_id="iot-simulator")

    running = True

    def _stop(signum: int, frame: object) -> None:
        nonlocal running
        logger.info("Señal %s recibida — deteniendo simulador...", signum)
        running = False

    signal.signal(signal.SIGINT, _stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _stop)

    try:
        publisher.connect()
        # Esperar conexión
        for _ in range(50):
            if publisher.is_connected:
                break
            time.sleep(0.1)
        if not publisher.is_connected:
            logger.error("No se pudo conectar al broker MQTT en %s:%s", args.host, args.port)
            logger.error("¿Está Mosquitto arriba?  →  docker compose up -d mosquitto")
            return 1

        # Publicar estado inicial (retained)
        for device in devices:
            publisher.publish(device.status_topic, device.status_payload(), retain=True)

        logger.info(
            "Simulador activo | %s dispositivos | intervalo=%ss | anomalía=%.1f%%",
            len(devices),
            args.interval,
            args.anomaly_chance * 100,
        )
        logger.info("Topics: iot/devices/+/telemetry")

        if args.force_anomaly:
            target = next((d for d in devices if d.device_id == args.force_anomaly), None)
            if target is None:
                logger.error("Dispositivo no encontrado: %s", args.force_anomaly)
                return 1
            payload = target.read(force_anomaly=True)
            publisher.publish(target.telemetry_topic, payload.to_dict())
            logger.warning(
                "⚠ ANOMALÍA FORZADA → %s  temp=%s°C",
                target.device_id,
                payload.temperature,
            )
            time.sleep(0.5)
            return 0

        rounds_done = 0
        while running:
            for device in devices:
                # En modo rounds evitamos anomalías aleatorias para entrenar limpio
                payload = device.read(force_anomaly=False) if args.rounds else device.read()
                if args.rounds:
                    # Forzar lectura normal: si salió pico, re-samplear sin anomalía
                    while (payload.temperature or 0) >= 40:
                        payload = device.read(force_anomaly=False)
                        device._anomaly_remaining = 0
                publisher.publish(device.telemetry_topic, payload.to_dict())
                temp = payload.temperature or 0
                flag = " ⚠ ANOMALÍA" if temp >= 40 else ""
                logger.info(
                    "%s | T=%5.1f°C H=%5.1f%% P=%7.1f | %s%s",
                    device.device_id,
                    temp,
                    payload.humidity or 0,
                    payload.pressure or 0,
                    device.location,
                    flag,
                )
            rounds_done += 1
            if args.once or (args.rounds and rounds_done >= args.rounds):
                break
            # Sleep en pasos cortos para reaccionar rápido a Ctrl+C
            sleep_for = 0.05 if args.rounds else args.interval
            elapsed = 0.0
            while running and elapsed < sleep_for:
                time.sleep(0.05)
                elapsed += 0.05

    finally:
        publisher.disconnect()
        logger.info("Simulador detenido")

    return 0


if __name__ == "__main__":
    sys.exit(main())

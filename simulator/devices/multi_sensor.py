from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .base import BaseDevice, TelemetryPayload


@dataclass
class SensorBaseline:
    temperature: float = 24.0
    humidity: float = 55.0
    pressure: float = 1013.0
    battery: float = 100.0


class MultiSensorDevice(BaseDevice):
    """
    Dispositivo multi-sensor (temp / humedad / presión / motion).

    En modo normal las lecturas oscilan suavemente alrededor de una baseline.
    Con force_anomaly=True (o por probabilidad) dispara un pico de temperatura
    para que más adelante el servicio ML pueda detectarlo.
    """

    def __init__(
        self,
        device_id: str,
        name: str,
        location: str,
        baseline: SensorBaseline | None = None,
        anomaly_chance: float = 0.02,
    ) -> None:
        super().__init__(device_id, name, location)
        self.baseline = baseline or SensorBaseline()
        self.anomaly_chance = anomaly_chance
        self._tick = random.uniform(0, math.tau)
        self._anomaly_remaining = 0

    def read(self, force_anomaly: bool = False) -> TelemetryPayload:
        self._tick += 0.15

        if force_anomaly or self._anomaly_remaining > 0 or random.random() < self.anomaly_chance:
            if self._anomaly_remaining == 0:
                self._anomaly_remaining = random.randint(3, 6)
            self._anomaly_remaining -= 1
            return self._anomalous_reading()

        return self._normal_reading()

    def _normal_reading(self) -> TelemetryPayload:
        b = self.baseline
        temperature = b.temperature + 1.5 * math.sin(self._tick) + random.uniform(-0.3, 0.3)
        humidity = b.humidity + 4.0 * math.sin(self._tick / 2) + random.uniform(-1.0, 1.0)
        pressure = b.pressure + 1.2 * math.sin(self._tick / 3) + random.uniform(-0.4, 0.4)
        motion = random.random() < 0.08
        battery = max(5.0, b.battery - random.uniform(0.001, 0.01))
        self.baseline.battery = battery

        return TelemetryPayload(
            device_id=self.device_id,
            timestamp=self._now_iso(),
            temperature=round(temperature, 2),
            humidity=round(max(0.0, min(100.0, humidity)), 2),
            pressure=round(pressure, 2),
            motion=motion,
            battery=round(battery, 2),
            status=self.status,
        )

    def _anomalous_reading(self) -> TelemetryPayload:
        payload = self._normal_reading()
        # Pico térmico claro: 40–52 °C (fácil de detectar en la demo)
        payload.temperature = round(random.uniform(40.0, 52.0), 2)
        return payload

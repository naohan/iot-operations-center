from __future__ import annotations

import numpy as np

from app.models.measurement import Measurement


FEATURE_NAMES = ("temperature", "humidity", "pressure")


def measurement_to_features(m: Measurement) -> list[float] | None:
    if m.temperature is None or m.humidity is None or m.pressure is None:
        return None
    return [float(m.temperature), float(m.humidity), float(m.pressure)]


def measurements_to_matrix(rows: list[Measurement]) -> np.ndarray:
    features: list[list[float]] = []
    for row in rows:
        f = measurement_to_features(row)
        if f is not None:
            features.append(f)
    if not features:
        return np.empty((0, 3), dtype=float)
    return np.asarray(features, dtype=float)

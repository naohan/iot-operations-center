from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import IsolationForest


@dataclass
class AnomalyResult:
    is_anomaly: bool
    score: float
    model_ready: bool
    reason: str = ""


class IsolationForestDetector:
    """
    Detector por dispositivo con Isolation Forest + z-score de temperatura.

    Features: [temperature, humidity, pressure]
    score ∈ [0, 1] — más alto = más anómalo.
    """

    def __init__(
        self,
        contamination: float = 0.02,
        min_samples: int = 25,
        retrain_every: int = 50,
        min_score: float = 0.72,
        z_threshold: float = 4.0,
    ) -> None:
        self.contamination = contamination
        self.min_samples = min_samples
        self.retrain_every = retrain_every
        self.min_score = min_score
        self.z_threshold = z_threshold
        self._models: dict[int, IsolationForest] = {}
        self._fitted_on: dict[int, int] = {}
        self._seen_since_fit: dict[int, int] = {}
        self._temp_stats: dict[int, tuple[float, float]] = {}

    def status(self) -> dict[str, object]:
        return {
            "algorithm": "IsolationForest+zscore",
            "min_samples": self.min_samples,
            "contamination": self.contamination,
            "devices_with_model": sorted(self._models.keys()),
            "model_count": len(self._models),
        }

    def is_ready(self, device_id: int) -> bool:
        return device_id in self._models

    def maybe_train(self, device_id: int, matrix: np.ndarray) -> bool:
        """Entrena o re-entrena. Retorna True solo si hubo fit nuevo."""
        n = int(matrix.shape[0])
        if n < self.min_samples:
            return False

        needs_initial = device_id not in self._models
        seen = self._seen_since_fit.get(device_id, 0)
        needs_retrain = seen >= self.retrain_every

        if not needs_initial and not needs_retrain:
            return False

        model = IsolationForest(
            n_estimators=100,
            contamination=self.contamination,
            random_state=42,
            n_jobs=1,
        )
        model.fit(matrix)
        self._models[device_id] = model
        self._fitted_on[device_id] = n
        self._seen_since_fit[device_id] = 0
        temp = matrix[:, 0]
        self._temp_stats[device_id] = (float(temp.mean()), float(max(temp.std(), 0.5)))
        return True

    def evaluate(self, device_id: int, features: list[float]) -> AnomalyResult:
        model = self._models.get(device_id)
        if model is None:
            return AnomalyResult(is_anomaly=False, score=0.0, model_ready=False)

        self._seen_since_fit[device_id] = self._seen_since_fit.get(device_id, 0) + 1
        x = np.asarray([features], dtype=float)
        pred = int(model.predict(x)[0])  # -1 anomaly, 1 normal
        decision = float(model.decision_function(x)[0])
        raw = -decision
        score = float(1.0 / (1.0 + np.exp(-raw * 6.0)))

        z_hit = False
        stats = self._temp_stats.get(device_id)
        if stats is not None:
            mean, std = stats
            z = abs(features[0] - mean) / std
            if z >= self.z_threshold:
                z_hit = True
                score = max(score, min(0.99, 0.55 + z / 12.0))

        is_anomaly = z_hit or (pred == -1 and score >= self.min_score)
        reason = "zscore" if z_hit else ("isolation_forest" if is_anomaly else "normal")
        return AnomalyResult(
            is_anomaly=is_anomaly,
            score=round(score, 4),
            model_ready=True,
            reason=reason,
        )


detector = IsolationForestDetector()

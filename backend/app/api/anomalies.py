from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models.anomaly import Anomaly
from app.models.user import User
from app.repositories.anomaly import AnomalyRepository
from app.schemas.anomaly import AnomalyRead, MlStatus
from ml.detector import detector

router = APIRouter(tags=["ml"])


@router.get("/anomalies", response_model=list[AnomalyRead])
def list_anomalies(
    limit: int = Query(50, ge=1, le=200),
    device_id: int | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AnomalyRead]:
    rows = AnomalyRepository(db).list_recent(limit=limit, device_id=device_id)
    return [
        AnomalyRead(
            id=a.id,
            device_id=a.device_id,
            measurement_id=a.measurement_id,
            score=a.score,
            detected_at=a.detected_at,
            device_code=a.device.device_code if a.device else None,
            temperature=a.measurement.temperature if a.measurement else None,
        )
        for a in rows
    ]


@router.get("/ml/status", response_model=MlStatus)
def ml_status(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MlStatus:
    settings = get_settings()
    st = detector.status()
    _ = db.scalar(select(func.count()).select_from(Anomaly))
    return MlStatus(
        enabled=settings.ml_enabled,
        algorithm=str(st["algorithm"]),
        min_samples=settings.ml_min_samples,
        contamination=settings.ml_contamination,
        model_count=int(st["model_count"]),
        devices_with_model=list(st["devices_with_model"]),  # type: ignore[arg-type]
    )

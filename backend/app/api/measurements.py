from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.repositories.measurement import MeasurementRepository
from app.schemas.measurement import MeasurementWithDevice

router = APIRouter(prefix="/measurements", tags=["measurements"])


@router.get("", response_model=list[MeasurementWithDevice])
def list_measurements(
    limit: int = Query(50, ge=1, le=500),
    device_id: int | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MeasurementWithDevice]:
    rows = MeasurementRepository(db).list_recent(limit=limit, device_id=device_id)
    return [
        MeasurementWithDevice(
            id=m.id,
            device_id=m.device_id,
            timestamp=m.timestamp,
            temperature=m.temperature,
            humidity=m.humidity,
            pressure=m.pressure,
            motion=m.motion,
            battery=m.battery,
            created_at=m.created_at,
            device_code=m.device.device_code if m.device else None,
        )
        for m in rows
    ]

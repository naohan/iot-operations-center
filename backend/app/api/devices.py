from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models.user import User, UserRole
from app.repositories.device import DeviceRepository
from app.schemas.device import DeviceCreate, DeviceRead, DeviceUpdate

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceRead])
def list_devices(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DeviceRead]:
    return DeviceRepository(db).list()


@router.get("/{device_id}", response_model=DeviceRead)
def get_device(
    device_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeviceRead:
    device = DeviceRepository(db).get(device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


@router.post("", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
def create_device(
    payload: DeviceCreate,
    _: User = Depends(require_roles(UserRole.admin)),
    db: Session = Depends(get_db),
) -> DeviceRead:
    repo = DeviceRepository(db)
    if repo.get_by_code(payload.device_code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device {payload.device_code} already exists",
        )
    return repo.create(payload)


@router.patch("/{device_id}", response_model=DeviceRead)
def update_device(
    device_id: int,
    payload: DeviceUpdate,
    _: User = Depends(require_roles(UserRole.admin, UserRole.operator)),
    db: Session = Depends(get_db),
) -> DeviceRead:
    repo = DeviceRepository(db)
    device = repo.get(device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return repo.update(device, payload)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    _: User = Depends(require_roles(UserRole.admin)),
    db: Session = Depends(get_db),
) -> None:
    repo = DeviceRepository(db)
    device = repo.get(device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    repo.delete(device)

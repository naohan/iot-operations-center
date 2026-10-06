from fastapi import APIRouter

from app.api import alerts, anomalies, auth, devices, measurements, system

api_router = APIRouter(prefix="/api")
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(devices.router)
api_router.include_router(measurements.router)
api_router.include_router(alerts.router)
api_router.include_router(anomalies.router)

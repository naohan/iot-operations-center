from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import get_settings
from app.database import init_db
from app.services.seed import seed_users
from app.websocket.bridge import MqttWsBridge
from app.websocket.manager import manager
from app.websocket.routes import router as ws_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    seed_users()
    bridge = MqttWsBridge(manager)
    await bridge.start()
    try:
        yield
    finally:
        await bridge.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="IoT Operations Center API",
        description="Etapa 6 — JWT/RBAC + MQTT + WebSocket + ML + Docker",
        version="0.6.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    app.include_router(ws_router)
    return app


app = create_app()

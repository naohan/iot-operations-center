from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg2://iot:iot_secret@localhost:5432/iot_ops"
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_telemetry_topic: str = "iot/devices/+/telemetry"
    mqtt_status_topic: str = "iot/devices/+/status"
    mqtt_events_topic: str = "iot/events/#"
    temp_alert_threshold: float = 40.0
    cors_origins: str = "http://localhost:4200,http://localhost:8000,http://localhost"

    ml_enabled: bool = True
    ml_min_samples: int = 25
    ml_contamination: float = 0.02
    ml_train_window: int = 200

    jwt_secret: str = "change-me-iot-ops-dev-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    seed_admin_email: str = "admin@example.com"
    seed_admin_password: str = "admin123"
    seed_operator_email: str = "operator@example.com"
    seed_operator_password: str = "operator123"
    seed_viewer_email: str = "viewer@example.com"
    seed_viewer_password: str = "viewer123"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

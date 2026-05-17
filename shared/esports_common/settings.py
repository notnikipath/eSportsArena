from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "esports-service"
    service_port: int = 8600
    environment: str = "dev"

    postgres_dsn: str = "postgresql+psycopg://esports:esports@postgres:5432/esports"
    influx_url: str = "http://influxdb:8086"
    redis_url: str = "redis://redis:6379/0"
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"
    mqtt_broker_url: str = "mqtt://mosquitto:1883"

    jwt_secret: str = "esports-dev-secret"
    encryption_key: str = "esports-dev-encryption-key"

    stream_delay_target_sec: float = 10.0
    stats_refresh_target_sec: float = 2.0
    viewer_capacity_target: int = 100000
    eta_mape_target_pct: float = 10.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

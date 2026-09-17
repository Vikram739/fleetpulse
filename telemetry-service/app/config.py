import os


class Settings:
    def __init__(self) -> None:
        self.redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_channel: str = os.getenv("TELEMETRY_CHANNEL", "telemetry")
        self.snapshot_key: str = os.getenv("SNAPSHOT_KEY", "fleet:snapshot")
        self.redis_max_retries: int = int(os.getenv("REDIS_MAX_RETRIES", "10"))
        self.redis_retry_base_delay: float = float(os.getenv("REDIS_RETRY_BASE_DELAY", "0.5"))
        self.redis_retry_max_delay: float = float(os.getenv("REDIS_RETRY_MAX_DELAY", "10"))
        self.redis_socket_timeout: float = float(os.getenv("REDIS_SOCKET_TIMEOUT", "2"))
        self.min_message_interval_seconds: float = float(
            os.getenv("MIN_MESSAGE_INTERVAL_SECONDS", "0.5")
        )
        self.host: str = os.getenv("TELEMETRY_SERVICE_HOST", "0.0.0.0")
        self.port: int = int(os.getenv("TELEMETRY_SERVICE_PORT", "8000"))

        self.cors_allowed_origins: list[str] = os.getenv(
            "CORS_ALLOWED_ORIGINS", "http://localhost:5173"
        ).split(",")


settings = Settings()

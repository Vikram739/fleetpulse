import os


class Settings:
    def __init__(self) -> None:
        self.database_url: str = os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ota_service"
        )
        self.db_max_retries: int = int(os.getenv("DB_MAX_RETRIES", "10"))
        self.db_retry_base_delay: float = float(os.getenv("DB_RETRY_BASE_DELAY", "0.5"))
        self.db_retry_max_delay: float = float(os.getenv("DB_RETRY_MAX_DELAY", "10"))
        self.db_query_timeout: float = float(os.getenv("DB_QUERY_TIMEOUT", "5"))
        self.default_rollout_stages: list[int] = [
            int(x) for x in os.getenv("DEFAULT_ROLLOUT_STAGES", "10,50,100").split(",")
        ]
        self.default_failure_threshold_percent: float = float(
            os.getenv("DEFAULT_FAILURE_THRESHOLD_PERCENT", "15")
        )
        self.simulated_success_probability: float = float(
            os.getenv("SIMULATED_SUCCESS_PROBABILITY", "0.85")
        )
        self.simulated_failure_probability: float = float(
            os.getenv("SIMULATED_FAILURE_PROBABILITY", "0.10")
        )
        self.simulated_unresponsive_probability: float = float(
            os.getenv("SIMULATED_UNRESPONSIVE_PROBABILITY", "0.05")
        )
        self.host: str = os.getenv("OTA_SERVICE_HOST", "0.0.0.0")
        self.port: int = int(os.getenv("OTA_SERVICE_PORT", "8001"))

        self.cors_allowed_origins: list[str] = os.getenv(
            "CORS_ALLOWED_ORIGINS", "http://localhost:5173"
        ).split(",")


settings = Settings()

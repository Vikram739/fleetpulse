import os


class Settings:
    def __init__(self) -> None:
        self.groq_api_key: str = os.getenv("GROQ_API_KEY", "")
        self.groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3")
        self.llm_timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "10"))

        self.redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/1")
        self.redis_max_retries: int = int(os.getenv("REDIS_MAX_RETRIES", "10"))
        self.redis_retry_base_delay: float = float(os.getenv("REDIS_RETRY_BASE_DELAY", "0.5"))
        self.redis_retry_max_delay: float = float(os.getenv("REDIS_RETRY_MAX_DELAY", "10"))
        self.redis_socket_timeout: float = float(os.getenv("REDIS_SOCKET_TIMEOUT", "2"))
        self.cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
        self.cache_key_prefix: str = os.getenv("CACHE_KEY_PREFIX", "diagnosis")

        self.host: str = os.getenv("DIAGNOSTICS_SERVICE_HOST", "0.0.0.0")
        self.port: int = int(os.getenv("DIAGNOSTICS_SERVICE_PORT", "8002"))

        self.cors_allowed_origins: list[str] = os.getenv(
            "CORS_ALLOWED_ORIGINS", "http://localhost:5173"
        ).split(",")

    def uses_groq(self) -> bool:
        return bool(self.groq_api_key)


settings = Settings()

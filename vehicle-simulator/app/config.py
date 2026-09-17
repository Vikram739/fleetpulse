import os


class Settings:
    def __init__(self) -> None:
        self.telemetry_ws_url: str = os.getenv(
            "TELEMETRY_WS_URL", "ws://localhost:8000/ws/telemetry"
        )
        self.vehicle_count: int = int(os.getenv("VEHICLE_COUNT", "25"))
        self.min_update_interval_seconds: float = float(
            os.getenv("MIN_UPDATE_INTERVAL_SECONDS", "1")
        )
        self.max_update_interval_seconds: float = float(
            os.getenv("MAX_UPDATE_INTERVAL_SECONDS", "3")
        )
        self.fault_code_probability: float = float(
            os.getenv("FAULT_CODE_PROBABILITY", "0.02")
        )
        self.firmware_versions: list[str] = os.getenv(
            "FIRMWARE_VERSIONS", "1.0.0,1.1.0,1.2.0"
        ).split(",")
        self.bounding_box_min_lat: float = float(os.getenv("BOUNDING_BOX_MIN_LAT", "37.70"))
        self.bounding_box_max_lat: float = float(os.getenv("BOUNDING_BOX_MAX_LAT", "37.83"))
        self.bounding_box_min_lon: float = float(os.getenv("BOUNDING_BOX_MIN_LON", "-122.52"))
        self.bounding_box_max_lon: float = float(os.getenv("BOUNDING_BOX_MAX_LON", "-122.36"))
        self.reconnect_base_delay_seconds: float = float(
            os.getenv("RECONNECT_BASE_DELAY_SECONDS", "1")
        )
        self.reconnect_max_delay_seconds: float = float(
            os.getenv("RECONNECT_MAX_DELAY_SECONDS", "30")
        )


settings = Settings()

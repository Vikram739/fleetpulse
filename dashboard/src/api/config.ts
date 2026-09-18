export const TELEMETRY_WS_URL: string =
  import.meta.env.VITE_TELEMETRY_WS_URL ?? "ws://localhost:8000/ws/dashboard";

export const TELEMETRY_HTTP_URL: string =
  import.meta.env.VITE_TELEMETRY_HTTP_URL ?? "http://localhost:8000";

export const OTA_API_URL: string = import.meta.env.VITE_OTA_API_URL ?? "http://localhost:8001";

export const DIAGNOSTICS_API_URL: string =
  import.meta.env.VITE_DIAGNOSTICS_API_URL ?? "http://localhost:8002";

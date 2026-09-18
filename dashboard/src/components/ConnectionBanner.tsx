import type { ConnectionStatus } from "../types";

interface ConnectionBannerProps {
  status: ConnectionStatus;
}

export function ConnectionBanner({ status }: ConnectionBannerProps) {
  if (status === "connected") {
    return null;
  }

  const message =
    status === "reconnecting"
      ? "Connection to telemetry service lost, reconnecting..."
      : "Connecting to telemetry service...";

  return <div className="connection-banner">{message}</div>;
}

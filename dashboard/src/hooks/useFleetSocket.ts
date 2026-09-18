import { useEffect, useState } from "react";
import { TELEMETRY_WS_URL } from "../api/config";
import type { ConnectionStatus, FleetSocketMessage, Vehicle } from "../types";

const CHANNEL_NAME = "fleetpulse-telemetry";
const LOCK_NAME = "fleetpulse-ws-leader";
const BASE_RECONNECT_DELAY_MS = 1000;
const MAX_RECONNECT_DELAY_MS = 30000;

type BroadcastPayload =
  | { kind: "snapshot"; vehicles: Vehicle[] }
  | { kind: "vehicle"; vehicle: Vehicle }
  | { kind: "status"; status: ConnectionStatus };

function safePostMessage(channel: BroadcastChannel, payload: BroadcastPayload): void {
  try {
    channel.postMessage(payload);
  } catch {
    // The channel may already be closed if the owning tab/effect has torn
    // down (e.g. React StrictMode's double-invoke in development). Dropping
    // the message here is safe, a fresh effect run will re-establish state.
  }
}

interface LeaderConnection {
  close: () => void;
}

function connectAsLeader(channel: BroadcastChannel, isCancelled: () => boolean): LeaderConnection {
  let delay = BASE_RECONNECT_DELAY_MS;
  let currentSocket: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  const connect = (): void => {
    if (isCancelled()) {
      return;
    }
    safePostMessage(channel, { kind: "status", status: "connecting" });
    const socket = new WebSocket(TELEMETRY_WS_URL);
    currentSocket = socket;

    socket.onopen = () => {
      if (isCancelled()) return;
      delay = BASE_RECONNECT_DELAY_MS;
      safePostMessage(channel, { kind: "status", status: "connected" });
    };

    socket.onmessage = (event: MessageEvent<string>) => {
      if (isCancelled()) return;
      try {
        const message = JSON.parse(event.data) as FleetSocketMessage;
        if (message.type === "snapshot") {
          safePostMessage(channel, { kind: "snapshot", vehicles: message.vehicles });
        } else if (message.type === "telemetry") {
          safePostMessage(channel, { kind: "vehicle", vehicle: message.data });
        }
      } catch {
        // Ignore malformed messages from the server rather than crashing the tab.
      }
    };

    socket.onclose = () => {
      if (isCancelled()) {
        return;
      }
      safePostMessage(channel, { kind: "status", status: "reconnecting" });
      reconnectTimer = setTimeout(connect, delay);
      delay = Math.min(delay * 2, MAX_RECONNECT_DELAY_MS);
    };

    socket.onerror = () => {
      socket.close();
    };
  };

  connect();

  return {
    close: () => {
      if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer);
      }
      currentSocket?.close();
    },
  };
}

export interface FleetSocketState {
  vehicles: Map<string, Vehicle>;
  status: ConnectionStatus;
}

export function useFleetSocket(): FleetSocketState {
  const [vehicles, setVehicles] = useState<Map<string, Vehicle>>(new Map());
  const [status, setStatus] = useState<ConnectionStatus>("connecting");

  useEffect(() => {
    let cancelled = false;
    const isCancelled = (): boolean => cancelled;

    // A BroadcastChannel never delivers a message back to the exact channel
    // object that sent it, even within the same tab. If the leader tab used
    // one channel for both sending and receiving, it would never see its
    // own updates, so sending and receiving use separate channel instances.
    const sendChannel = new BroadcastChannel(CHANNEL_NAME);
    const receiveChannel = new BroadcastChannel(CHANNEL_NAME);
    let leaderConnection: LeaderConnection | null = null;

    receiveChannel.onmessage = (event: MessageEvent<BroadcastPayload>) => {
      const payload = event.data;
      if (payload.kind === "snapshot") {
        setVehicles(new Map(payload.vehicles.map((v) => [v.vehicle_id, v])));
      } else if (payload.kind === "vehicle") {
        setVehicles((prev) => {
          const next = new Map(prev);
          next.set(payload.vehicle.vehicle_id, payload.vehicle);
          return next;
        });
      } else if (payload.kind === "status") {
        setStatus(payload.status);
      }
    };

    let releaseLock: (() => void) | null = null;

    if ("locks" in navigator) {
      void navigator.locks.request(LOCK_NAME, { mode: "exclusive" }, () => {
        return new Promise<void>((resolve) => {
          if (isCancelled()) {
            resolve();
            return;
          }
          releaseLock = resolve;
          leaderConnection = connectAsLeader(sendChannel, isCancelled);
        });
      });
    } else {
      // Web Locks API unavailable (older Safari): fall back to a direct
      // per-tab connection. Multiple tabs will each open their own socket
      // in this case, which is a known, acceptable degradation.
      leaderConnection = connectAsLeader(sendChannel, isCancelled);
    }

    return () => {
      cancelled = true;
      leaderConnection?.close();
      releaseLock?.();
      sendChannel.close();
      receiveChannel.close();
    };
  }, []);

  return { vehicles, status };
}

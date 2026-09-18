export interface Vehicle {
  vehicle_id: string;
  speed: number;
  battery_percent: number;
  latitude: number;
  longitude: number;
  fault_code: string | null;
  firmware_version: string;
  server_received_at: number;
}

export type ConnectionStatus = "connecting" | "connected" | "reconnecting";

export interface FleetSnapshotMessage {
  type: "snapshot";
  vehicles: Vehicle[];
}

export interface FleetTelemetryMessage {
  type: "telemetry";
  data: Vehicle;
}

export type FleetSocketMessage = FleetSnapshotMessage | FleetTelemetryMessage;

export type RolloutStatusName =
  | "pending"
  | "in_progress"
  | "halted"
  | "rolled_back"
  | "completed";

export type VehicleRolloutStatus =
  | "pending"
  | "in_progress"
  | "success"
  | "failed"
  | "unresponsive"
  | "rollback";

export interface BatchVehicleStatus {
  vehicle_id: string;
  stage_index: number;
  stage_percent: number;
  status: VehicleRolloutStatus;
}

export interface RolloutStatus {
  id: number;
  firmware_version: string;
  stages: number[];
  current_stage_index: number;
  current_stage_percent: number | null;
  status: RolloutStatusName;
  failure_threshold_percent: number;
  total_vehicles: number;
  assigned_count: number;
  success_count: number;
  failed_count: number;
  unresponsive_count: number;
  rollback_count: number;
  pending_count: number;
  percent_complete: number;
  vehicles: BatchVehicleStatus[];
}

export interface RolloutSummary {
  id: number;
  firmware_version: string;
  status: RolloutStatusName;
  current_stage_index: number;
  stages: number[];
}

export interface DiagnosisResult {
  fault_code: string;
  explanation: string;
  suggested_next_step: string;
  source: "cache" | "llm" | "fallback";
}

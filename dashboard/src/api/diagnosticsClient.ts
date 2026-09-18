import { DIAGNOSTICS_API_URL } from "./config";
import type { DiagnosisResult, Vehicle } from "../types";

export async function diagnoseFaultCode(
  faultCode: string,
  vehicle: Vehicle | undefined,
): Promise<DiagnosisResult> {
  const response = await fetch(`${DIAGNOSTICS_API_URL}/diagnose`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      fault_code: faultCode,
      telemetry_context: vehicle
        ? {
            speed: vehicle.speed,
            battery_percent: vehicle.battery_percent,
            firmware_version: vehicle.firmware_version,
          }
        : null,
    }),
  });
  if (!response.ok) {
    throw new Error(`Failed to diagnose fault code ${faultCode}: ${response.status}`);
  }
  return (await response.json()) as DiagnosisResult;
}

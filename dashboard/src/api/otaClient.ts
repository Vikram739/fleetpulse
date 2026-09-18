import { OTA_API_URL } from "./config";
import type { RolloutStatus, RolloutSummary } from "../types";

export async function fetchRollouts(): Promise<RolloutSummary[]> {
  const response = await fetch(`${OTA_API_URL}/rollouts`);
  if (!response.ok) {
    throw new Error(`Failed to fetch rollouts: ${response.status}`);
  }
  return (await response.json()) as RolloutSummary[];
}

export async function fetchRolloutStatus(rolloutId: number): Promise<RolloutStatus> {
  const response = await fetch(`${OTA_API_URL}/rollouts/${rolloutId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch rollout ${rolloutId}: ${response.status}`);
  }
  return (await response.json()) as RolloutStatus;
}

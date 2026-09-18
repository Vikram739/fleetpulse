import { useEffect, useState } from "react";
import { fetchRolloutStatus, fetchRollouts } from "../api/otaClient";
import type { RolloutStatus, RolloutSummary } from "../types";

const POLL_INTERVAL_MS = 5000;

export function RolloutPanel() {
  const [rollouts, setRollouts] = useState<RolloutSummary[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [status, setStatus] = useState<RolloutStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const poll = async (): Promise<void> => {
      try {
        const list = await fetchRollouts();
        if (cancelled) return;
        setRollouts(list);
        setError(null);
        setSelectedId((current) => current ?? (list.length > 0 ? list[0].id : null));
      } catch {
        if (!cancelled) {
          setError("Could not reach the OTA service.");
        }
      }
    };

    void poll();
    const interval = setInterval(() => void poll(), POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    if (selectedId === null) {
      setStatus(null);
      return;
    }
    let cancelled = false;

    const poll = async (): Promise<void> => {
      try {
        const detail = await fetchRolloutStatus(selectedId);
        if (!cancelled) {
          setStatus(detail);
          setError(null);
        }
      } catch {
        if (!cancelled) {
          setError("Could not reach the OTA service.");
        }
      }
    };

    void poll();
    const interval = setInterval(() => void poll(), POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [selectedId]);

  if (error && rollouts.length === 0) {
    return <p className="empty-message">{error}</p>;
  }

  if (rollouts.length === 0) {
    return <p className="empty-message">No rollouts have been created yet.</p>;
  }

  return (
    <div>
      <label className="rollout-select-label">
        Rollout:{" "}
        <select
          value={selectedId ?? undefined}
          onChange={(event) => setSelectedId(Number(event.target.value))}
        >
          {rollouts.map((rollout) => (
            <option key={rollout.id} value={rollout.id}>
              #{rollout.id} {rollout.firmware_version} ({rollout.status})
            </option>
          ))}
        </select>
      </label>

      {status && (
        <div className="rollout-detail">
          <div className={`rollout-status-badge status-${status.status}`}>{status.status}</div>
          <p>
            Stage: {status.current_stage_percent ?? "not started"}% (
            {status.current_stage_index + 1} of {status.stages.length})
          </p>
          <div className="progress-bar-track">
            <div
              className="progress-bar-fill"
              style={{ width: `${status.percent_complete}%` }}
            />
          </div>
          <p>{status.percent_complete}% complete</p>
          <ul className="rollout-counts">
            <li>Success: {status.success_count}</li>
            <li>Failed: {status.failed_count}</li>
            <li>Unresponsive: {status.unresponsive_count}</li>
            <li>Rollback: {status.rollback_count}</li>
            <li>Pending: {status.pending_count}</li>
          </ul>
        </div>
      )}
    </div>
  );
}

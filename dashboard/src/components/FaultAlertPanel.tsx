import { useEffect, useState } from "react";
import { diagnoseFaultCode } from "../api/diagnosticsClient";
import type { DiagnosisResult, Vehicle } from "../types";

interface FaultAlertPanelProps {
  vehicle: Vehicle;
  onClose: () => void;
}

export function FaultAlertPanel({ vehicle, onClose }: FaultAlertPanelProps) {
  const [result, setResult] = useState<DiagnosisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setResult(null);

    const faultCode = vehicle.fault_code;
    if (!faultCode) {
      setLoading(false);
      return;
    }

    diagnoseFaultCode(faultCode, vehicle)
      .then((data) => {
        if (!cancelled) {
          setResult(data);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError("Could not reach the diagnostics copilot.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [vehicle]);

  return (
    <div className="fault-panel-backdrop" onClick={onClose}>
      <div className="fault-panel" onClick={(event) => event.stopPropagation()}>
        <div className="fault-panel-header">
          <h3>
            {vehicle.vehicle_id}: {vehicle.fault_code}
          </h3>
          <button className="close-button" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        {loading && <p>Loading explanation...</p>}
        {error && <p className="error-message">{error}</p>}
        {result && (
          <div>
            <p>{result.explanation}</p>
            <p className="next-step">
              <strong>Next step:</strong> {result.suggested_next_step}
            </p>
            {result.source === "fallback" && (
              <p className="fallback-note">Diagnostics assistant is currently unavailable, showing a generic explanation.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

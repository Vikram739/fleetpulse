import { useMemo, useState } from "react";
import { ConnectionBanner } from "./components/ConnectionBanner";
import { FaultAlertPanel } from "./components/FaultAlertPanel";
import { FleetMap } from "./components/FleetMap";
import { RolloutPanel } from "./components/RolloutPanel";
import { VehicleList } from "./components/VehicleList";
import { useFleetSocket } from "./hooks/useFleetSocket";
import type { Vehicle } from "./types";

export function App() {
  const { vehicles, status } = useFleetSocket();
  const [selectedFaultVehicle, setSelectedFaultVehicle] = useState<Vehicle | null>(null);

  const vehicleList = useMemo(
    () => Array.from(vehicles.values()).sort((a, b) => a.vehicle_id.localeCompare(b.vehicle_id)),
    [vehicles],
  );

  return (
    <div className="app-shell">
      <ConnectionBanner status={status} />

      <header className="app-header">
        <h1>FleetPulse</h1>
        <span className="fleet-count">{vehicleList.length} vehicles</span>
      </header>

      <main className="app-grid">
        <section className="panel map-panel">
          <h2>Fleet Map</h2>
          {vehicleList.length > 0 ? (
            <FleetMap vehicles={vehicleList} />
          ) : (
            <p className="empty-message">No vehicles are reporting telemetry yet.</p>
          )}
        </section>

        <section className="panel list-panel">
          <h2>Vehicles</h2>
          <VehicleList vehicles={vehicleList} onSelectFault={setSelectedFaultVehicle} />
        </section>

        <section className="panel rollout-panel">
          <h2>Rollout Progress</h2>
          <RolloutPanel />
        </section>
      </main>

      {selectedFaultVehicle && (
        <FaultAlertPanel vehicle={selectedFaultVehicle} onClose={() => setSelectedFaultVehicle(null)} />
      )}
    </div>
  );
}
